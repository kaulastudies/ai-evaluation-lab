import { redirect } from "next/navigation";
import PurchaseDesk from "../components/proofpay/purchase-desk";

export const dynamic = "force-dynamic";
export default function Home() {
  if (process.env.JUDGE_DEMO_ONLY === "true") redirect("/judge");
  return <PurchaseDesk />;
}
