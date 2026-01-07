"use client";

import React, { useEffect, useRef, useState, useId } from "react";
import mermaid from "mermaid";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils"; // Corrected import for cn

// Initialize mermaid with the brand theme.
mermaid.initialize({
  startOnLoad: true,
  theme: "base",
  themeVariables: {
    primaryColor: '#0A0A0A',
    primaryTextColor: '#fff',
    primaryBorderColor: '#14b8a6',
    lineColor: '#14b8a6',
    secondaryColor: '#1A1A1A',
    tertiaryColor: '#1A1A1A',
    fontFamily: 'Inter',
    background: '#0A0A0A',
  },
});

interface MermaidProps {
  /** The mermaid diagram definition string. */
  chart: string;
  /** Optional additional classes. */
  className?: string;
}

/**
 * Optimized Mermaid diagram renderer with Framer Motion integration.
 */
export function Mermaid({ chart, className }: MermaidProps) {
  const [svg, setSvg] = useState<string>("");
  const containerRef = useRef<HTMLDivElement>(null);
  const chartId = useId().replace(/:/g, ""); // Mermaid IDs must be alphanumeric

  useEffect(() => {
    const renderChart = async () => {
      if (!containerRef.current) return;
      try {
        const { svg: renderedSvg } = await mermaid.render(`mermaid-${chartId}`, chart);
        setSvg(renderedSvg);
      } catch (err) {
        console.error("Mermaid parsing error:", err);
      }
    };
    renderChart();
  }, [chart, chartId]);

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.98 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      className={cn(
        "my-8 p-6 rounded-2xl border border-border bg-black/40 shadow-xl overflow-x-auto flex justify-center",
        className
      )}
      ref={containerRef}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
