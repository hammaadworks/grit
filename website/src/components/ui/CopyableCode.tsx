"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils"; // Corrected import path for cn

interface CopyableCodeProps {
  /** The code string to be displayed and copied. */
  code: string;
  /** Optional container classes. */
  className?: string;
  /** Optional label prefix (e.g. '$'). */
  label?: string;
}

/**
 * A reusable, copy-to-clipboard code snippet component.
 */
export function CopyableCode({ code, className, label }: CopyableCodeProps) {
  const [copied, setCopied] = useState(false);

  /**
   * Handles the copy interaction with a temporary success state.
   */
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  return (
    <div className={cn(
      "group relative flex items-center bg-white/[0.03] hover:bg-white/[0.05] border border-white/10 rounded-xl transition-all",
      className
    )}>
      <div className="flex-1 flex items-center px-4 py-3 font-mono text-sm overflow-hidden">
        {label && <span className="text-primary/50 mr-2 shrink-0 select-none">{label}</span>}
        <code className="text-white/90 truncate">{code}</code>
      </div>
      <button
        onClick={handleCopy}
        className="px-4 py-3 border-l border-white/10 hover:bg-white/5 transition-colors text-muted-foreground hover:text-primary flex items-center justify-center active:scale-95"
        aria-label="Copy to clipboard"
      >
        {copied ? (
          <Check className="w-4 h-4 text-primary animate-in zoom-in duration-200" />
        ) : (
          <Copy className="w-4 h-4 transition-transform group-hover:scale-110" />
        )}
      </button>
    </div>
  );
}
