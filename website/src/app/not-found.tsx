"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Terminal, Home, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/shadcn";
import { Section } from "@/components/ui/core";
import { cn } from "@/lib/utils";

export default function NotFound() {
  const [path, setPath] = useState("this-page");

  useEffect(() => {
    setPath(window.location.pathname);
  }, []);

  return (
    <Section className="relative min-h-[80vh] flex flex-col items-center justify-center text-center overflow-hidden">
      {/* Background glowing effects */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-[600px] h-[400px] bg-primary/10 blur-[120px] pointer-events-none rounded-full" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[50%] bg-gradient-to-b from-primary/5 to-transparent blur-3xl opacity-30" />

      {/* Grid Pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(#ffffff05_1px,transparent_1px)] [background-size:24px_24px] pointer-events-none opacity-50" />

      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 flex flex-col items-center max-w-2xl px-4"
      >
        <div className="w-20 h-20 rounded-3xl bg-black/50 border border-white/10 flex items-center justify-center mb-8 shadow-2xl overflow-hidden relative group">
          <div className="absolute inset-0 bg-primary/20 blur-xl group-hover:bg-primary/30 transition-colors" />
          <Terminal className="text-primary w-10 h-10 relative z-10" />
        </div>

        <h1 className="text-7xl sm:text-9xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-white to-white/30 mb-4 select-none drop-shadow-sm">
          404
        </h1>

        <div className="bg-red-500/10 border border-red-500/20 text-red-400 font-mono text-sm px-4 py-2 rounded-md mb-8 shadow-inner shadow-red-500/5">
          <span className="font-bold">fatal:</span> pathspec &apos;{path}&apos; did not match any files
        </div>

        <h2 className="text-2xl sm:text-3xl font-bold mb-4 text-white/90">
          Looks like you pushed to the void.
        </h2>
        
        <p className="text-lg text-muted-foreground mb-10 leading-relaxed max-w-lg">
          Not even <span className="font-bold text-primary">Grit</span> can backfill this gap in your streak. The page you&apos;re looking for has been squashed, rebased out of existence, or never existed at all.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto justify-center">
          <Link href="/">
            <Button size="lg" className="w-full sm:w-auto group">
              <Terminal className="mr-2 w-4 h-4" /> 
              git checkout main
            </Button>
          </Link>
          <Button 
            onClick={() => window.history.back()} 
            size="lg" 
            variant="outline" 
            className="w-full sm:w-auto group"
          >
            <ArrowLeft className="mr-2 w-4 h-4 transition-transform group-hover:-translate-x-1" />
            Go Back
          </Button>
        </div>
      </motion.div>
    </Section>
  );
}