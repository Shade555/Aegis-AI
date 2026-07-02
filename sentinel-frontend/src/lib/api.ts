import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

export interface AnalyzeProjectResponse {
  execution_id: string;
  status: string;
}

export async function analyzeProject(localPath: string, demoId?: string): Promise<AnalyzeProjectResponse> {
  const formData = new FormData();
  if (localPath) formData.append("local_path", localPath);
  if (demoId) formData.append("demo_id", demoId);
  const response = await api.post("/analyze", formData);
  return response.data;
}

export interface ExecutionStatusResponse {
  execution_id: string;
  status: string;
  progress: number;
  current_agent: string | null;
  timeline: {
    timestamp: string;
    agent_id: string;
    event_type: string;
    message: string;
    metadata: any;
  }[];
  created_at: string | null;
  updated_at: string | null;
}

export async function getExecutionStatus(executionId: string): Promise<ExecutionStatusResponse> {
  const response = await api.get(`/executions/${executionId}`);
  return response.data;
}

export interface ExecutionFindingsResponse {
  threat_score: number;
  findings: any[];
  patches: any[];
  severity_counts: Record<string, number>;
  confidence_summary: Record<string, number>;
}

export async function getExecutionFindings(executionId: string): Promise<ExecutionFindingsResponse> {
  const response = await api.get(`/executions/${executionId}/findings`);
  return response.data;
}

export async function getExecutionManifest(executionId: string): Promise<any> {
  const response = await api.get(`/executions/${executionId}/manifest`);
  return response.data;
}

export interface ExecutionHistoryItem {
  execution_id: string;
  project_name: string;
  status: string;
  threat_score: number;
  created_at: string | null;
  updated_at: string | null;
  progress: number;
}

export async function listExecutions(): Promise<ExecutionHistoryItem[]> {
  const response = await api.get("/executions");
  return response.data;
}
