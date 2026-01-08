"use client";

import { Mermaid } from "@/components/ui/Mermaid";
import { CopyableCode } from "@/components/ui/CopyableCode";
import { Step } from "@/components/ui/Step";
import { Terminal } from "@/components/ui/Terminal";
import { DocsLayout } from "@/components/layout/DocsLayout";
import { Heading, Card } from "@/components/ui/core";
import { Button, Badge } from "@/components/ui/shadcn";
import { Code2, Cpu, Database, Layers, ArrowRight, ChevronRight } from "lucide-react";
import Link from "next/link";
import { SITE_CONFIG } from "@/lib/constants";
import { DIAGRAMS } from "@/lib/diagrams";

/**
 * Developer and Architecture Guide.
 * Synchronized with wiki/diagrams/ source of truth.
 */
export default function DeveloperGuide() {
  return (
    <DocsLayout 
      title="Developer Guide" 
      description="Grit is built with Python, Typer, and SQLite. It's designed to be fast, reliable, and easy to maintain."
      backHref="/docs/user-guide"
      backLabel="Back to User Guide"
    >
      {/* AI-First Section */}
      <section className="mb-24 space-y-8">
        <header className="flex items-center justify-between">
          <Heading level={2} className="flex items-center gap-3">
            <Cpu className="text-primary w-6 h-6" /> AI-First Development
          </Heading>
          <Badge>Advanced</Badge>
        </header>
        <Card className="space-y-8 p-10 bg-gradient-to-br from-card to-background border-primary/10 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 blur-3xl -mr-16 -mt-16 rounded-full" />
          <p className="text-muted-foreground leading-relaxed text-lg">
            Grit maintainers use a high-density technical snapshot in <code>docs/llms.md</code> to bootstrap AI agents with perfect context.
          </p>
          <div className="flex flex-col sm:flex-row gap-6">
            <a 
              href={`${SITE_CONFIG.repo_url}/blob/main/docs/llms.md`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button className="group px-8">
                View on GitHub <ArrowRight className="ml-2 w-4 h-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </a>
          </div>
        </Card>
      </section>

      {/* Local Setup */}
      <section className="mb-24 space-y-12">
        <Heading level={2} className="flex items-center gap-3">
          <Code2 className="text-primary w-6 h-6" /> Local Setup
        </Heading>
        <div className="space-y-12">
          <Step 
            num={1} 
            title="Clone and Install" 
            desc="Setup the Rust-powered Python environment." 
            code={`git clone ${SITE_CONFIG.repo_url} && cd grit && uv sync`} 
          />
          <Step 
            num={2} 
            title="Run Local Code" 
            desc="Test the CLI logic directly from source." 
            code="uv run grit status" 
          />
          <Step 
            num={3} 
            title="Run Tests" 
            desc="Maintain the 'Iron Rule': 100% logic coverage." 
            code="uv run pytest tests/" 
          />
        </div>
        <Terminal 
          title="pytest runner"
          className="mt-12 shadow-none border-white/5 bg-white/[0.02] max-w-full"
          lines={[
            { text: "uv run pytest tests/", type: "input", delay: 500, duration: 800 },
            { text: "collecting ... collected 18 items", type: "output", delay: 300 },
            { text: "tests/test_allocator.py ....", type: "output", delay: 400 },
            { text: "tests/test_cli.py ...", type: "output", delay: 200 },
            { text: "tests/test_executor.py ..", type: "output", delay: 200 },
            { text: "tests/test_state.py ...", type: "output", delay: 200 },
            { text: "tests/test_sync.py ....", type: "output", delay: 200 },
            { text: "✓ 18 passed in 1.42s", type: "success", delay: 500 },
            { text: "Logic coverage: 100% (Iron Rule satisfied)", type: "output", delay: 400 },
          ]}
        />
      </section>

      {/* Architecture */}
      <section className="mb-24 space-y-10">
        <Heading level={2} className="flex items-center gap-3">
          <Layers className="text-primary w-6 h-6" /> Core Logic
        </Heading>
        <p className="text-muted-foreground leading-relaxed text-lg">
          Grit offloads date discovery to SQLite via a Recursive CTE. This architecture ensures O(1) performance regardless of graph density.
        </p>
        <div className="group">
          <Mermaid chart={DIAGRAMS.ALLOCATOR} />
          <p className="text-center text-[10px] font-mono text-white/20 uppercase tracking-[0.2em] mt-4 group-hover:text-primary transition-colors">
            Architecture: allocator.mmd
          </p>
        </div>
      </section>

      {/* Project Map */}
      <section className="mb-24 space-y-10">
        <Heading level={2} className="flex items-center gap-3">
          <Database className="text-primary w-6 h-6" /> Project Map
        </Heading>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <MapItem path="src/grit/cli.py" desc="Entry point. Rich rendering and user interaction." />
          <MapItem path="src/grit/allocator.py" desc="The date discovery engine (SQL CTE)." />
          <MapItem path="src/grit/state.py" desc="Atomic SQLite wrapper and state management." />
          <MapItem path="src/grit/sync.py" desc="Self-healing logic and GitHub scraper." />
        </div>
      </section>

      <footer className="mt-20 pt-12 border-t border-border flex justify-center">
        <Link href="/">
          <Button variant="outline" size="lg" className="rounded-2xl group border-white/5 hover:border-primary/50">
            Return Home <ChevronRight className="w-6 h-6 ml-2 transition-transform group-hover:translate-x-1" />
          </Button>
        </Link>
      </footer>
    </DocsLayout>
  );
}

function MapItem({ path, desc }: { path: string; desc: string }) {
  return (
    <div className="p-6 rounded-2xl bg-card border border-border group hover:border-primary/20 transition-all hover:scale-[1.02]">
      <code className="text-primary text-sm font-black block mb-2">{path}</code>
      <p className="text-muted-foreground text-xs leading-relaxed font-medium">{desc}</p>
    </div>
  );
}
