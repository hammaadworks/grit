"use client";

import { motion } from "framer-motion";
import { Heading, Section } from "../ui/core";
import { ShieldAlert, Smile, Heart } from "lucide-react";
import { cn } from "@/lib/utils"; // Corrected import for cn

/**
 * Section dedicated to articulating the emotional pain points and benefits.
 */
export function Emotions() {
  return (
    <Section className="py-32 text-center bg-card/30 border-y border-white/5 relative overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[300px] bg-primary/5 blur-[100px] pointer-events-none rounded-full" />

      <Heading level={2} className="mb-16 max-w-4xl mx-auto">
        We get it. The frustration of an <span className="text-primary">unseen streak</span> is real.
      </Heading>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
        <EmotionCard
          icon={ShieldAlert}
          title="The Missed Day Panic"
          description="That sudden anxiety when you realize you forgot to commit, and your beautiful green graph has a glaring white spot."
          color="text-red-400"
        />
        <EmotionCard
          icon={Heart}
          title="Your Effort, Unseen"
          description="You pour hours into your craft, but a sparse GitHub shows an incomplete story. Your hard work deserves recognition."
          color="text-rose-400"
        />
        <EmotionCard
          icon={Smile}
          title="The Joy of Green"
          description="Imagine a consistently vibrant contribution graph, a perfect reflection of every bit of code you wrote. Pure satisfaction."
          color="text-emerald-400"
        />
      </div>
    </Section>
  );
}

interface EmotionCardProps {
  icon: React.ElementType;
  title: string;
  description: string;
  color: string;
}

function EmotionCard({ icon: Icon, title, description, color }: EmotionCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.5 }}
      transition={{ duration: 0.5, delay: 0.1 }}
      className={cn("space-y-6")}
    >
      <Icon className={cn("w-16 h-16 mx-auto", color)} />
      <Heading level={3} className="text-2xl">{title}</Heading>
      <p className="text-muted-foreground leading-relaxed font-medium">
        {description}
      </p>
    </motion.div>
  );
}
