import { Pool } from "pg";
import { PostgresDatabase } from "./postgres-database";
import { ProofPayError } from "./types";
import type { Configuration, SqlDatabase } from "./types";
import type { OwnerConfiguration } from "./auth";

export type RuntimeConfiguration = Configuration & OwnerConfiguration & {DATABASE_URL?: string; POSTGRES_URL?: string; JUDGE_DEMO_ONLY?: string};
export function getRuntimeConfiguration(): RuntimeConfiguration { return process.env; }
/** Judge requests select only their own deployment configuration. Owner keys,
 * payment credentials, AI funding and platform identity tokens are not read. */
export function getJudgeRuntimeConfiguration() {
  return {JUDGE_DEMO_ONLY: process.env.JUDGE_DEMO_ONLY, JUDGE_SESSION_SECRET: process.env.JUDGE_SESSION_SECRET, APP_ORIGIN: process.env.APP_ORIGIN, NODE_ENV: process.env.NODE_ENV, DATABASE_URL: process.env.DATABASE_URL, POSTGRES_URL: process.env.POSTGRES_URL};
}
export async function getRequestConfiguration(config: RuntimeConfiguration): Promise<RuntimeConfiguration> {
  const current = {...config, VERCEL_OIDC_TOKEN: undefined as string | undefined};
  // Use Vercel's request-context SDK only on Vercel. Never promote a public
  // header or a stale local environment value into a platform identity token.
  if (config.AI_FUNDING_MODE === "vercel-free-credit" && process.env.VERCEL === "1") {
    try {
      const {getVercelOidcToken} = await import("@vercel/oidc");
      current.VERCEL_OIDC_TOKEN = await getVercelOidcToken();
    } catch { /* AI remains unavailable; PayPal diagnostics remain usable. */ }
  }
  return current;
}
let cached: {url: string; database: PostgresDatabase} | undefined;
export function getDatabase(config: RuntimeConfiguration): SqlDatabase {
  let url: URL;
  try { url = new URL(config.DATABASE_URL ?? config.POSTGRES_URL ?? ""); } catch { throw new ProofPayError("DATABASE_UNAVAILABLE", "The remote durable database is not configured.", 503); }
  if (!["postgres:", "postgresql:"].includes(url.protocol) || !url.hostname || !url.username || !url.password || url.pathname === "/" || url.hash) throw new ProofPayError("DATABASE_UNAVAILABLE", "A remote authenticated PostgreSQL database is required. No local ledger fallback is available.", 503);
  // Connection-string SSL options otherwise overwrite pg's verified TLS object.
  for (const name of ["sslmode", "sslcert", "sslkey", "sslrootcert", "sslnegotiation"]) url.searchParams.delete(name);
  if (!cached || cached.url !== url.toString()) {
    if (cached) void cached.database.pool.end();
    const pool = new Pool({connectionString: url.toString(), ssl: {rejectUnauthorized: true}, max: 3, idleTimeoutMillis: 10000, connectionTimeoutMillis: 10000, statement_timeout: 10000, query_timeout: 15000, allowExitOnIdle: true, application_name: "proofpay"});
    // Do not log idle connection errors or connection strings. A later request
    // receives a bounded application error and retains its durable financial state.
    pool.on("error", () => {});
    cached = {url: url.toString(), database: new PostgresDatabase(pool)};
  }
  return cached.database;
}
