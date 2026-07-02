import { useQuery, useMutation } from "@tanstack/react-query";
import {
  analyzeProject,
  getExecutionStatus,
  getExecutionFindings,
  getExecutionManifest,
} from "./api";

export function useAnalyzeProject() {
  return useMutation({
    mutationFn: (params: { localPath: string, demoId?: string }) => analyzeProject(params.localPath, params.demoId),
  });
}

export function useExecutionStatus(executionId: string, options?: { refetchInterval?: number }) {
  return useQuery({
    queryKey: ["execution", executionId],
    queryFn: () => getExecutionStatus(executionId),
    refetchInterval: options?.refetchInterval,
  });
}

export function useExecutionFindings(executionId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["findings", executionId],
    queryFn: () => getExecutionFindings(executionId),
    enabled,
  });
}

export function useExecutionManifest(executionId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["manifest", executionId],
    queryFn: () => getExecutionManifest(executionId),
    enabled,
  });
}

export function useExecutionHistory() {
  return useQuery({
    queryKey: ["executions", "history"],
    queryFn: () => import("./api").then(m => m.listExecutions()),
  });
}
