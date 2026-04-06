"use client";

import { Mermaid } from "@/components/ui/Mermaid";
import { CopyableCode } from "@/components/ui/CopyableCode";
import { Step } from "@/components/ui/Step";
import { Terminal } from "@/components/ui/Terminal";
import { DocsLayout } from "@/components/layout/DocsLayout";
import { Heading } from "@/components/ui/core";
import { Badge, Button } from "@/components/ui/shadcn";
import { CheckCircle2, Command, Zap, ChevronRight } from "lucide-react";
import Link from "next/link";
import { COMMANDS } from "@/lib/constants";
import { DIAGRAMS } from "@/lib/diagrams";

/**
 * User Guide page.
 */
export default function UserGuide() {
  return (
    <DocsLayout 
      title="User Guide" 
      description="Grit is a simple tool. Once you set it up, it stays out of your way and handles the math of your contribution graph automatically."
    >
      {/* 1. Quick Start */}
      <section className="mb-20 space-y-10">
        <header className="flex items-center justify-between">
          <Heading level={2} className="flex items-center gap-3">
            <CheckCircle2 className="text-primary w-6 h-6" /> 1. Quick Start
          </Heading>
          <Badge>Recommended</Badge>
        </header>
        <Step 
          num={1} 
          title="Install Grit" 
          desc="Use uv to install Grit as a global tool." 
          code={COMMANDS.INSTALL} 
        />
        <Step 
          num={2} 
          title="Configure Your Goals" 
          desc="Tell Grit your daily target and when to start tracking." 
          code={COMMANDS.CONFIG} 
        />
        <Step 
          num={3} 
          title="Make a Commit" 
          desc="Use it exactly like git. Grit takes care of the rest." 
          code={COMMANDS.COMMIT} 
        />
      </section>

      {/* 2. Self-Healing Sync */}
      <section className="mb-20 py-16 px-10 bg-card border border-border rounded-[2.5rem] space-y-8 relative overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[80px] -mr-32 -mt-32 rounded-full" />
        
        <Heading level={2} className="flex items-center gap-3">
          <Zap className="text-primary w-6 h-6" /> 2. Self-Healing Sync
        </Heading>
        <p className="text-muted-foreground leading-relaxed text-lg font-medium">
          If you commit from a different machine or merge a PR on GitHub, your local Grit state might fall behind. Running <code>grit sync</code> fixes this instantly.
        </p>
        <Mermaid chart={DIAGRAMS.SYNC} />
        <Terminal 
          title="grit sync demo"
          className="mt-12 shadow-none border-white/5 bg-white/[0.02] max-w-full"
          lines={[
            { text: "grit sync", type: "input", delay: 500, duration: 800 },
            { text: "Scanning local database...", type: "output", delay: 300 },
            { text: "Fetching remote history...", type: "output", delay: 400 },
            { text: "Found 2 discrepancies in March 2026", type: "warning", delay: 500 },
            { text: "Repairing state...", type: "output", delay: 300 },
            { text: "progress", type: "progress", delay: 200, duration: 1500 },
            { text: "✓ Local state is now in sync with GitHub.", type: "success", delay: 500 },
          ]}
        />
      </section>

      {/* 3. Commands */}
      <section className="mb-20 space-y-8">
        <Heading level={2} className="flex items-center gap-3">
          <Command className="text-primary w-6 h-6" /> 3. Command Reference
        </Heading>
        <div className="grid grid-cols-1 gap-4">
          <CommandCard cmd="grit dash" desc="Launch the high-fidelity web dashboard. Use --stop to terminate the background process." />
          <CommandCard cmd="grit log" desc="A beautifully enhanced, human-readable git log on jetpack rollerskates." />
          <CommandCard cmd="grit status" desc="Check your progress and see where your next commit will land." />
          <CommandCard cmd="grit sync" desc="Align your local database with your real git history." />
          <CommandCard cmd="grit ungrit" desc="Remove all configuration and state from your machine." />
        </div>
      </section>

      <footer className="mt-20 pt-12 border-t border-border flex justify-end">
        <Link href="/docs/developer-guide">
          <Button size="lg" className="group h-auto py-6 px-10 rounded-[2rem]">
            <div className="text-right mr-6">
              <p className="text-[10px] uppercase font-black tracking-[0.2em] opacity-50 mb-1">Architecture</p>
              <Heading level={4} className="text-xl">Developer Guide</Heading>
            </div>
            <ChevronRight className="w-8 h-8 transition-transform group-hover:translate-x-2" />
          </Button>
        </Link>
      </footer>
    </DocsLayout>
  );
}

function CommandCard({ cmd, desc }: { cmd: string; desc: string }) {
  return (
    <div className="p-6 rounded-2xl bg-card border border-border flex flex-col sm:flex-row sm:items-center gap-6 group hover:border-primary/30 transition-all hover:translate-x-1">
      <code className="text-primary font-bold text-base shrink-0 bg-primary/5 px-3 py-1 rounded-lg border border-primary/10">{cmd}</code>
      <p className="text-muted-foreground text-sm leading-relaxed font-medium">{desc}</p>
    </div>
  );
}
