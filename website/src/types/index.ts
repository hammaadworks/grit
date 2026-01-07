/**
 * @file types/index.ts
 * @description Centralized type definitions for the Grit website.
 */

import { LucideIcon } from "lucide-react";

export interface Feature {
  title: string;
  description: string;
  icon: LucideIcon;
}

export interface NavItem {
  label: string;
  href: string;
  icon?: LucideIcon;
}

export interface TerminalLine {
  text: string;
  type: "input" | "output" | "prompt" | "success";
  delay: number;
}

export interface Command {
  name: string;
  description: string;
  flags?: string;
}
