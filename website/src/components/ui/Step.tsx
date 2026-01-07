"use client";

import { Heading } from "./core";
import { CopyableCode } from "./CopyableCode";
import { cn } from "@/lib/utils"; // Corrected import for cn

interface StepProps {
  /** Sequential step number. */
  num: number;
  /** Step title. */
  title: string;
  /** Detailed description. */
  desc: string;
  /** Optional shell command to copy. */
  code?: string;
}

/**
 * A numbered instructional step component.
 */
export function Step({ num, title, desc, code }: StepProps) {
  return (
    <div className="group space-y-3">
      <header className="flex items-center gap-3">
        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground text-[10px] font-bold flex items-center justify-center select-none">
          {num}
        </span>
        <Heading level={4} className="text-lg">{title}</Heading>
      </header>
      <div className="ml-9 space-y-4">
        <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
        {code && <CopyableCode code={code} className={cn("bg-black/20", code && "pl-4")} />}
      </div>
    </div>
  );
}
