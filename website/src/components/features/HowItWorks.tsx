"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Database, GitBranch, Cpu } from "lucide-react";
import { Mermaid } from "../ui/Mermaid";
import { Section, Heading } from "../ui/core";
import { cn } from "@/lib/utils"; // Corrected import for cn
import { DIAGRAMS } from "@/lib/diagrams";

const STEPS = [
  {
    title: "DevX Wizard",
    description: "Launch an interactive TUI to pick files and let AI auto-generate your Conventional Commits.",
    icon: GitBranch,
    color: "text-blue-400"
  },
  {
    title: "O(1) Allocation",
    description: "A single Recursive SQL query finds the most recent open date matching your target to fix streaks.",
    icon: Database,
    color: "text-teal-400"
  },
  {
    title: "Quantum Undo",
    description: "Made a mistake? Safely reset your work and automatically decrement the database count.",
    icon: Cpu,
    color: "text-purple-400"
  },
  {
    title: "Smart Push",
    description: "Grit prompts you to push, detects rejections, and handles automatic pull-rebasing.",
    icon: CheckCircle2,
    color: "text-green-400"
  }
] as const;

/**
 * Technical explanation section with process steps and sequence diagram.
 * Uses shared diagram definitions from wiki/diagrams store.
 */
export function HowItWorks() {
  return (
    <Section className="max-w-7xl">
      <div className="text-center mb-16">
        <Heading level={2} className="mb-4">How Grit Works</Heading>
        <p className="text-muted-foreground max-w-2xl mx-auto text-lg font-medium">
          A zero-latency wrapper built on robust systems engineering.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        <div className="space-y-6">
          {STEPS.map((step, index) => (
            <motion.div 
              key={step.title}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.5 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={cn("flex gap-6 p-6 rounded-2xl bg-card border border-border hover:border-primary/30 transition-all group shadow-sm")}
            >
              <div className={cn(
                "mt-1 flex-shrink-0 w-12 h-12 rounded-xl bg-background border border-border flex items-center justify-center transition-transform group-hover:scale-110",
                step.color
              )}>
                <step.icon className="w-6 h-6" />
              </div>
              <div>
                <Heading level={4} className="mb-1">{step.title}</Heading>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="relative">
          <div className="absolute -inset-4 bg-primary/10 blur-3xl rounded-full opacity-50" />
          <div className="relative group">
            <Mermaid chart={DIAGRAMS.ALLOCATOR} />
            <p className="mt-4 text-center text-[10px] font-mono text-white/20 uppercase tracking-[0.2em] group-hover:text-primary transition-colors">
              Internal Logic: allocator.mmd
            </p>
          </div>
        </div>
      </div>
    </Section>
  );
}
