"use client";

import { useParams } from "next/navigation";
import { useExecutionFindings, useExecutionManifest } from "@/lib/queries";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Download, FileJson, FileText, Printer, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { format } from "date-fns";
import * as React from "react";
import ReactMarkdown from "react-markdown";

export default function ReportPreviewPage() {
  const params = useParams();
  const executionId = params.id as string;
  
  const { data: findingsData, isLoading: isLoadingFindings } = useExecutionFindings(executionId);
  const { data: manifestData, isLoading: isLoadingManifest } = useExecutionManifest(executionId);

  if (isLoadingFindings || isLoadingManifest) {
    return <div className="container mx-auto p-12 text-center text-muted-foreground animate-pulse">Generating Report...</div>;
  }

  if (!findingsData || !manifestData) {
    return <div className="container mx-auto p-12 text-center text-destructive">Report data not available.</div>;
  }

  const { threat_score, severity_counts, findings } = findingsData;
  const { project_name, languages, frameworks } = manifestData;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="container mx-auto max-w-5xl px-4 py-8">
      {/* Non-printable Header Controls */}
      <div className="print:hidden flex flex-col sm:flex-row justify-between items-center mb-10 gap-4 bg-secondary/20 p-4 rounded-xl border border-white/5">
        <Button variant="ghost" size="sm" asChild className="text-muted-foreground">
          <Link href={`/dashboard/executions/${executionId}`}><ArrowLeft className="mr-2 h-4 w-4" /> Back to Execution</Link>
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handlePrint}>
            <Printer className="mr-2 h-4 w-4" /> Print
          </Button>
          <Button variant="outline" size="sm" asChild>
            <a href={`/api/executions/${executionId}/reports/json`} target="_blank"><FileJson className="mr-2 h-4 w-4" /> JSON</a>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <a href={`/api/executions/${executionId}/reports/html`} target="_blank"><FileText className="mr-2 h-4 w-4" /> HTML</a>
          </Button>
          <Button size="sm" asChild className="bg-primary/90">
            <a href={`/api/executions/${executionId}/reports/pdf`} target="_blank"><Download className="mr-2 h-4 w-4" /> Download PDF</a>
          </Button>
        </div>
      </div>

      {/* Printable Report Content */}
      <div className="bg-background print:bg-white text-foreground print:text-black rounded-2xl border border-white/10 print:border-none p-8 md:p-12 shadow-2xl print:shadow-none space-y-12">
        
        {/* Cover Section */}
        <div className="border-b border-border print:border-gray-200 pb-12 flex flex-col md:flex-row justify-between items-start gap-8">
          <div>
            <div className="flex items-center gap-3 mb-6">
              <ShieldAlert className="h-10 w-10 text-primary print:text-black" />
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Aegis AI Security Report</h1>
                <p className="text-muted-foreground print:text-gray-500">Autonomous Security Intelligence</p>
              </div>
            </div>
            <h2 className="text-5xl font-black mb-4">{project_name || "Repository"}</h2>
            <p className="text-xl text-muted-foreground print:text-gray-600">Generated on {format(new Date(), "MMMM d, yyyy 'at' h:mm a")}</p>
          </div>
          <div className="text-right">
            <div className="inline-block text-center p-6 rounded-2xl bg-secondary/50 print:bg-gray-100 border border-white/5 print:border-gray-300">
              <p className="text-sm font-semibold uppercase tracking-wider text-muted-foreground print:text-gray-500 mb-2">Overall Threat Score</p>
              <div className={`text-6xl font-black ${
                threat_score > 70 ? 'text-destructive' : 
                threat_score > 30 ? 'text-yellow-500' : 
                'text-green-500'
              }`}>{threat_score}</div>
              <p className="text-sm font-medium mt-2">/ 100</p>
            </div>
          </div>
        </div>

        {/* Executive Summary & Architecture */}
        <div className="grid md:grid-cols-2 gap-12">
          <div>
            <h3 className="text-2xl font-bold mb-4 border-b border-border print:border-gray-200 pb-2">Executive Summary</h3>
            <p className="text-muted-foreground print:text-gray-700 leading-relaxed">
              Aegis AI performed an autonomous security audit on the <strong>{project_name}</strong> repository. 
              The analysis detected a total of <strong>{findings.length}</strong> vulnerabilities. 
              The most critical issues are related to {findings.length > 0 ? findings[0].rule_id : "No severe vulnerabilities"}. 
              Immediate remediation is highly recommended for any Critical or High severity findings.
            </p>
            <div className="mt-6 flex gap-4">
              <div className="bg-destructive/10 text-destructive print:bg-red-100 print:text-red-700 px-4 py-2 rounded-lg text-center flex-1">
                <span className="block text-2xl font-bold">{severity_counts.CRITICAL || 0}</span>
                <span className="text-xs uppercase font-bold tracking-wider">Critical</span>
              </div>
              <div className="bg-yellow-500/10 text-yellow-500 print:bg-yellow-100 print:text-yellow-700 px-4 py-2 rounded-lg text-center flex-1">
                <span className="block text-2xl font-bold">{severity_counts.HIGH || 0}</span>
                <span className="text-xs uppercase font-bold tracking-wider">High</span>
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="text-2xl font-bold mb-4 border-b border-border print:border-gray-200 pb-2">Tech Stack Profile</h3>
            <div className="space-y-4">
              <div>
                <p className="text-sm font-bold text-muted-foreground print:text-gray-500 uppercase tracking-wider mb-2">Languages</p>
                <div className="flex flex-wrap gap-2">
                  {languages?.map((lang: string) => (
                    <span key={lang} className="bg-secondary print:bg-gray-100 px-3 py-1 rounded-md text-sm font-medium">{lang}</span>
                  ))}
                  {!languages?.length && <span className="text-muted-foreground">None detected</span>}
                </div>
              </div>
              <div>
                <p className="text-sm font-bold text-muted-foreground print:text-gray-500 uppercase tracking-wider mb-2">Frameworks</p>
                <div className="flex flex-wrap gap-2">
                  {frameworks?.map((fw: string) => (
                    <span key={fw} className="bg-secondary print:bg-gray-100 px-3 py-1 rounded-md text-sm font-medium">{fw}</span>
                  ))}
                  {!frameworks?.length && <span className="text-muted-foreground">None detected</span>}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Findings */}
        <div className="break-before-page">
          <h3 className="text-2xl font-bold mb-8 border-b border-border print:border-gray-200 pb-2">Detailed Vulnerabilities</h3>
          
          {findings.length === 0 ? (
            <div className="text-center p-12 bg-secondary/20 print:bg-gray-50 rounded-xl">
              <p className="text-lg font-medium text-green-500">No vulnerabilities detected.</p>
            </div>
          ) : (
            <div className="space-y-8">
              {findings.map((finding: any, idx: number) => (
                <Card key={idx} className="bg-background print:bg-white border-white/10 print:border-gray-300 print:shadow-none break-inside-avoid">
                  <CardHeader className="bg-secondary/20 print:bg-gray-50 border-b border-white/5 print:border-gray-200">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                            finding.severity === "CRITICAL" ? "bg-destructive/20 text-destructive print:text-red-700" :
                            finding.severity === "HIGH" ? "bg-yellow-500/20 text-yellow-500 print:text-yellow-700" :
                            finding.severity === "MEDIUM" ? "bg-orange-500/20 text-orange-500 print:text-orange-700" :
                            "bg-blue-500/20 text-blue-500 print:text-blue-700"
                          }`}>
                            {finding.severity}
                          </span>
                          <span className="text-xs font-mono text-muted-foreground print:text-gray-500 border border-border print:border-gray-300 px-2 py-0.5 rounded">
                            {finding.rule_id}
                          </span>
                        </div>
                        <CardTitle className="text-lg mt-2">{finding.title || `Vulnerability in ${finding.file_path}`}</CardTitle>
                      </div>
                      <div className="text-right text-sm">
                        <p className="font-mono">{finding.file_path}</p>
                        <p className="text-muted-foreground">Line {finding.line_number}</p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-6 space-y-6">
                    <div>
                      <h4 className="text-sm font-bold uppercase tracking-wider text-muted-foreground print:text-gray-500 mb-2">Description</h4>
                      <p className="leading-relaxed">{finding.description}</p>
                    </div>
                    
                    {finding.ai_explanation && (
                      <div className="bg-primary/5 print:bg-blue-50 border border-primary/20 print:border-blue-200 rounded-lg p-4">
                        <h4 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-primary print:text-blue-800 mb-2">
                          <SparklesIcon className="w-4 h-4" /> AI Analysis
                        </h4>
                        <div className="prose prose-sm dark:prose-invert print:prose-blue max-w-none">
                          <ReactMarkdown>{finding.ai_explanation.real_world_impact}</ReactMarkdown>
                        </div>
                        <div className="mt-4 pt-4 border-t border-primary/10 print:border-blue-100">
                          <p className="text-sm font-semibold mb-1">Recommendation:</p>
                          <div className="prose prose-sm dark:prose-invert print:prose-blue max-w-none">
                            <ReactMarkdown>{finding.ai_explanation.secure_coding_recommendation}</ReactMarkdown>
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SparklesIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
      <path d="M5 3v4" />
      <path d="M19 17v4" />
      <path d="M3 5h4" />
      <path d="M17 19h4" />
    </svg>
  );
}
