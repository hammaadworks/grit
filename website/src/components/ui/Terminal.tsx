"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState, useRef } from "react";
import { Copy, Check, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";

type LineType = "input" | "progress" | "output" | "success" | "prompt" | "warning";

interface TerminalLineDef {
  text: string;
  type: LineType;
  delay?: number;    // wait before starting this line
  duration?: number; // how long the line takes to "type" or "progress"
}

// We simulate installing Grit and running a basic config
const DEFAULT_LINES: TerminalLineDef[] = [
  { text: "uv tool install grit", type: "input", delay: 500, duration: 1200 },
  { text: "Resolved 24 packages in 142ms", type: "output", delay: 200 },
  { text: "Installed grit v0.1.0", type: "success", delay: 400 },
  { text: "grit status", type: "input", delay: 800, duration: 600 },
  { text: "Current Streak: 42 days", type: "output", delay: 300 },
  { text: "Gaps detected: 3 (Last 7 days)", type: "warning", delay: 200 },
  { text: "Next scheduled sync: 18:00 (Today)", type: "output", delay: 200 },
  { text: "grit sync --force", type: "input", delay: 1000, duration: 800 },
  { text: "Syncing 3 missed contributions...", type: "output", delay: 300 },
  { text: "progress", type: "progress", delay: 100, duration: 2000 },
  { text: "✓ Contribution graph updated successfully!", type: "success", delay: 500 },
  { text: "Your green wall is looking solid. 🌿", type: "output", delay: 400 },
];

interface TerminalProps {
  lines?: TerminalLineDef[];
  title?: string;
  className?: string;
}

export function Terminal({ lines = DEFAULT_LINES, title = "grit terminal", className }: TerminalProps) {
  const [currentLineIndex, setCurrentLineIndex] = useState(-1);
  const [key, setKey] = useState(0); // for restarting
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const isFinished = currentLineIndex >= lines.length;

  useEffect(() => {
    let currentIdx = 0;
    let cancelled = false;

    const runSequence = async () => {
      for (let i = 0; i < lines.length; i++) {
        if (cancelled) return;
        const line = lines[i];
        
        // Wait before showing the line
        await new Promise((r) => setTimeout(r, line.delay || 0));
        if (cancelled) return;
        
        setCurrentLineIndex(i);

        // Wait for the line to "finish" its internal animation
        if (line.duration) {
          await new Promise((r) => setTimeout(r, line.duration));
        }
      }
      if (!cancelled) {
        setCurrentLineIndex(lines.length); // Mark as fully finished
      }
    };

    runSequence();

    return () => {
      cancelled = true;
    };
  }, [key, lines]);

  const handleRestart = () => {
    setCurrentLineIndex(-1);
    setKey((prev) => prev + 1);
  };

  const copyToClipboard = async (text: string, index: number) => {
    await navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className={cn(
        "w-full max-w-2xl mx-auto rounded-2xl overflow-hidden shadow-[0_20px_50px_rgba(20,184,166,0.1)] border border-white/10 bg-black/80 backdrop-blur-xl relative",
        className
      )}
    >
      <header className="flex items-center px-5 py-4 bg-white/[0.03] border-b border-white/5 relative">
        <div className="flex gap-2">
          <div className="w-3 h-3 rounded-full bg-rose-500/50" />
          <div className="w-3 h-3 rounded-full bg-amber-500/50" />
          <div className="w-3 h-3 rounded-full bg-emerald-500/50" />
        </div>
        <div className="mx-auto text-[10px] font-bold text-white/20 uppercase tracking-[0.2em] select-none absolute left-1/2 -translate-x-1/2">
          {title}
        </div>
        
        {/* Restart Button */}
        <button 
          onClick={handleRestart}
          className={cn(
            "absolute right-4 text-white/40 hover:text-white transition-opacity flex items-center gap-1.5 text-xs font-mono",
            isFinished ? "opacity-100" : "opacity-0 pointer-events-none"
          )}
          title="Restart animation"
        >
          restart <RotateCcw className="w-3 h-3" />
        </button>
      </header>
      
      <div key={key} className="p-8 font-mono text-sm sm:text-base leading-relaxed min-h-[360px] max-h-[400px] overflow-y-auto text-left relative flex flex-col">
        {lines.map((line, i) => {
          if (i > currentLineIndex) return null;
          const isCurrent = i === currentLineIndex;

          return (
            <motion.div 
              initial={{ opacity: 0, x: -5 }}
              animate={{ opacity: 1, x: 0 }}
              key={i} 
              className="mb-3 flex items-center group relative w-full"
            >
              <div className="flex-1 min-w-0">
                {line.type === "input" ? (
                  <div className="flex items-center gap-3">
                    <span className="text-primary font-bold shrink-0">$</span>
                    <span className="text-white font-medium break-all">
                      {isCurrent ? (
                        <Typewriter text={line.text} duration={line.duration || 1000} />
                      ) : (
                        line.text
                      )}
                    </span>
                  </div>
                ) : line.type === "progress" ? (
                  <div className="text-teal-400 w-full overflow-hidden text-xs sm:text-sm">
                    {isCurrent ? (
                      <ProgressBar duration={line.duration || 1500} />
                    ) : (
                      <span className="tracking-tighter">████████████████████████████████████████ 100%</span>
                    )}
                  </div>
                ) : (
                  <span className={cn(
                    line.type === "prompt" && "text-teal-400/80",
                    line.type === "success" && "text-emerald-400 font-bold",
                    line.type === "warning" && "text-amber-400",
                    line.type === "output" && "text-white/40",
                    "break-words block"
                  )}>
                    {line.text}
                  </span>
                )}
              </div>
              
              {line.type === "input" && !isCurrent && (
                <button 
                  onClick={() => copyToClipboard(line.text, i)}
                  className="opacity-0 group-hover:opacity-100 transition-all p-2 hover:bg-white/5 rounded-lg text-white/20 hover:text-primary active:scale-95 shrink-0 ml-2"
                  title="Copy command"
                >
                  {copiedIndex === i ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </button>
              )}
            </motion.div>
          );
        })}

        {/* Blinking Cursor at the bottom if animation is not finished */}
        {!isFinished && (
          <motion.div 
            animate={{ opacity: [1, 0] }} 
            transition={{ repeat: Infinity, duration: 0.8 }}
            className="inline-block w-2.5 h-5 bg-primary/70 align-middle mt-1"
          />
        )}
      </div>
    </motion.div>
  );
}

function Typewriter({ text, duration }: { text: string; duration: number }) {
  const [displayedText, setDisplayedText] = useState("");

  useEffect(() => {
    let start = Date.now();
    let frameId: number;

    const tick = () => {
      const elapsed = Date.now() - start;
      const progress = Math.min(elapsed / duration, 1);
      const charsToShow = Math.floor(progress * text.length);
      setDisplayedText(text.slice(0, charsToShow));

      if (progress < 1) {
        frameId = requestAnimationFrame(tick);
      }
    };

    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [text, duration]);

  return <span>{displayedText}</span>;
}

function ProgressBar({ duration }: { duration: number }) {
  const [progress, setProgress] = useState(0);
  
  useEffect(() => {
    let start = Date.now();
    let frameId: number;

    const tick = () => {
      const elapsed = Date.now() - start;
      const p = Math.min((elapsed / duration) * 100, 100);
      setProgress(p);

      if (p < 100) {
        frameId = requestAnimationFrame(tick);
      }
    };

    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [duration]);

  const totalBlocks = 40;
  const blocksToFill = Math.floor((progress / 100) * totalBlocks);
  const bar = "█".repeat(blocksToFill) + "░".repeat(totalBlocks - blocksToFill);

  return (
    <span className="tracking-tighter">
      {bar} {Math.floor(progress).toString().padStart(3, " ")}%
    </span>
  );
}
