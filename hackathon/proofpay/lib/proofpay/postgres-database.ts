import type { Pool, QueryResult, PoolClient } from "pg";
import type { SqlDatabase, SqlResult, SqlStatement } from "./types";

/** Translate the small reviewed SQLite SQL surface used by the service. Text
 * literals and comments are never rewritten; user values remain bound. */
export function postgresSql(sql: string): string {
  let index = 0;
  const parts = sql.match(/'(?:''|[^'])*'|"(?:""|[^"])*"|--[^\n]*(?:\n|$)|\/\*[\s\S]*?\*\/|[^'"\/-]+|[-\/]/g) ?? [];
  return parts.map(part => {
    if (part.startsWith("'") || part.startsWith('"') || part.startsWith("--") || part.startsWith("/*")) return part;
    return part.replace(/\browid\b/gi, "sequence").replace(/\bAS\s+(operationId|createdAt)\b/g, 'AS "$1"').replace(/\?/g, () => `$${++index}`).replace(/\bIS\s+NOT\s+(\$\d+)/gi, "IS DISTINCT FROM $1").replace(/\bIS\s+(\$\d+)/gi, "IS NOT DISTINCT FROM $1");
  }).join("");
}
function result<T>(value: QueryResult): SqlResult<T> {
  const rows = value.rows.map(row => {
    const normalized = {...row};
    for (const field of value.fields ?? []) if (field.dataTypeID === 20 && normalized[field.name] !== null) {
      const number = Number(normalized[field.name]);
      if (!Number.isSafeInteger(number)) throw new Error("Database integer is outside the application's safe range");
      normalized[field.name] = number;
    }
    return normalized;
  });
  return {results: rows as T[], meta: {changes: value.rowCount ?? 0}, success: true};
}
class Prepared implements SqlStatement {
  constructor(readonly database: PostgresDatabase, readonly sql: string, readonly args: unknown[] = []) {}
  bind(...values: unknown[]): SqlStatement {
    if (values.some(value => value !== null && typeof value !== "string" && (typeof value !== "number" || !Number.isSafeInteger(value)))) throw new Error("Unsupported SQL binding");
    return new Prepared(this.database, this.sql, values);
  }
  async first<T = Record<string, unknown>>(column?: string): Promise<T | null> {
    const row = (await this.all<Record<string, unknown>>()).results?.[0];
    return row ? (column ? row[column] : row) as T : null;
  }
  async all<T = Record<string, unknown>>(): Promise<SqlResult<T>> { return result<T>(await this.database.pool.query(postgresSql(this.sql), this.args)); }
  async run(): Promise<SqlResult> { return this.all(); }
}

export class PostgresDatabase implements SqlDatabase {
  constructor(readonly pool: Pool) {}
  prepare(sql: string): SqlStatement { return new Prepared(this, sql); }
  async batch(statements: SqlStatement[]): Promise<SqlResult[]> {
    const queries = statements.map(statement => {
      if (!(statement instanceof Prepared) || statement.database !== this) throw new Error("A transaction cannot mix database adapters");
      return {text: postgresSql(statement.sql), values: statement.args};
    });
    for (let attempt = 0; ; attempt++) {
      let client: PoolClient | undefined;
      try {
        client = await this.pool.connect();
        await client.query("BEGIN ISOLATION LEVEL SERIALIZABLE");
        const results: SqlResult[] = [];
        for (const query of queries) results.push(result(await client.query(query)));
        await client.query("COMMIT");
        return results;
      } catch (error) {
        let rolledBack = false;
        if (client) { try { await client.query("ROLLBACK"); rolledBack = true; } catch { /* Outcome is not known; never retry. */ } }
        const code = (error as {code?: unknown})?.code;
        // Retry only a complete SQL-only transaction that PostgreSQL explicitly
        // aborted. Never retry ambiguous transport/commit errors or provider work.
        if (!rolledBack || attempt >= 3 || !["40001", "40P01"].includes(String(code))) throw error;
      } finally { client?.release(); }
    }
  }
}
