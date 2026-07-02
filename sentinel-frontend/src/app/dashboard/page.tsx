"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAnalyzeProject, useExecutionHistory } from "@/lib/queries";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FolderGit2, AlertTriangle, ArrowRight, Play, Server, ShieldAlert, Sparkles, TerminalSquare } from "lucide-react";
import * as motion from "framer-motion/client";

const DEMOS = [
  {
    id: "quickshop",
    name: "QuickShop API",
    difficulty: "Beginner",
    description: "Simple Python Flask backend with basic vulnerabilities.",
    tags: ["SQL Injection", "Exposed Secret", "Weak Auth"]
  },
  {
    id: "healthsync",
    name: "HealthSync Portal",
    difficulty: "Intermediate",
    description: "Node.js application handling sensitive medical data.",
    tags: ["Stored XSS", "Command Injection", "JWT Secrets"]
  },
  {
    id: "fintrust",
    name: "FinTrust Platform",
    difficulty: "Advanced",
    description: "Complex FastAPI & Next.js microservices architecture.",
    tags: ["SSRF", "Docker Leaks", "CI/CD Secrets"]
  }
];

export default function DashboardPage() {
  const router = useRouter();
  const analyzeMutation = useAnalyzeProject();
  const historyQuery = useExecutionHistory();
  const [localPath, setLocalPath] = useState("");
  const [activeTab, setActiveTab] = useState<"local" | "demo">("local");

  const handleAnalyzeLocal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!localPath) return;
    try {
      const response = await analyzeMutation.mutateAsync({ localPath });
      if (response.execution_id) {
        router.push(`/dashboard/executions/${response.execution_id}`);
      }
    } catch (error) {
      console.error("Failed to start analysis:", error);
    }
  };

  const handleAnalyzeDemo = async (demoId: string) => {
    try {
      const response = await analyzeMutation.mutateAsync({ localPath: "", demoId });
      if (response.execution_id) {
        router.push(`/dashboard/executions/${response.execution_id}`);
      }
    } catch (error) {
      console.error("Failed to start demo analysis:", error);
    }
  };

  return (
    <div className="container mx-auto max-w-6xl px-4 py-12">
      <div className="mb-10">
        <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-primary to-primary/50">Dashboard</h1>
        <p className="text-muted-foreground mt-2 text-lg">Manage your autonomous repository security analyses.</p>
      </div>

      <div className="flex space-x-1 mb-8 bg-secondary/30 p-1 rounded-xl w-fit border border-white/5 backdrop-blur-md">
        <button
          onClick={() => setActiveTab("local")}
          className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === "local" ? 'bg-primary/20 text-primary shadow-sm border border-primary/20' : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'}`}
        >
          Local Scan
        </button>
        <button
          onClick={() => setActiveTab("demo")}
          className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${activeTab === "demo" ? 'bg-primary/20 text-primary shadow-sm border border-primary/20' : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'}`}
        >
          <Sparkles className="w-4 h-4" /> Demo Mode
        </button>
      </div>

      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {activeTab === "local" ? (
          <div className="grid gap-8 md:grid-cols-2">
            <Card className="glass-card hover-glow transition-all h-fit">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TerminalSquare className="h-5 w-5 text-primary" />
                  New Analysis
                </CardTitle>
                <CardDescription>Enter a local repository absolute path to begin a comprehensive security scan.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleAnalyzeLocal} className="space-y-4">
                  <div className="space-y-2">
                    <input
                      type="text"
                      placeholder="C:\Users\Developer\MyProject"
                      className="flex h-11 w-full rounded-md border border-input bg-background/50 backdrop-blur-sm px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-all hover:bg-background/80"
                      value={localPath}
                      onChange={(e) => setLocalPath(e.target.value)}
                      disabled={analyzeMutation.isPending}
                    />
                  </div>
                  <Button type="submit" className="w-full h-11 font-medium bg-gradient-to-r from-primary/80 to-primary hover:from-primary hover:to-primary/80 transition-all shadow-[0_0_20px_rgba(var(--primary),0.3)]" disabled={analyzeMutation.isPending || !localPath}>
                    {analyzeMutation.isPending ? "Starting Analysis..." : "Analyze Repository"}
                  </Button>
                  {analyzeMutation.isError && (
                    <p className="text-sm text-destructive mt-2 font-medium">Failed to start analysis. Please verify the path.</p>
                  )}
                </form>
              </CardContent>
            </Card>

            <div className="flex flex-col gap-4 h-[400px] overflow-y-auto pr-2 custom-scrollbar">
              {historyQuery.isLoading ? (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  Loading history...
                </div>
              ) : historyQuery.data && historyQuery.data.length > 0 ? (
                historyQuery.data.map((item) => (
                  <Card key={item.execution_id} className="glass-card hover-glow transition-all">
                    <CardHeader className="py-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-base">{item.project_name}</CardTitle>
                          <CardDescription className="text-xs">
                            {new Date(item.created_at || '').toLocaleDateString()}
                          </CardDescription>
                        </div>
                        <span className={`text-[10px] font-bold px-2 py-1 rounded-full uppercase ${
                          item.status === 'COMPLETED' ? 'bg-green-500/10 text-green-500' :
                          item.status === 'FAILED' ? 'bg-red-500/10 text-red-500' :
                          'bg-yellow-500/10 text-yellow-500'
                        }`}>
                          {item.status}
                        </span>
                      </div>
                    </CardHeader>
                    <CardContent className="py-0 pb-4">
                      <div className="flex justify-between items-center mt-2">
                        <div className="text-sm">
                          <span className="text-muted-foreground">Threat Score: </span>
                          <span className={item.threat_score > 50 ? 'text-destructive font-bold' : 'text-primary'}>
                            {item.threat_score}
                          </span>
                        </div>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="gap-2 text-xs"
                          onClick={() => router.push(`/dashboard/executions/${item.execution_id}`)}
                        >
                          View Report <ArrowRight className="h-3 w-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <Card className="flex flex-col items-center justify-center border-dashed border-2 p-12 text-center h-full min-h-[300px] bg-secondary/10 hover:bg-secondary/20 transition-all">
                  <div className="rounded-full bg-secondary p-4 mb-4 shadow-inner">
                    <AlertTriangle className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">No active analyses</h3>
                  <p className="text-sm text-muted-foreground max-w-sm mb-6">
                    You haven't run any security scans yet. Enter a repository path to begin your first autonomous audit.
                  </p>
                </Card>
              )}
            </div>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-3">
            {DEMOS.map((demo, i) => (
              <motion.div
                key={demo.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -5 }}
              >
                <Card className="glass-card hover-glow h-full flex flex-col group overflow-hidden border-white/10">
                  <div className="h-2 w-full bg-gradient-to-r from-primary/40 via-primary to-primary/40 opacity-50 group-hover:opacity-100 transition-opacity" />
                  <CardHeader>
                    <div className="flex justify-between items-start mb-2">
                      <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                        <Server className="h-5 w-5" />
                      </div>
                      <span className={`text-[10px] uppercase font-bold tracking-wider px-2.5 py-1 rounded-full ${
                        demo.difficulty === 'Beginner' ? 'bg-green-500/10 text-green-500' :
                        demo.difficulty === 'Intermediate' ? 'bg-yellow-500/10 text-yellow-500' :
                        'bg-red-500/10 text-red-500'
                      }`}>
                        {demo.difficulty}
                      </span>
                    </div>
                    <CardTitle className="text-xl">{demo.name}</CardTitle>
                    <CardDescription className="pt-2">{demo.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="flex-1 flex flex-col justify-end">
                    <div className="flex flex-wrap gap-2 mb-6 mt-4">
                      {demo.tags.map(tag => (
                        <span key={tag} className="text-xs bg-secondary/50 text-secondary-foreground px-2 py-1 rounded-md border border-white/5">
                          {tag}
                        </span>
                      ))}
                    </div>
                    <Button 
                      className="w-full gap-2 font-medium" 
                      variant="default"
                      onClick={() => handleAnalyzeDemo(demo.id)}
                      disabled={analyzeMutation.isPending}
                    >
                      <Play className="h-4 w-4" /> Run Demo Audit
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  );
}
