export const CATALOGUE = [
  {sku: "workflow-review", title: "Workflow review", description: "One sandbox seller's digital workflow review package.", amountCents: 18000, currency: "USD"},
  {sku: "design-review", title: "Design review", description: "One sandbox seller's digital design review package.", amountCents: 16000, currency: "USD"},
  {sku: "starter-review", title: "Starter review", description: "A smaller digital review scope that costs $90.", amountCents: 9000, currency: "USD"},
] as const;
export function amountString(cents: number): string { return `${Math.floor(cents / 100)}.${String(cents % 100).padStart(2, "0")}`; }
export function parseAmount(value: string | undefined): number | null { if (!value || !/^\d{1,10}\.\d{2}$/.test(value)) return null; const [whole, fraction] = value.split("."); const cents = Number(whole) * 100 + Number(fraction); return Number.isSafeInteger(cents) ? cents : null; }
