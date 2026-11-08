import {handleJudge} from "@/lib/proofpay/judge-http";
export const runtime = "nodejs";
export async function GET(request: Request, context: {params: Promise<{path: string[]}>}) { return handleJudge(request, (await context.params).path); }
export async function POST(request: Request, context: {params: Promise<{path: string[]}>}) { return handleJudge(request, (await context.params).path); }
