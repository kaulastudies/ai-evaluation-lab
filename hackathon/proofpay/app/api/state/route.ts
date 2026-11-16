import { handle } from "@/lib/proofpay/http";
export async function GET(request: Request) { return handle(request, "state"); }
