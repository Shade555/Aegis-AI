"use client";

import { useParams } from "next/navigation";
import { useExecutionStream } from "@/lib/useExecutionStream";
import { AgentThinkingPanel } from "@/components/execution/AgentThinkingPanel";
import { AgentStatusCards } from "@/components/execution/AgentStatusCards";
import { RepositoryOverview } from "@/components/execution/RepositoryOverview";
import { ExecutionTimeline } from "@/components/execution/ExecutionTimeline";
import { FindingsTable } from "@/components/execution/FindingsTable";
import { PatchViewer } from "@/components/execution/PatchViewer";
import { AIAssistantPanel } from "@/components/execution/AIAssistantPanel";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Loader2, AlertCircle } from "lucide-react";
import Link from "next/link";
import { Progress } from "@/components/ui/progress";
import * as React from "react";
import * as motion from "framer-motion/client";

export default function ExecutionDetailsPage() {
  const params = useParams();
  const executionId = params.id as string;

  const { data: statusData, isLoading, isError } = useExecutionStream(executionId);

  if (isLoading) {
    return (
      <div className="container mx-auto flex h-[80vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-muted-foreground">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p>Loading execution details...</p>
        </div>
      </div>
    );
  }

  if (isError || !statusData) {
    return (
      <div className="container mx-auto flex h-[80vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-center">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <h2 className="text-xl font-bold">Execution Not Found</h2>
          <p className="text-muted-foreground max-w-md">
            The requested execution session could not be found. It may have expired from the in-memory cache.
          </p>
          <Button asChild className="mt-4">
            <Link href="/dashboard">Return to Dashboard</Link>
          </Button>
        </div>
      </div>
    );
  }

  const { status, progress, current_agent, timeline } = statusData;
  const isRunning = status !== "COMPLETED" && status !== "FAILED";

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <Button variant="ghost" size="sm" asChild className="-ml-3 mb-2 text-muted-foreground">
            <Link href="/dashboard"><ArrowLeft className="mr-2 h-4 w-4" /> Back to Dashboard</Link>
          </Button>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            Execution Details
            <span className={`text-sm px-2.5 py-0.5 rounded-full border ${status === 'COMPLETED' ? 'border-green-500 text-green-500 bg-green-500/10' : status === 'FAILED' ? 'border-destructive text-destructive bg-destructive/10' : 'border-primary text-primary bg-primary/10'}`}>
              {status}
            </span>
          </h1>
          <p className="text-sm font-mono text-muted-foreground mt-2">{executionId}</p>
        </div>

        {status === "COMPLETED" && (
          <div className="flex gap-2">
            <Button size="sm" className="bg-primary/90 hover:bg-primary shadow-lg shadow-primary/20" asChild>
              <Link href={`/dashboard/executions/${executionId}/report`}>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/></svg>
                View Final Report
              </Link>
            </Button>
          </div>
        )}
      </div>

      {/* Progress Bar (Global) */}
      {isRunning && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-2">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Overall Progress</span>
            <span>{Math.round(progress * 100)}%</span>
          </div>
          <Progress value={progress * 100} className="h-2" />
        </motion.div>
      )}

      {/* Repository Overview */}
      <RepositoryOverview executionId={executionId} />

      {/* Agent Thinking Panel */}
      {isRunning && (
        <AgentThinkingPanel timeline={timeline || []} currentAgent={current_agent} />
      )}

      {/* Agent Status Cards */}
      <AgentStatusCards 
        timeline={timeline || []} 
        currentAgent={current_agent} 
        globalStatus={status} 
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <ExecutionTimeline timeline={timeline || []} />
        </div>
        <div className="lg:col-span-2 space-y-6">
          <FindingsTable executionId={executionId} />
          <PatchViewer executionId={executionId} />
        </div>
      </div>

      <AIAssistantPanel executionId={executionId} status={status} />
    </div>
  );
}
