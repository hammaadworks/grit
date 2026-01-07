"use client";

import Link from "next/link";
import { Terminal as Github, BookOpen, Code2 } from "lucide-react";
import { SITE_CONFIG } from "@/lib/constants";
import { cn } from "@/lib/utils"; // Corrected import for cn
import { motion } from "framer-motion";
import { Button } from "../ui/shadcn";
import Image from "next/image"; // Import Image component
import { Star } from "lucide-react"; // Import Star icon

interface NavLinkProps {
  href: string;
  children: React.ReactNode;
  icon?: React.ElementType;
}

function NavLink({ href, children, icon: Icon }: NavLinkProps) {
  return (
    <Link 
      href={href} 
      className="text-white/60 hover:text-white transition-colors flex items-center gap-2 group text-sm font-medium"
    >
      {Icon && <Icon className="w-4 h-4 transition-transform group-hover:scale-110" />}
      {children}
    </Link>
  );
}

/**
 * Global Header component for consistent site navigation and branding.
 */
export function Header() {
  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5, duration: 0.5 }}
      className={cn(
        "fixed top-0 left-0 right-0 z-40 bg-background/80 backdrop-blur-md border-b border-white/5",
        "flex items-center justify-between h-16 px-6 sm:px-12 lg:px-24"
      )}
    >
      <Link href="/" className="flex items-center gap-3">
        <Image src="/assets/logo.svg" alt="Grit Logo" width={32} height={32} />
        <span className="font-black text-xl tracking-tighter text-white select-none">GRIT</span>
      </Link>

      <nav className="hidden md:flex items-center gap-8">
        <NavLink href={SITE_CONFIG.docs.user}>User Guide</NavLink>
        <NavLink href={SITE_CONFIG.docs.developer}>Developer Docs</NavLink>
        <NavLink href={SITE_CONFIG.repo_url} icon={Github}>GitHub</NavLink>
      </nav>

      {/* Mobile / CTA */}
      <Link href={SITE_CONFIG.docs.user}>
        <Button size="sm" className="hidden md:flex">Get Started</Button>
      </Link>
      <Button size="sm" variant="ghost" className="md:hidden">Menu</Button> {/* Placeholder for mobile menu */}
    </motion.header>
  );
}

/**
 * Global Footer component for consistent site navigation, branding, and legal information.
 */
export function Footer() {
  return (
    <footer className="py-20 px-6 border-t border-white/5 bg-black/40 backdrop-blur-md relative z-10">
      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12">
        <div className="col-span-1 md:col-span-2 space-y-6">
          <Link href="/" className="flex items-center gap-3">
            <Image src="/assets/logo.svg" alt="Grit Logo" width={40} height={40} />
            <span className="font-black text-xl tracking-tighter text-white select-none">GRIT</span>
          </Link>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-xs">
            Intelligent commit distribution for consistent GitHub graphs. Built with technical integrity by hammaadworks.
          </p>
        </div>
        
        <div className="space-y-4">
          <h4 className="text-xs font-black uppercase tracking-[0.2em] text-white/40">Resources</h4>
          <nav className="flex flex-col gap-3">
            <NavLink href={SITE_CONFIG.docs.user}>User Guide</NavLink>
            <NavLink href={SITE_CONFIG.docs.developer}>Developer Docs</NavLink>
            <NavLink href={SITE_CONFIG.docs.llms}>AI context (LLMS.MD)</NavLink>
            <NavLink href={SITE_CONFIG.releases_url}>Download Releases</NavLink>
            <NavLink href={SITE_CONFIG.pypi_url}>PyPI Package</NavLink>
          </nav>
        </div>

        <div className="space-y-4">
          <h4 className="text-xs font-black uppercase tracking-[0.2em] text-white/40">Community</h4>
          <nav className="flex flex-col gap-3">
            <NavLink href={SITE_CONFIG.repo_url} icon={Github}>GitHub Repo</NavLink>
            <NavLink href={`${SITE_CONFIG.repo_url}/issues`}>Report Issue</NavLink>
            <NavLink href={`${SITE_CONFIG.repo_url}/stargazers`} icon={Star}>Stargazers</NavLink>
          </nav>
        </div>
      </div>
      <div className="max-w-5xl mx-auto mt-20 pt-10 border-t border-white/5 flex flex-col sm:flex-row justify-between items-center gap-6">
        <p className="text-[10px] font-bold uppercase tracking-widest text-white/20">
          &copy; 2026 hammaadworks. all rights reserved.
        </p>
        <div className="flex gap-6">
          <NavLink href="/#">Security</NavLink>
          <NavLink href="/#">Privacy</NavLink>
        </div>
      </div>
    </footer>
  );
}
