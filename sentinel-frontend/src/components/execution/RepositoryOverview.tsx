"use client";

import { useExecutionManifest, useExecutionFindings } from "@/lib/queries";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Shield, Code, Layers, FileCode } from "lucide-react";

export function RepositoryOverview({ executionId }: { executionId: string }) {
  const { data: manifest, isLoading: isManifestLoading } = useExecutionManifest(executionId);
  const { data: findings, isLoading: isFindingsLoading } = useExecutionFindings(executionId);

  if (isManifestLoading || isFindingsLoading) {
    return <Skeleton className="h-40 w-full" />;
  }

  const threatScore = findings?.threat_score ?? 0;
  
  return (
    <Card className="glass-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Repository Overview</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
          <div className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground flex items-center gap-1"><Layers className="h-3 w-3" /> Framework</span>
            <span className="font-medium">{manifest?.project_type && manifest.project_type !== "Unknown" ? manifest.project_type : (manifest?.frameworks?.[0] || "Unknown")}</span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground flex items-center gap-1"><Code className="h-3 w-3" /> Languages</span>
            <span className="font-medium capitalize">{manifest?.languages?.join(", ") || "None"}</span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground flex items-center gap-1"><FileCode className="h-3 w-3" /> Files</span>
            <span className="font-medium">{manifest?.file_count || 0}</span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground flex items-center gap-1"><Layers className="h-3 w-3" /> Dependencies</span>
            <span className="font-medium">{manifest?.dependencies?.length || 0}</span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground flex items-center gap-1"><Shield className="h-3 w-3" /> Threat Score</span>
            <span className={`font-bold text-lg ${threatScore > 50 ? 'text-destructive' : threatScore > 0 ? 'text-orange-500' : 'text-green-500'}`}>
              {threatScore}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
