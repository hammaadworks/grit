"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";

export type TerminalLineType = "input" | "progress" | "output";

export interface TerminalLine {
  type: TerminalLineType;
  value: string;
  delay?: number; // Delay before this line starts showing
  duration?: number; // Duration of the animation (typing or progress)
  prompt?: string; // Custom prompt for input lines
}

interface TerminalAnimationProps {
  lines: TerminalLine[];
  className?: string;
  title?: string;
}

export function TerminalAnimation({ lines, className, title = "bash" }: TerminalAnimationProps) {
  const [currentLineIndex, setCurrentLineIndex] = useState(0);
  const [isFinished, setIsFinished] = useState(false);
  const [key, setKey] = useState(0); // Used to force re-render on restart

  useEffect(() => {
    if (currentLineIndex < lines.length) {
      const line = lines[currentLineIndex];
      const nextDelay = (line.delay || 0) + (line.duration || 0);

      const timer = setTimeout(() => {
        setCurrentLineIndex((prev) => prev + 1);
      }, nextDelay);

      return () => clearTimeout(timer);
    } else {
      setIsFinished(true);
    }
  }, [currentLineIndex, lines, key]);

  const handleRestart = () => {
    setCurrentLineIndex(0);
    setIsFinished(false);
    setKey((prev) => prev + 1);
  };

  return (
    <div className={cn("relative group rounded-xl overflow-hidden bg-[#1a1b26] border border-white/10 shadow-2xl font-mono text-sm", className)}>
      {/* Terminal Header */}
      <div className="flex items-center px-4 py-3 bg-[#24283b] border-b border-white/5">
        <div className="flex gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500/80" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
          <div className="w-3 h-3 rounded-full bg-green-500/80" />
        </div>
        <div className="flex-1 text-center text-xs text-white/40 select-none">
          {title}
        </div>
        <div className="w-12 flex justify-end">
          <button 
            onClick={handleRestart}
            className={cn(
              "text-white/40 hover:text-white transition-opacity",
              isFinished ? "opacity-100" : "opacity-0 pointer-events-none"
            )}
            title="Restart animation"
            aria-label="Restart animation"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Terminal Body */}
      <div className="p-5 min-h-[200px] overflow-x-auto text-white/80">
        <AnimatePresence mode="popLayout">
          <div key={key} className="flex flex-col gap-2">
            {lines.slice(0, currentLineIndex + 1).map((line, idx) => {
              const isCurrent = idx === currentLineIndex;
              return (
                <TerminalLineRender
                  key={idx}
                  line={line}
                  isCurrent={isCurrent}
                />
              );
            })}
          </div>
        </AnimatePresence>
      </div>
    </div>
  );
}

function TerminalLineRender({ line, isCurrent }: { line: TerminalLine; isCurrent: boolean }) {
  const { type, value, duration = 1000, prompt = "$" } = line;

  if (type === "input") {
    return (
      <div className="flex gap-2 items-center">
        <span className="text-primary font-bold">{prompt}</span>
        {isCurrent ? (
          <Typewriter text={value} duration={duration} />
        ) : (
          <span>{value}</span>
        )}
      </div>
    );
  }

  if (type === "progress") {
    return (
      <div className="text-cyan-400">
        {isCurrent ? (
          <ProgressBar text={value} duration={duration} />
        ) : (
          <span>████████████████████████████████████████ 100%</span>
        )}
      </div>
    );
  }

  // Output
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="text-white/60"
    >
      {value}
    </motion.div>
  );
}

function Typewriter({ text, duration }: { text: string; duration: number }) {
  const [displayedText, setDisplayedText] = useState("");

  useEffect(() => {
    let i = 0;
    const interval = duration / text.length;
    const timer = setInterval(() => {
      setDisplayedText((prev) => prev + text.charAt(i));
      i++;
      if (i >= text.length) {
        clearInterval(timer);
      }
    }, interval);

    return () => clearInterval(timer);
  }, [text, duration]);

  return (
    <span>
      {displayedText}
      <motion.span
        animate={{ opacity: [1, 0] }}
        transition={{ repeat: Infinity, duration: 0.8 }}
        className="inline-block w-2 h-4 bg-white/60 align-middle ml-1"
      />
    </span>
  );
}

function ProgressBar({ text, duration }: { text: string; duration: number }) {
  const [progress, setProgress] = useState(0);
  
  useEffect(() => {
    let start = Date.now();
    const timer = setInterval(() => {
      const elapsed = Date.now() - start;
      const newProgress = Math.min((elapsed / duration) * 100, 100);
      setProgress(newProgress);
      if (newProgress >= 100) clearInterval(timer);
    }, 50);
    return () => clearInterval(timer);
  }, [duration]);

  const totalBlocks = 40;
  const blocksToFill = Math.floor((progress / 100) * totalBlocks);
  const bar = "█".repeat(blocksToFill) + "░".repeat(totalBlocks - blocksToFill);

  return (
    <span>
      {bar} {Math.floor(progress)}%
    </span>
  );
}
