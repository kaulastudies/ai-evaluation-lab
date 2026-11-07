import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProofPay — Purchase Desk",
  description: "A studio purchase desk with shared allowances, owner approval and inspectable payment outcomes.",
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
