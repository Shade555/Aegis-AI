import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ShieldAlert, Server, Code2, Workflow, Bot, ChevronRight, Zap } from "lucide-react";
import * as motion from "framer-motion/client";

export default function LandingPage() {
  return (
    <div className="flex flex-col items-center relative overflow-hidden">
      {/* Aurora Background */}
      <div className="absolute top-[-20%] left-[-10%] w-[120%] h-[120%] z-[-1] pointer-events-none opacity-40">
        <div className="absolute top-[20%] left-[20%] w-[50%] h-[50%] bg-primary/30 blur-[120px] rounded-full mix-blend-screen animate-pulse" style={{ animationDuration: '8s' }} />
        <div className="absolute top-[40%] right-[20%] w-[40%] h-[40%] bg-blue-500/20 blur-[100px] rounded-full mix-blend-screen animate-pulse" style={{ animationDuration: '10s', animationDelay: '2s' }} />
        <div className="absolute bottom-[20%] left-[40%] w-[40%] h-[40%] bg-purple-500/20 blur-[100px] rounded-full mix-blend-screen animate-pulse" style={{ animationDuration: '12s', animationDelay: '4s' }} />
      </div>

      {/* Hero Section */}
      <section className="w-full flex justify-center pb-24 pt-40 text-center relative z-10">
        <div className="container max-w-5xl px-4 flex flex-col items-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="flex flex-col items-center"
          >
            <div className="mb-6 inline-flex items-center rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-sm font-medium text-primary backdrop-blur-md">
              <SparklesIcon className="mr-2 h-4 w-4" />
              Introducing Aegis AI 1.0
            </div>
            <h1 className="mb-6 text-6xl font-extrabold tracking-tight sm:text-7xl lg:text-8xl leading-tight">
              Autonomous <br />
              <span className="bg-gradient-to-r from-primary via-blue-400 to-purple-500 bg-clip-text text-transparent">Security Intelligence</span>
            </h1>
            <p className="mb-10 text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              The premier multi-agent AI platform that automatically audits repositories, detects critical vulnerabilities, generates secure patches, and synthesizes executive security reports.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4 w-full sm:w-auto">
              <Button size="lg" className="h-14 px-8 text-lg font-medium shadow-[0_0_30px_rgba(var(--primary),0.3)] bg-primary hover:bg-primary/90 transition-all" asChild>
                <Link href="/dashboard">
                  Start Analysis <ChevronRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" className="h-14 px-8 text-lg glass-card border-white/10 hover:bg-white/5" asChild>
                <a href="#how-it-works">Explore Architecture</a>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Interactive Architecture Map */}
      <section id="how-it-works" className="w-full flex justify-center py-32 relative z-10">
        <div className="absolute inset-0 bg-secondary/20 backdrop-blur-xl border-y border-white/5" />
        <div className="container max-w-6xl px-4 relative">
          <div className="mb-20 text-center">
            <h2 className="text-4xl font-bold tracking-tight">Multi-Agent Architecture</h2>
            <p className="mt-4 text-xl text-muted-foreground max-w-2xl mx-auto">Specialized AI agents working in concert to secure your codebase, mirroring elite red and blue teams.</p>
          </div>
          
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {[
              { title: "Supervisor", description: "Orchestrates the workflow, delegates tasks, and synthesizes the final report.", icon: Workflow, color: "from-blue-500/20 to-blue-500/0", border: "border-blue-500/30" },
              { title: "Repository", description: "Parses the codebase, identifies frameworks, and maps dependencies.", icon: Server, color: "from-purple-500/20 to-purple-500/0", border: "border-purple-500/30" },
              { title: "Security", description: "Performs static and dynamic analysis to detect critical vulnerabilities.", icon: ShieldAlert, color: "from-red-500/20 to-red-500/0", border: "border-red-500/30" },
              { title: "AI Patching", description: "Generates intelligent fixes and PRs for discovered issues via LLMs.", icon: Bot, color: "from-green-500/20 to-green-500/0", border: "border-green-500/30" }
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ delay: i * 0.15, duration: 0.6 }}
                className={`rounded-2xl border ${feature.border} bg-card/50 backdrop-blur-md p-8 shadow-2xl relative overflow-hidden group hover:-translate-y-2 transition-transform duration-300`}
              >
                <div className={`absolute top-0 left-0 w-full h-full bg-gradient-to-b ${feature.color} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                <div className="relative z-10">
                  <div className="bg-background/80 w-16 h-16 rounded-xl flex items-center justify-center mb-6 shadow-sm border border-white/5">
                    <feature.icon className="h-8 w-8 text-primary" />
                  </div>
                  <h3 className="mb-3 text-2xl font-semibold tracking-tight">{feature.title}</h3>
                  <p className="text-muted-foreground leading-relaxed">{feature.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="w-full flex justify-center py-32 relative z-10">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="container max-w-4xl px-4 text-center glass-card p-16 rounded-3xl border border-primary/20 relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-primary/5 blur-3xl" />
          <h2 className="text-4xl font-bold tracking-tight mb-6 relative z-10">Ready to secure your software?</h2>
          <p className="text-xl text-muted-foreground mb-10 max-w-xl mx-auto relative z-10">
            Deploy Aegis AI today and let autonomous agents handle your security posture.
          </p>
          <Button size="lg" className="h-14 px-10 text-lg relative z-10 shadow-lg" asChild>
            <Link href="/dashboard">
              Launch Dashboard <Zap className="ml-2 h-5 w-5" />
            </Link>
          </Button>
        </motion.div>
      </section>
    </div>
  );
}

function SparklesIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
      <path d="M5 3v4" />
      <path d="M19 17v4" />
      <path d="M3 5h4" />
      <path d="M17 19h4" />
    </svg>
  );
}
