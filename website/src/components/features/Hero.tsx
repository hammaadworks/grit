"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Code2, Star, Download } from "lucide-react";
import { Heading, Section } from "../ui/core";
import { Button, Badge } from "../ui/shadcn";
import { CopyableCode } from "../ui/CopyableCode";
import { Terminal } from "../ui/Terminal";
import { COMMANDS, SITE_CONFIG } from "@/lib/constants";
import { cn } from "@/lib/utils";

/**
 * High-end Hero section with 21st-dev visual patterns and transparent navigation.
 */
export function Hero() {
  return (
    <Section className="relative pt-32 pb-20 flex flex-col items-center text-center overflow-visible">
      {/* 21st-Dev Spotlight Effect */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[600px] bg-primary/5 blur-[120px] pointer-events-none rounded-full" />
      <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[120%] h-[40%] bg-gradient-to-b from-primary/10 to-transparent blur-3xl opacity-50" />

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Badge className="mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-primary mr-2 animate-pulse" />
          Production v{SITE_CONFIG.version}
        </Badge>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Heading level={1} className="mb-8 max-w-4xl mx-auto leading-tight">
          Your GitHub streak? <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-teal-400 to-emerald-400">
            Consider it unbreakable.
          </span>
        </Heading>
      </motion.div>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="text-lg sm:text-xl text-muted-foreground max-w-3xl mb-12 leading-relaxed font-medium"
      >
        Grit is a professional, high-fidelity git wrapper that intelligently distributes your commits to maintain a consistent contribution graph. Featuring <strong>CommitScribe AI</strong>, we generate architectural, CTO-level commit messages while keeping your daily goals perfectly on track.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="flex flex-col sm:flex-row gap-4 w-full justify-center mb-20 relative z-10"
      >
        <CopyableCode code={COMMANDS.INSTALL} label="$" className={cn("w-full sm:w-[340px] shadow-2xl shadow-primary/10", "border-white/5")} />
        <div className="flex gap-3">
          <Link href={SITE_CONFIG.docs.user} className="flex-1 sm:flex-none">
            <Button size="lg" className="w-full group">
              Get Started <ArrowRight className="ml-2 w-5 h-5 transition-transform group-hover:translate-x-1" />
            </Button>
          </Link>
          <a href={SITE_CONFIG.releases_url} target="_blank" rel="noopener noreferrer" className="flex-1 sm:flex-none">
            <Button size="lg" variant="outline" className="w-full group border-primary/20 hover:border-primary/50">
              <Download className="mr-2 w-5 h-5 transition-transform group-hover:-translate-y-1" />
              Download
            </Button>
          </a>
          <a href={SITE_CONFIG.repo_url} target="_blank" rel="noopener noreferrer" className="hidden sm:block">
            <Button size="lg" variant="ghost" className="group">
              <Star className="mr-2 w-5 h-5 text-yellow-500 fill-yellow-500" />
              Star
            </Button>
          </a>
        </div>
      </motion.div>

      <Terminal />
    </Section>
  );
}
