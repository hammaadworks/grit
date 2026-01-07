"use client";

import * as React from "react";
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { cn as cn_import } from "@/lib/utils"; // Import cn from utils

/**
 * High-performance Tailwind class merger.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Standardized Section container following SOLID layout principles.
 */
export function Section({ 
  children, 
  className, 
  id 
}: { 
  children: React.ReactNode; 
  className?: string; 
  id?: string 
}) {
  return (
    <section 
      id={id} 
      className={cn_import("py-24 px-6 max-w-5xl mx-auto relative", className)}
    >
      {children}
    </section>
  );
}

/**
 * Semantic Heading component with variant-based styling.
 */
export function Heading({ 
  children, 
  className, 
  level = 2 
}: { 
  children: React.ReactNode; 
  className?: string; 
  level?: 1 | 2 | 3 | 4 
}) {
  const Tag = `h${level}` as const;
  const styles = {
    1: "text-5xl sm:text-7xl font-extrabold tracking-tight leading-[1.1]",
    2: "text-4xl font-bold tracking-tight",
    3: "text-2xl font-bold tracking-tight",
    4: "text-xl font-bold",
  };

  return (
    <Tag className={cn_import(styles[level], className)}>
      {children}
    </Tag>
  );
}

/**
 * Composable Card primitive for feature and content containers.
 */
export function Card({ 
  children, 
  className 
}: { 
  children: React.ReactNode; 
  className?: string 
}) {
  return (
    <div className={cn_import(
      "bg-card border border-border rounded-[2rem] p-8 shadow-sm overflow-hidden", 
      className
    )}>
      {children}
    </div>
  );
}
