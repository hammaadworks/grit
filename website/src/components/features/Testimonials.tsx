"use client";

import { motion } from "framer-motion";
import { Heading, Section } from "../ui/core";
import { Star } from "lucide-react";
import { cn } from "../ui/core";

interface Testimonial {
  quote: string;
  author: string;
  role: string;
  rating: number;
}

const TESTIMONIALS: Testimonial[] = [
  {
    quote: "Grit has completely changed how I think about my GitHub. My graph finally looks like I actually code, even with my sporadic schedule. Huge confidence booster!",
    author: "Alex 'ByteBender' Rivera",
    role: "Freelance Developer",
    rating: 5,
  },
  {
    quote: "The O(1) allocator is genius. I expected some lag, but it's seamless. My streak is safe, and I don't even have to think about it. This is how dev tools should be built.",
    author: "Jordan 'CodeWhisperer' Smith",
    role: "Open Source Maintainer",
    rating: 5,
  },
  {
    quote: "As someone who jumps between projects and machines, the self-healing sync is a lifesaver. Grit just works, making sure my efforts are always visible.",
    author: "Sarah 'DevOpsDiva' Chen",
    role: "Staff Software Engineer",
    rating: 5,
  },
];

/**
 * Testimonials section for the homepage.
 * Uses placeholder content from early users.
 */
export function Testimonials() {
  return (
    <Section className="py-32 bg-card/30 border-y border-white/5 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-primary/5 blur-[100px] rounded-full -mr-48 -mt-48" />
      <div className="text-center mb-16">
        <Heading level={2} className="mb-4">What Our Early Users Say</Heading>
        <p className="text-muted-foreground max-w-2xl mx-auto text-lg font-medium">
          Hear from developers who've transformed their GitHub presence with Grit.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {TESTIMONIALS.map((testimonial, index) => (
          <TestimonialCard key={index} {...testimonial} />
        ))}
      </div>
    </Section>
  );
}

function TestimonialCard({ quote, author, role, rating }: Testimonial) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true, amount: 0.5 }}
      transition={{ duration: 0.5, delay: 0.1 * rating }}
      className={cn(
        "p-8 rounded-[2rem] bg-background border border-border shadow-lg",
        "flex flex-col justify-between h-full group hover:border-primary/30 transition-all hover:-translate-y-2"
      )}
    >
      <div className="flex items-center gap-1 mb-4">
        {[...Array(rating)].map((_, i) => (
          <Star key={i} className="w-5 h-5 fill-yellow-500 text-yellow-500" />
        ))}
      </div>
      <p className="text-lg italic mb-6 text-foreground/90 leading-relaxed">"{quote}"</p>
      <div>
        <h4 className="font-bold text-base">{author}</h4>
        <p className="text-sm text-muted-foreground">{role}</p>
      </div>
    </motion.div>
  );
}
