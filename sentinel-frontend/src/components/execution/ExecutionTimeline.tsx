"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { format } from "date-fns";
import * as motion from "framer-motion/client";

export function ExecutionTimeline({ timeline }: { timeline: any[] }) {
  if (!timeline || timeline.length === 0) {
    return (
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg">Execution Timeline</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          No events recorded yet.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="text-lg">Execution Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative border-l border-border ml-3 space-y-6">
          {timeline.map((event, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05, type: "spring", stiffness: 100 }}
              className="relative pl-6"
            >
              <span className="absolute -left-1.5 top-1.5 h-3 w-3 rounded-full border-2 border-background bg-primary" />
              <div className="flex flex-col gap-1">
                <span className="text-xs font-mono text-muted-foreground">
                  {format(new Date(event.timestamp), "HH:mm:ss.SSS")} - {event.agent_id}
                </span>
                <span className="text-sm font-medium">{event.event_type}</span>
                {event.message && (
                  <p className="text-sm text-muted-foreground">{event.message}</p>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
