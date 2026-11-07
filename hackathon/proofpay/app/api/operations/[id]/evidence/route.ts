import { handle } from "@/lib/proofpay/http";
export async function GET(request: Request, context: { params: Promise<{ id: string }> }) { const { id } = await context.params; return handle(request, "evidence", id); }
