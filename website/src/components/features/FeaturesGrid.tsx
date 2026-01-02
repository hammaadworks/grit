"use client";

import { Shield, Zap, BookOpen, GitGraph } from "lucide-react";
import { Heading, Section } from "../ui/core";
import { Feature } from "@/types";
import { cn } from "@/lib/utils"; // Corrected import for cn
import { motion } from "framer-motion";

const FEATURES: Feature[] = [
  {
    icon: Shield,
    title: "Atomic Integrity",
    description: "Commit counts increment ONLY on success. No false positives, no corrupted history."
  },
  {
    icon: Zap,
    title: "Recursive SQL",
    description: "SQLite CTEs find dates in under 1ms. No Python loops, just raw database speed."
  },
  {
    icon: GitGraph,
    title: "Visual Logging",
    description: "A beautifully enhanced, human-readable git log on jetpack rollerskates."
  },
  {
    icon: BookOpen,
    title: "Open Architecture",
    description: "Built with Python 3.10+, Typer, and Rich. Clean, typed, and easy to audit or extend."
  }
];

/**
 * Grid of core project values and features.
 */
export function FeaturesGrid() {
  return (
    <Section>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
        {FEATURES.map((feature, index) => (
          <motion.div 
            key={feature.title} 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.5 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className={cn("space-y-6 group")}
          >
            <div className={cn("text-primary w-12 h-12 rounded-xl bg-primary/5 flex items-center justify-center border border-primary/10 transition-transform group-hover:scale-110")}>
              <feature.icon className="w-6 h-6" />
            </div>
            <Heading level={3} className="text-2xl">{feature.title}</Heading>
            <p className="text-muted-foreground leading-relaxed font-medium">
              {feature.description}
            </p>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}
