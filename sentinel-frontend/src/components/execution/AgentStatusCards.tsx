"use client";

import { Card } from "@/components/ui/card";
import { Workflow, Server, ShieldAlert, Code2, Sparkles, FileText, CheckCircle2, Loader2, XCircle, Clock } from "lucide-react";
import * as motion from "framer-motion/client";

const AGENTS = [
  { id: "supervisor", title: "Supervisor", icon: Workflow },
  { id: "repository", title: "Repository", icon: Server },
  { id: "security", title: "Security", icon: ShieldAlert },
  { id: "patch", title: "Patch Gen", icon: Code2 },
  { id: "enhancement", title: "AI Enhance", icon: Sparkles },
  { id: "documentation", title: "Reporting", icon: FileText },
];

export function AgentStatusCards({ timeline, currentAgent, globalStatus }: { timeline: any[], currentAgent: string | null, globalStatus: string }) {
  const getAgentStatus = (agentId: string) => {
    if (globalStatus === "FAILED") return "failed";
    const agentEvents = timeline.filter((e) => e.agent_id === agentId);
    if (agentEvents.some((e) => e.event_type === "COMPLETE")) return "completed";
    if (agentEvents.some((e) => e.event_type === "ERROR")) return "failed";
    
    // Check if running (we match either the agent_id or the registry name like agent_id + '_agent')
    if (currentAgent === agentId || currentAgent === `${agentId}_agent`) return "running";
    
    if (agentEvents.length > 0) return "queued";
    return "idle";
  };

  const getAgentProgress = (agentId: string) => {
    const progressEvents = timeline.filter(e => e.agent_id === agentId && e.event_type === "PROGRESS");
    if (progressEvents.length > 0) {
      return progressEvents[progressEvents.length - 1].message;
    }
    return null;
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
      {AGENTS.map((agent, i) => {
        const status = getAgentStatus(agent.id);
        const progressMsg = getAgentProgress(agent.id);
        
        const isRunning = status === "running";
        const isCompleted = status === "completed";
        const isFailed = status === "failed";
        
        return (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <Card className={`relative overflow-hidden p-4 h-full flex flex-col items-center text-center transition-colors ${isRunning ? 'border-primary glow-primary' : ''} ${isCompleted ? 'border-green-500/50' : ''}`}>
              <div className={`mb-3 rounded-full p-3 ${isRunning ? 'bg-primary/20 text-primary' : isCompleted ? 'bg-green-500/10 text-green-500' : 'bg-muted text-muted-foreground'}`}>
                <agent.icon className="h-6 w-6" />
              </div>
              <h4 className="font-medium text-sm mb-1">{agent.title}</h4>
              
              <div className="mt-auto flex items-center justify-center gap-1.5 text-xs">
                {isRunning && <><Loader2 className="h-3 w-3 animate-spin text-primary" /><span className="text-primary font-medium">Running</span></>}
                {isCompleted && <><CheckCircle2 className="h-3 w-3 text-green-500" /><span className="text-green-500 font-medium">Completed</span></>}
                {isFailed && <><XCircle className="h-3 w-3 text-destructive" /><span className="text-destructive font-medium">Failed</span></>}
                {status === "queued" && <><Clock className="h-3 w-3 text-muted-foreground" /><span className="text-muted-foreground">Queued</span></>}
                {status === "idle" && <span className="text-muted-foreground/50">Idle</span>}
              </div>
              
              {isRunning && progressMsg && (
                <p className="mt-2 text-[10px] text-muted-foreground truncate w-full max-w-[120px]">{progressMsg}</p>
              )}
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
