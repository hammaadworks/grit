"use client";

import { motion } from "framer-motion";
import { Terminal } from "@/components/Terminal";
import { Code2, Terminal as TermIcon, Shield, Zap } from "lucide-react";
import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-background relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-accent/5 blur-[120px] pointer-events-none" />

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6 sm:px-12 lg:px-24 max-w-7xl mx-auto flex flex-col items-center text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium mb-8 border border-primary/20"
        >
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          v0.1.0 is now live
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-foreground mb-6"
        >
          Your GitHub graph, <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">
            perfectly consistent.
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-lg sm:text-xl text-muted-foreground max-w-2xl mb-10"
        >
          Grit is an intelligent CLI wrapper that mathematically distributes your commits to hit daily targets—without rewriting true repository history.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="flex flex-col sm:flex-row gap-4 w-full justify-center"
        >
          <div className="flex items-center bg-[#1A1A1A] border border-border rounded-lg pl-4 pr-1 py-1 group hover:border-primary/50 transition-colors">
            <code className="text-white font-mono text-sm mr-4">uv tool install grit</code>
            <button 
              onClick={() => navigator.clipboard.writeText('uv tool install grit')}
              className="p-2 hover:bg-white/10 rounded-md text-white/50 hover:text-white transition-colors"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            </button>
          </div>
          <Link href="#docs" className="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors">
            Read the Docs
          </Link>
        </motion.div>

        <Terminal />
      </section>

      {/* Features Grid */}
      <section className="py-24 bg-card/50 border-y border-border px-6 sm:px-12 lg:px-24">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard 
              icon={<Zap className="w-6 h-6 text-accent" />}
              title="O(1) SQLite Allocator"
              description="Calculates the optimal commit date instantly using recursive SQL. No Python loops. Concurrency safe."
            />
            <FeatureCard 
              icon={<Shield className="w-6 h-6 text-primary" />}
              title="Self-Healing Sync"
              description="Automatically scrapes your public GitHub graph and local git log to ensure it never overwrites a day you already committed to."
            />
            <FeatureCard 
              icon={<TermIcon className="w-6 h-6 text-secondary" />}
              title="Frictionless Passthrough"
              description="Passes every argument exactly as-is to vanilla Git. Want to bypass hooks? Use --no-verify. It just works."
            />
          </div>
        </div>
      </section>

      {/* Quick Docs / Getting Started Section */}
      <section id="docs" className="py-24 px-6 sm:px-12 lg:px-24 max-w-4xl mx-auto">
        <h2 className="text-3xl font-bold mb-12 text-center">Developer Guide</h2>
        
        <div className="space-y-12">
          <DocSection title="1. Global Installation" code="uv tool install grit" />
          <DocSection title="2. Setup Wizard" code="grit config" description="Sets your daily target and syncs your existing GitHub activity." />
          <DocSection title="3. Start Committing" code="grit commit -m 'Initial commit'" description="Use it exactly like Git. Grit handles the environment variables." />
          
          <div className="mt-12 p-6 rounded-xl bg-card border border-border">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Code2 className="w-5 h-5" /> Local Development
            </h3>
            <p className="text-muted-foreground mb-4">Want to contribute to the code? Setup takes 2 minutes.</p>
            <pre className="p-4 bg-[#0A0A0A] rounded-lg text-sm text-white/80 font-mono overflow-x-auto">
              {`git clone https://github.com/your-org/grit.git
cd grit
uv sync
uv run pytest tests/ -v
uv run grit config`}
            </pre>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 text-center text-muted-foreground border-t border-border">
        <p>Built with precision. <a href="#" className="hover:text-primary transition-colors">View on GitHub</a></p>
      </footer>
    </main>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className="p-6 rounded-2xl bg-card border border-border hover:border-primary/30 transition-colors group"
    >
      <div className="w-12 h-12 rounded-lg bg-background border border-border flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="text-xl font-bold mb-3">{title}</h3>
      <p className="text-muted-foreground leading-relaxed">{description}</p>
    </motion.div>
  );
}

function DocSection({ title, code, description }: { title: string, code: string, description?: string }) {
  return (
    <div className="group">
      <h3 className="text-lg font-semibold mb-3 text-foreground">{title}</h3>
      {description && <p className="text-muted-foreground mb-3 text-sm">{description}</p>}
      <div className="relative">
        <div className="absolute inset-0 bg-primary/5 rounded-lg blur opacity-0 group-hover:opacity-100 transition-opacity" />
        <pre className="relative p-4 bg-[#0A0A0A] border border-border rounded-lg text-sm text-white/80 font-mono">
          <span className="text-primary mr-2">$</span>{code}
        </pre>
      </div>
    </div>
  );
}
