"use client";

import { Cpu, Terminal as Github, FileText, ArrowRight, Star, Copy, Check } from "lucide-react";
import Link from "next/link";
import { Heading, Section } from "../ui/core";
import { Button } from "../ui/shadcn";
import { SITE_CONFIG } from "@/lib/constants";
import { useState } from "react";
import { LLMS_MD_CONTENT } from "@/lib/llms-md-content"; // Importing the content
import { cn } from "@/lib/utils"; // Corrected import for cn

/**
 * Explains the AI-Native / Context-Sharing feature of Grit.
 * Includes a "Star on GitHub" call-to-action and interactive LLMS.md access.
 */
export function AINative() {
  const [copied, setCopied] = useState(false);

  const handleCopyLLMS = async () => {
    // In a real scenario, we'd fetch the actual file content. 
    // For now, we provide the core bootstrapping prompt.
    const bootstrapPrompt = `Please read the Grit project context from: ${SITE_CONFIG.docs.llms}\nThis file contains the technical invariants and architecture for the project.`;
    await navigator.clipboard.writeText(LLMS_MD_CONTENT);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Section className="py-32 border-y border-white/5 bg-white/[0.01] relative max-w-none">
      <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(#ffffff05_1px,transparent_1px)] [background-size:20px_20px] pointer-events-none" />
      
      <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
        <div>
          <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-8 shadow-inner">
            <Cpu className="text-primary w-7 h-7" />
          </div>
          <Heading level={2} className="mb-6">AI-Native Context</Heading>
          <p className="text-lg text-muted-foreground mb-8 leading-relaxed">
            Grit is built for the agentic era. We maintain a high-density technical snapshot designed to bootstrap any AI agent with perfect context in seconds.
          </p>
          
          <div className="space-y-6 mb-10">
            <FeatureItem title="Zero Hallucination" desc="Technical invariants ensure AI-generated code follows our SQLite-first rules." />
            <FeatureItem title="Instant Bootstrapping" desc="Copy the LLM context directly from here or link to the raw file." />
          </div>

          <div className="flex flex-wrap gap-4">
            <Button onClick={handleCopyLLMS} variant="primary" className="group">
              {copied ? (
                <>
                  <Check className="mr-2 w-4 h-4" /> Content Copied!
                </>
              ) : (
                <>
                  <Copy className="mr-2 w-4 h-4" /> Copy LLMS.md Content
                </>
              )}
            </Button>
            <a href={SITE_CONFIG.repo_url} target="_blank" rel="noopener noreferrer">
              <Button variant="outline" className="group">
                <Star className="mr-2 w-4 h-4 text-yellow-500 fill-yellow-500 group-hover:scale-110 transition-transform" />
                Star on GitHub
              </Button>
            </a>
          </div>
        </div>

        <div className="relative group">
          <div className="absolute -inset-4 bg-primary/20 blur-3xl opacity-20 rounded-full group-hover:opacity-30 transition-opacity" />
          <div className="relative bg-black border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
            <header className="flex items-center px-4 py-3 bg-white/5 border-b border-white/10 gap-2">
              <div className="w-2 h-2 rounded-full bg-red-500/50" />
              <div className="w-2 h-2 rounded-full bg-yellow-500/50" />
              <div className="w-2 h-2 rounded-full bg-green-500/50" />
              <span className="text-[10px] font-mono text-white/30 ml-2 select-none uppercase tracking-widest">llms.md</span>
            </header>
            <div className="p-6 font-mono text-[12px] leading-relaxed text-primary/80 h-[300px] overflow-auto">
              {LLMS_MD_CONTENT.split('\n').map((line, index) => (
                <pre key={index}>{line}</pre>
              ))}
            </div>
            <Link 
              href={SITE_CONFIG.docs.llms}
              target="_blank"
              className="absolute bottom-4 right-4 text-[10px] font-bold text-primary hover:underline flex items-center gap-1 bg-black/80 px-2 py-1 rounded"
            >
              View Full Source <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>
    </Section>
  );
}

function FeatureItem({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="flex gap-4">
      <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0" />
      <div>
        <Heading level={4} className="text-sm font-bold">{title}</Heading>
        <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}
