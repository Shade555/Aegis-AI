"use client";

import { useState, useRef, useEffect } from "react";
import { Bot, X, Send, Sparkles, Loader2, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import * as motion from "framer-motion/client";
import ReactMarkdown from "react-markdown";

const SUGGESTED_QUESTIONS = [
  "Explain the most critical finding.",
  "How do I fix the SQL injection?",
  "What is the overall threat posture?"
];

// Typewriter effect component for streaming simulation
function TypewriterMessage({ content }: { content: string }) {
  const [displayed, setDisplayed] = useState("");
  
  useEffect(() => {
    let i = 0;
    setDisplayed("");
    const interval = setInterval(() => {
      setDisplayed((prev) => prev + content.charAt(i));
      i++;
      if (i >= content.length) clearInterval(interval);
    }, 15); // ms per character
    return () => clearInterval(interval);
  }, [content]);

  return <ReactMarkdown>{displayed}</ReactMarkdown>;
}

export function AIAssistantPanel({ executionId, status }: { executionId: string; status: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string; streamed?: boolean }[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, isOpen]); // Also scroll when opened

  const handleSend = async (text: string = input) => {
    if (!text.trim() || isLoading) return;

    const userMessage = text.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch(`/api/executions/${executionId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!response.ok) throw new Error("Failed to chat");

      const data = await response.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply, streamed: true }]);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I am unable to connect to the AI service right now." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (status !== "COMPLETED") return null;

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="fixed bottom-6 right-6 z-50"
        >
          <Button
            size="icon"
            className="h-16 w-16 rounded-full shadow-[0_0_20px_rgba(var(--primary),0.5)] bg-gradient-to-tr from-primary to-blue-500 hover:scale-105 transition-all text-white border-2 border-white/20"
            onClick={() => setIsOpen(true)}
          >
            <Sparkles className="h-7 w-7" />
          </Button>
        </motion.div>
      )}

      {/* Chat Panel */}
      {isOpen && (
        <motion.div
          initial={{ y: 50, opacity: 0, scale: 0.95 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          className="fixed bottom-6 right-6 z-50 w-[350px] md:w-[450px]"
        >
          <Card className="shadow-2xl border-primary/30 glass-card bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60 overflow-hidden flex flex-col h-[600px]">
            {/* Header */}
            <CardHeader className="p-4 border-b border-white/10 bg-gradient-to-r from-primary/10 to-transparent flex flex-row items-center justify-between space-y-0 relative">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary via-blue-500 to-purple-500" />
              <CardTitle className="text-md font-bold flex items-center gap-2 text-primary tracking-wide">
                <Bot className="h-5 w-5 text-blue-400" /> Aegis AI Intelligence
              </CardTitle>
              <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-white/10 rounded-full" onClick={() => setIsOpen(false)}>
                <X className="h-5 w-5" />
              </Button>
            </CardHeader>
            
            {/* Message Area */}
            <CardContent className="p-4 flex-1 overflow-y-auto flex flex-col gap-4 relative">
              {messages.length === 0 && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center mt-8 text-sm flex flex-col items-center justify-center h-full">
                  <div className="h-20 w-20 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 border border-primary/20 shadow-[0_0_30px_rgba(var(--primary),0.15)]">
                    <Sparkles className="h-10 w-10 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">How can I assist?</h3>
                  <p className="text-muted-foreground max-w-[250px] mb-8">
                    Ask me anything about the vulnerabilities or patches in this report.
                  </p>
                  <div className="flex flex-col gap-2 w-full">
                    {SUGGESTED_QUESTIONS.map((q, i) => (
                      <button
                        key={i}
                        onClick={() => handleSend(q)}
                        className="text-left px-4 py-2.5 rounded-lg border border-white/5 bg-secondary/30 hover:bg-secondary/70 hover:border-primary/30 transition-all text-xs flex items-center gap-2 text-muted-foreground hover:text-foreground"
                      >
                        <Zap className="h-3 w-3 text-yellow-500" /> {q}
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}
              {messages.map((msg, i) => (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  key={i}
                  className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl p-4 text-sm shadow-sm ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground rounded-tr-sm"
                        : "bg-secondary/50 border border-white/5 text-foreground rounded-tl-sm"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed">
                        {msg.streamed && i === messages.length - 1 ? (
                          <TypewriterMessage content={msg.content} />
                        ) : (
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        )}
                      </div>
                    ) : (
                      msg.content
                    )}
                  </div>
                </motion.div>
              ))}
              {isLoading && (
                <div className="flex w-full justify-start">
                  <div className="bg-secondary/50 border border-white/5 text-foreground rounded-2xl rounded-tl-sm p-4 flex items-center gap-2">
                    <span className="flex gap-1">
                      <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1.2 }} className="w-1.5 h-1.5 bg-primary rounded-full block" />
                      <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1.2, delay: 0.2 }} className="w-1.5 h-1.5 bg-primary rounded-full block" />
                      <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1.2, delay: 0.4 }} className="w-1.5 h-1.5 bg-primary rounded-full block" />
                    </span>
                    <span className="text-xs text-muted-foreground font-medium ml-2 tracking-wide">THINKING</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} className="h-1" />
            </CardContent>
            
            {/* Input Footer */}
            <CardFooter className="p-4 border-t border-white/10 bg-background/50 backdrop-blur-md">
              <div className="flex w-full items-center gap-2 relative">
                <Input
                  placeholder="Ask a question..."
                  className="flex-1 bg-secondary/50 border-white/10 rounded-full pl-4 pr-12 h-12 focus-visible:ring-primary/50"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
                <Button 
                  size="icon" 
                  className="absolute right-1.5 top-1.5 h-9 w-9 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground transition-all"
                  onClick={() => handleSend()} 
                  disabled={!input.trim() || isLoading}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </CardFooter>
          </Card>
        </motion.div>
      )}
    </>
  );
}
