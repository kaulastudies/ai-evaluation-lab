import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProofPay — Purchase Desk",
  description: "A payment operations workspace for purchase approvals, spending controls and verified outcomes.",
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/favicon.ico", type: "image/x-icon", sizes: "16x16 32x32 48x48" },
    ],
    shortcut: "/favicon.ico",
  },
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
