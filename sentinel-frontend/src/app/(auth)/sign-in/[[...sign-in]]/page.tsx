import { SignIn } from "@clerk/nextjs";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign In",
};

export default function SignInPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background">
      {/* Radial gradient background for depth */}
      <div
        className="pointer-events-none fixed inset-0 opacity-30"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% -10%, hsl(252 87% 67% / 0.2), transparent)",
        }}
      />
      <div className="relative z-10 flex flex-col items-center gap-8">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-xl"
            style={{
              background:
                "linear-gradient(135deg, hsl(252 87% 67%) 0%, hsl(221 83% 53%) 100%)",
            }}
          >
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 2L3 7V12C3 16.5 7 20.7 12 22C17 20.7 21 16.5 21 12V7L12 2Z"
                fill="white"
                fillOpacity="0.9"
              />
              <path
                d="M9 12L11 14L15 10"
                stroke="hsl(252 87% 67%)"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <span className="text-xl font-semibold tracking-tight text-foreground">
            Aegis AI
          </span>
        </div>
        {/* Clerk SignIn component */}
        <SignIn />
      </div>
    </main>
  );
}
