"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

const lines = [
  { text: "$ grit config", type: "input", delay: 0 },
  { text: "Welcome to Grit Setup", type: "output", delay: 500 },
  { text: "? What is your daily commit target? 3", type: "prompt", delay: 1000 },
  { text: "✓ Setup complete!", type: "success", delay: 1500 },
  { text: "$ grit commit -m 'feat: intelligent graph allocation'", type: "input", delay: 2500 },
  { text: "✓ Commit successfully allocated to 2024-03-24", type: "success", delay: 3500 },
];

export function Terminal() {
  const [visibleLines, setVisibleLines] = useState<number>(0);

  useEffect(() => {
    let timeouts: NodeJS.Timeout[] = [];
    
    lines.forEach((line, index) => {
      const timeout = setTimeout(() => {
        setVisibleLines((prev) => Math.max(prev, index + 1));
      }, line.delay);
      timeouts.push(timeout);
    });

    return () => timeouts.forEach(clearTimeout);
  }, []);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="w-full max-w-2xl mx-auto mt-12 rounded-xl overflow-hidden shadow-2xl border border-border bg-[#0A0A0A]"
    >
      <div className="flex items-center px-4 py-3 bg-[#1A1A1A] border-b border-white/5">
        <div className="flex gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <div className="w-3 h-3 rounded-full bg-green-500" />
        </div>
        <div className="mx-auto text-xs text-white/40 font-mono">bash</div>
      </div>
      <div className="p-6 font-mono text-sm sm:text-base leading-relaxed h-[240px] overflow-hidden">
        {lines.slice(0, visibleLines).map((line, i) => (
          <motion.div 
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            key={i} 
            className="mb-2"
          >
            {line.type === "input" && (
              <span className="text-white"><span className="text-primary font-bold">{line.text.split(' ')[0]}</span> {line.text.slice(line.text.indexOf(' '))}</span>
            )}
            {line.type === "prompt" && (
              <span className="text-cyan-400">{line.text}</span>
            )}
            {line.type === "success" && (
              <span className="text-green-400">{line.text}</span>
            )}
            {line.type === "output" && (
              <span className="text-white/70">{line.text}</span>
            )}
          </motion.div>
        ))}
        <motion.div 
          animate={{ opacity: [1, 0] }} 
          transition={{ repeat: Infinity, duration: 0.8 }}
          className="inline-block w-2 h-4 bg-primary align-middle mt-1"
        />
      </div>
    </motion.div>
  );
}
