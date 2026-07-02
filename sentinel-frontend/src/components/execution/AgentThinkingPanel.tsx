import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Brain, Terminal } from "lucide-react";
import * as motion from "framer-motion/client";

interface AgentThinkingPanelProps {
  timeline: any[];
  currentAgent: string | null;
}

export function AgentThinkingPanel({ timeline, currentAgent }: AgentThinkingPanelProps) {
  // Find the most recent event for the active agent that isn't a terminal event
  const activeAgentEvents = timeline.filter(
    (e) => e.agent_id === currentAgent && !e.event_type.includes("COMPLETED")
  );
  const latestEvent = activeAgentEvents.length > 0 ? activeAgentEvents[activeAgentEvents.length - 1] : null;

  if (!currentAgent) return null;

  return (
    <Card className="bg-muted/50 border-primary/20 overflow-hidden">
      <CardHeader className="py-3 px-4 bg-muted/80 border-b flex flex-row items-center space-y-0 gap-2">
        <Brain className="h-4 w-4 text-primary animate-pulse" />
        <CardTitle className="text-sm font-mono tracking-tight font-medium text-primary">
          {currentAgent} reasoning
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="bg-black/90 p-4 font-mono text-xs sm:text-sm text-green-400 min-h-[80px] max-h-[200px] overflow-y-auto">
          {latestEvent ? (
            <motion.div
              key={latestEvent.timestamp}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-2"
            >
              <Terminal className="h-4 w-4 shrink-0 mt-0.5 opacity-50" />
              <span>{latestEvent.message}</span>
            </motion.div>
          ) : (
            <div className="flex items-center gap-2 opacity-50">
              <Terminal className="h-4 w-4" />
              <span className="animate-pulse">Initializing reasoning engine...</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
