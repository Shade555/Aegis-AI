"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { FileCode, Clock, GitMerge, Sparkles, CheckCircle2 } from "lucide-react";
import { useExecutionFindings } from "@/lib/queries";
import { Skeleton } from "@/components/ui/skeleton";
import ReactMarkdown from "react-markdown";

export function PatchViewer({ executionId }: { executionId: string }) {
  const { data, isLoading } = useExecutionFindings(executionId);

  if (isLoading) {
    return (
      <Card className="glass-card mt-6">
        <CardHeader><CardTitle className="text-lg">Generated Patches</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-48 w-full" /></CardContent>
      </Card>
    );
  }

  const patches = data?.patches || [];

  if (patches.length === 0) {
    return (
      <Card className="glass-card mt-6">
        <CardHeader><CardTitle className="text-lg">Generated Patches</CardTitle></CardHeader>
        <CardContent className="flex flex-col items-center py-12 text-center">
          <GitMerge className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
          <h3 className="text-lg font-medium">No Patches Generated</h3>
          <p className="text-sm text-muted-foreground mt-2 max-w-md">
            The Patch Agent did not find any fixable vulnerabilities or hasn't run yet.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-card mt-6">
      <CardHeader>
        <CardTitle className="text-lg flex items-center justify-between">
          <span className="flex items-center gap-2"><GitMerge className="h-5 w-5 text-green-500" /> Proposed Patches</span>
          <Badge variant="secondary" className="bg-green-500/10 text-green-500 border-green-500/20">{patches.length} Available</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Accordion type="multiple" className="w-full space-y-4">
          {patches.map((patch: any, i: number) => (
            <AccordionItem value={`patch-${i}`} key={i} className="border rounded-lg px-0 bg-background overflow-hidden">
              <AccordionTrigger className="hover:no-underline px-4 bg-secondary/20">
                <div className="flex flex-1 items-center justify-between text-left">
                  <div className="flex items-center gap-3">
                    <FileCode className="h-4 w-4 text-muted-foreground" />
                    <span className="font-mono text-sm font-semibold">{patch.file_path}</span>
                    {patch.ai_explanation && (
                      <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/20 text-[10px] uppercase py-0 px-1.5 h-4 ml-2 flex items-center gap-1">
                        <Sparkles className="h-3 w-3" /> AI Enhanced
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-4 mr-4">
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" /> {patch.estimated_review_time}
                    </div>
                    <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
                      {patch.confidence} CONF
                    </Badge>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="pt-0 border-t">
                
                {/* AI Explanation Bar */}
                {patch.ai_explanation && (
                  <div className="bg-primary/5 border-b border-primary/10 p-4">
                    <div className="flex gap-4">
                      <div className="bg-primary/20 p-2 rounded-full h-fit">
                        <Sparkles className="h-4 w-4 text-primary" />
                      </div>
                      <div className="space-y-3">
                        <div>
                          <h4 className="text-xs font-bold uppercase tracking-wider text-primary mb-1">AI Explanation</h4>
                          <p className="text-sm text-foreground leading-relaxed">{patch.ai_explanation.explanation}</p>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Why this fix?</h4>
                            <p className="text-sm text-muted-foreground">{patch.ai_explanation.why_preferred}</p>
                          </div>
                          <div>
                            <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Trade-offs</h4>
                            <p className="text-sm text-muted-foreground">{patch.ai_explanation.trade_offs}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Diff Viewer */}
                <div className="bg-zinc-950 font-mono text-xs md:text-sm overflow-x-auto w-full">
                  {patch.unified_diff.split('\n').map((line: string, lineIdx: number) => {
                    if (line.startsWith('+') && !line.startsWith('+++')) {
                      return <div key={lineIdx} className="bg-green-950/40 text-green-400 px-4 py-0.5 border-l-2 border-green-500"><span className="select-none inline-block w-4 mr-2 text-green-700">+</span>{line.substring(1)}</div>;
                    }
                    if (line.startsWith('-') && !line.startsWith('---')) {
                      return <div key={lineIdx} className="bg-red-950/40 text-red-400 px-4 py-0.5 border-l-2 border-red-500"><span className="select-none inline-block w-4 mr-2 text-red-700">-</span>{line.substring(1)}</div>;
                    }
                    if (line.startsWith('@@')) {
                      return <div key={lineIdx} className="bg-blue-950/20 text-blue-400 px-4 py-1 my-1 opacity-70"><span className="select-none inline-block w-4 mr-2"> </span>{line}</div>;
                    }
                    if (line.startsWith('---') || line.startsWith('+++')) {
                      return <div key={lineIdx} className="text-zinc-500 px-4 py-0.5 font-bold"><span className="select-none inline-block w-4 mr-2"> </span>{line}</div>;
                    }
                    return <div key={lineIdx} className="text-zinc-300 px-4 py-0.5"><span className="select-none inline-block w-4 mr-2 text-zinc-600"> </span>{line}</div>;
                  })}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </CardContent>
    </Card>
  );
}
