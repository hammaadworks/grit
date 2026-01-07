"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { motion } from "framer-motion";
import { Heading, Section } from "../ui/core";
import { cn } from "@/lib/utils"; // Corrected import for cn

interface DocsLayoutProps {
  children: React.ReactNode;
  title: string;
  description: string;
  backHref?: string;
  backLabel?: string;
}

/**
 * Standardized layout for documentation pages.
 */
export function DocsLayout({ children, title, description, backHref = "/", backLabel = "Back to Home" }: DocsLayoutProps) {
  return (
    <main className="min-h-screen bg-background text-foreground py-20 px-6 sm:px-12 lg:px-24 selection:bg-primary/20 pt-32"> {/* Added pt-32 for fixed header */}
      <div className="max-w-4xl mx-auto">
        <Link href={backHref} className={cn("inline-flex items-center text-primary hover:text-primary/80 transition-colors mb-8 group")}>
          <ArrowLeft className={cn("w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform")} /> {backLabel}
        </Link>
        
        <motion.header 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <Heading level={1} className={cn("text-4xl sm:text-5xl mb-6")}>{title}</Heading>
          <p className={cn("text-xl text-muted-foreground leading-relaxed")}>
            {description}
          </p>
        </motion.header>

        {children}
      </div>
    </main>
  );
}
