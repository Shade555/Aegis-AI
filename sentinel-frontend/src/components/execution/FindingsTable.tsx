"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ShieldAlert, Info, AlertTriangle, Bug, Sparkles } from "lucide-react";
import { useExecutionFindings } from "@/lib/queries";
import { Skeleton } from "@/components/ui/skeleton";

export function FindingsTable({ executionId }: { executionId: string }) {
  const { data, isLoading } = useExecutionFindings(executionId);

  if (isLoading) {
    return (
      <Card className="glass-card mt-6">
        <CardHeader>
          <CardTitle className="text-lg">Security Findings</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full" />
        </CardContent>
      </Card>
    );
  }

  const findings = data?.findings || [];

  if (findings.length === 0) {
    return (
      <Card className="glass-card mt-6">
        <CardHeader>
          <CardTitle className="text-lg">Security Findings</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center py-12 text-center">
          <ShieldAlert className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
          <h3 className="text-lg font-medium">No Vulnerabilities Found</h3>
          <p className="text-sm text-muted-foreground mt-2 max-w-md">
            The security agents did not detect any vulnerabilities in the repository based on the active ruleset.
          </p>
        </CardContent>
      </Card>
    );
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case "CRITICAL": return <Badge className="bg-destructive hover:bg-destructive text-destructive-foreground">CRITICAL</Badge>;
      case "HIGH": return <Badge className="bg-orange-500 hover:bg-orange-600 text-white">HIGH</Badge>;
      case "MEDIUM": return <Badge className="bg-yellow-500 hover:bg-yellow-600 text-white">MEDIUM</Badge>;
      case "LOW": return <Badge className="bg-green-500 hover:bg-green-600 text-white">LOW</Badge>;
      default: return <Badge variant="outline">{severity}</Badge>;
    }
  };

  return (
    <Card className="glass-card mt-6">
      <CardHeader>
        <CardTitle className="text-lg flex items-center justify-between">
          <span>Security Findings</span>
          <Badge variant="secondary">{findings.length} total</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Accordion type="multiple" className="w-full space-y-4">
          {findings.map((finding, i) => (
            <AccordionItem value={`item-${i}`} key={i} className="border rounded-lg px-4 bg-background">
              <AccordionTrigger className="hover:no-underline">
                <div className="flex flex-1 items-center gap-4 text-left">
                  <div className="w-24">{getSeverityBadge(finding.severity)}</div>
                  <div className="flex-1 font-semibold flex items-center gap-2">
                    {finding.title}
                    {finding.ai_enhancement && (
                      <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/20 text-[10px] uppercase py-0 px-1.5 h-4 inline-flex items-center gap-1 whitespace-nowrap shrink-0">
                        <Sparkles className="h-3 w-3 shrink-0" /> AI Enhanced
                      </Badge>
                    )}
                  </div>
                  <div className="hidden md:block w-48 text-sm text-muted-foreground truncate shrink-0">{finding.file_path}:{finding.line_start}</div>
                  <div className="hidden sm:flex w-28 items-center justify-end shrink-0">
                    <Badge variant="outline" className="whitespace-nowrap">{finding.confidence} CONF</Badge>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="pt-4 border-t">
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-semibold mb-1 flex items-center gap-2"><Bug className="h-4 w-4 text-muted-foreground" /> Description</h4>
                      <p className="text-sm text-muted-foreground">{finding.description}</p>
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold mb-1 flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-muted-foreground" /> Remediation</h4>
                      <p className="text-sm text-muted-foreground">{finding.remediation_recommendation}</p>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="rounded-md border bg-secondary/30 p-4">
                      <h4 className="text-sm font-semibold mb-2 flex items-center gap-2 text-primary"><Info className="h-4 w-4" /> AI Reasoning</h4>
                      {finding.ai_enhancement ? (
                        <div className="space-y-3">
                          <p className="text-sm text-muted-foreground"><strong className="text-foreground">Explanation:</strong> {finding.ai_enhancement.explanation}</p>
                          <p className="text-sm text-muted-foreground"><strong className="text-foreground">Impact:</strong> {finding.ai_enhancement.impact}</p>
                          <p className="text-sm text-muted-foreground"><strong className="text-foreground">Severity Justification:</strong> {finding.ai_enhancement.severity_justification}</p>
                          <p className="text-sm text-muted-foreground"><strong className="text-foreground">Secure Coding:</strong> {finding.ai_enhancement.secure_coding_recommendation}</p>
                          <p className="text-sm text-muted-foreground"><strong className="text-foreground">Best Practices:</strong> {finding.ai_enhancement.best_practices}</p>
                        </div>
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          {finding.explanation || `The agent detected a pattern matching the ${finding.rule_id} security rule.`}
                        </p>
                      )}
                    </div>
                    {finding.code_snippet && (
                      <div className="rounded-md bg-zinc-950 p-4 border border-zinc-800 overflow-x-auto">
                        <pre className="text-xs font-mono text-zinc-300">
                          <code>{finding.code_snippet}</code>
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </CardContent>
    </Card>
  );
}
