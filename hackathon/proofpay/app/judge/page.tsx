import type { Metadata } from "next";
import { notFound } from "next/navigation";
import JudgeDesk from "../../components/proofpay/judge-desk";

export const dynamic = "force-dynamic";
export const metadata: Metadata = {
  title: "ProofPay — Interactive Evaluator Rehearsal",
  description: "Try simulated purchase approval, held allowance and missing-response recovery. No live AI or real money is used in this evaluator rehearsal.",
};
export default function JudgePage() {
  if (process.env.JUDGE_DEMO_ONLY !== "true") notFound();
  return <JudgeDesk/>;
}
