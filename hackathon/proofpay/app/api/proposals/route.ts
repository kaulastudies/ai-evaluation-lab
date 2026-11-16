import { handle } from "@/lib/proofpay/http";
export async function POST(request: Request) { return handle(request, "propose"); }
