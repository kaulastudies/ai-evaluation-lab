import { handle } from "@/lib/proofpay/http";
export async function GET(request: Request) { return handle(request, "business"); }
export async function POST(request: Request) { return handle(request, "save-business"); }
