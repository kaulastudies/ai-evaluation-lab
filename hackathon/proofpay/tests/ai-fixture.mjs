// Synthetic funding configuration for intercepted requests only. Not a real grant.
export function fundedAiConfig(overrides={}) {
  return {
    AI_FUNDING_MODE:'vercel-free-credit', AI_GATEWAY_FREE_ONLY_CONFIRMED:'true',
    AI_GATEWAY_GRANT_ID:'synthetic-test-grant',
    AI_GATEWAY_GRANT_EXPIRES_AT:new Date(Date.now()+24*60*60*1000).toISOString(),
    AI_GATEWAY_MAX_REQUESTS:'1', AI_GATEWAY_MODEL:'openai/gpt-4.1-mini',
    VERCEL_OIDC_TOKEN:'synthetic.oidc.token', ...overrides,
  };
}
