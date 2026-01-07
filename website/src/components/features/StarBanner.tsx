"use client";

import { Heart, Star } from "lucide-react";
import Link from "next/link";
import { Button } from "../ui/shadcn";
import { SITE_CONFIG } from "@/lib/constants";
import { cn } from "../ui/core";
import { motion } from "framer-motion";

/**
 * A prominent banner encouraging users to star the GitHub repository.
 */
export function StarBanner({ className }: { className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.8, delay: 0.2 }}
      className={cn(
        "py-16 px-6 text-center bg-card/50 border-y border-white/5 relative overflow-hidden",
        className
      )}
    >
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[300px] h-[300px] bg-yellow-400/5 blur-[100px] rounded-full pointer-events-none" />

      <div className="max-w-3xl mx-auto space-y-8 relative z-10">
        <Heart className="w-12 h-12 text-rose-500 mx-auto animate-pulse drop-shadow-lg" />
        <h2 className="text-4xl font-bold tracking-tight">Support Grit's Mission</h2>
        <p className="text-lg text-muted-foreground leading-relaxed font-medium">
          Grit is built for developers like you, completely open-source and free. If it brings you joy and peace of mind, please show your support by starring our repository on GitHub!
        </p>
        <a href={SITE_CONFIG.repo_url} target="_blank" rel="noopener noreferrer" className="inline-block">
          <Button size="lg" className="px-10 group bg-primary hover:scale-105 transition-transform duration-300">
            <Star className="mr-2 w-5 h-5 fill-yellow-500 text-yellow-500 drop-shadow-md" /> Star on GitHub
          </Button>
        </a>
      </div>
    </motion.div>
  );
}
