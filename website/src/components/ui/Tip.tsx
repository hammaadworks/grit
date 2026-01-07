"use client";

import { Star } from "lucide-react";
import { Heading } from "./core";
import { cn } from "@/lib/utils"; // Corrected import for cn

interface TipProps {
  title: string;
  children: React.ReactNode;
}

/**
 * Callout component for tips and important notices.
 */
export function Tip({ title, children }: TipProps) {
  return (
    <aside className={cn("p-6 rounded-2xl bg-card border border-border shadow-sm group hover:border-primary/20 transition-colors")}>
      <header className="flex items-center gap-2 mb-2">
        <Star className={cn("w-4 h-4 text-primary fill-primary group-hover:scale-110 transition-transform")} />
        <Heading level={4} className="text-sm uppercase tracking-wider">{title}</Heading>
      </header>
      <div className="text-sm text-muted-foreground leading-relaxed">
        {children}
      </div>
    </aside>
  );
}
