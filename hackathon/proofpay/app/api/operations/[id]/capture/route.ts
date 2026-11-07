import { handle } from "@/lib/proofpay/http";
export async function POST(request: Request, context: { params: Promise<{ id: string }> }) { const { id } = await context.params; return handle(request, "capture", id); }
