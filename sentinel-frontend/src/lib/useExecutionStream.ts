import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ExecutionStatusResponse } from "./api";

export function useExecutionStream(executionId: string, initialData?: ExecutionStatusResponse) {
  const [statusData, setStatusData] = useState<ExecutionStatusResponse | undefined>(initialData);
  const [error, setError] = useState<Error | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!executionId) return;

    // We can initialize it empty if we have no initialData
    const eventSource = new EventSource(`/api/executions/${executionId}/stream`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        setStatusData((prev) => {
          const newTimeline = prev ? [...prev.timeline] : [];
          // Deduplicate events by appending only if not already in timeline?
          // Since the backend sends historical events first, we just append them.
          // To be safe, let's keep a Set of seen event timestamps/types or just rebuild if it's the first message.
          
          // Actually, we can just replace the timeline with a merged version, or just trust the stream.
          // Wait, the stream yields historical events first. 
          // If we append blindly, we might get duplicates if the connection drops and reconnects.
          // The backend does not send 'id', but it sends 'timestamp', 'event_type', 'message'.
          // Let's use a unique key.
          const eventKey = `${data.timestamp}-${data.event_type}`;
          
          if (!prev) {
            return {
              execution_id: executionId,
              status: "RUNNING",
              progress: data.progress || 0,
              current_agent: data.agent_id,
              timeline: [data],
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            };
          }

          // Check if already in timeline
          const exists = prev.timeline.some(
            (t) => `${t.timestamp}-${t.event_type}` === eventKey
          );

          let updatedTimeline = prev.timeline;
          if (!exists) {
            updatedTimeline = [...prev.timeline, data];
          }

          let newStatus = prev.status;
          if (data.event_type === "ExecutionCompleted") newStatus = "COMPLETED";
          if (data.event_type === "ExecutionFailed") newStatus = "FAILED";
          
          let newCurrentAgent = data.agent_id || prev.current_agent;
          if (newStatus === "COMPLETED" || newStatus === "FAILED") {
            newCurrentAgent = null;
          }

          return {
            ...prev,
            status: newStatus,
            progress: data.progress || prev.progress,
            current_agent: newCurrentAgent,
            timeline: updatedTimeline,
            updated_at: new Date().toISOString(),
          };
        });

        // Trigger invalidations silently for other queries
        if (data.event_type === "COMPLETE") {
          if (data.agent_id === "security") {
            queryClient.invalidateQueries({ queryKey: ["findings", executionId] });
          } else if (data.agent_id === "patch") {
            queryClient.invalidateQueries({ queryKey: ["findings", executionId] });
          } else if (data.agent_id === "enhancement") {
            queryClient.invalidateQueries({ queryKey: ["findings", executionId] });
          } else if (data.agent_id === "repository") {
            queryClient.invalidateQueries({ queryKey: ["manifest", executionId] });
          }
        }
        
        if (data.event_type === "ExecutionCompleted" || data.event_type === "ExecutionFailed") {
          eventSource.close();
        }

      } catch (e) {
        console.error("Error parsing SSE data", e);
      }
    };

    eventSource.onerror = () => {
      // EventSource doesn't provide status codes, so we just set a generic error
      // and close the stream. This happens expectedly for 404s (expired sessions).
      setError(new Error("Stream connection failed"));
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [executionId, queryClient]);

  return {
    data: statusData,
    isLoading: !statusData && !error,
    isError: !!error,
  };
}
