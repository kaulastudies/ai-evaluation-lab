import { ownerLogin } from "@/lib/proofpay/login";
export const runtime = "nodejs";
export async function POST(request: Request) { return ownerLogin(request, true); }
