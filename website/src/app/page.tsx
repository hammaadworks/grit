"use client";

import { Hero } from "@/components/features/Hero";
import { Emotions } from "@/components/features/Emotions";
import { HowItWorks } from "@/components/features/HowItWorks";
import { FeaturesGrid } from "@/components/features/FeaturesGrid";
import { Testimonials } from "@/components/features/Testimonials";
import { AINative } from "@/components/features/AINative";
import { StarBanner } from "@/components/features/StarBanner";

/**
 * Main landing page.
 * Architected for emotional resonance and clear user journey.
 */
export default function Home() {
  return (
    <main className="min-h-screen bg-background relative selection:bg-primary/20">
      <Hero />
      <Emotions />
      {/* Demo (Terminal is part of Hero) */}
      <FeaturesGrid />
      <HowItWorks />
      <Testimonials />
      <StarBanner />
      <AINative /> {/* Moved later in the page as requested */}
    </main>
  );
}
