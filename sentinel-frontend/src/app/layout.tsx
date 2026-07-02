import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Aegis AI — Autonomous Security Intelligence",
    template: "%s | Aegis AI",
  },
  description:
    "An autonomous multi-agent AI security engineering platform. Audits software repositories, detects vulnerabilities, generates patches, and produces professional security reports.",
  keywords: ["security", "AI", "vulnerability", "audit", "code analysis"],
};

import Providers from "@/components/providers/QueryProvider";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    // "dark" class ensures our CSS variables (dark-mode-first) are always active.
    <html lang="en" className={`dark ${inter.variable}`}>
      <body className="flex min-h-screen flex-col bg-background text-foreground antialiased">
        <ClerkProvider>
          <Providers>
            <Header />
            <main className="flex-1">{children}</main>
            <Footer />
          </Providers>
        </ClerkProvider>
      </body>
    </html>
  );
}
