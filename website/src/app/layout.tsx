import type { Metadata } from "next";
import "./globals.css";
import { Header, Footer } from "@/components/layout/Navigation";
import Image from "next/image"; // Import Image component

export const metadata: Metadata = {
  title: "Grit | The Intelligent Git Wrapper",
  description: "Keep your GitHub graph perfectly consistent with a unified backdated history.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground selection:bg-primary/30">
        <Header />
        <div className="pt-16">
          {children}
        </div>
        <Footer />
      </body>
    </html>
  );
}