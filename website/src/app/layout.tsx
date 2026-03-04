import { Footer, Header } from "@/components/layout/Navigation";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Grit | Git on TUI steroids with OCD.",
  description:
    "Git on TUI steroids for the obsessively disciplined. No mid graphs allowed. AI-powered commit distribution for perfectionists.",
  keywords: [
    "git wrapper",
    "github streak",
    "commit history",
    "ai commit message",
    "CommitScribe",
    "git automation",
    "backdated commits",
  ],
  authors: [{ name: "hammaadworks" }],
  openGraph: {
    title: "Grit | CommitScribe AI",
    description: "The intelligent git wrapper for professional developers.",
    url: "https://grit.dev",
    siteName: "Grit",
    images: [
      {
        url: "/assets/logo.svg",
        width: 1200,
        height: 630,
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Grit | CommitScribe AI",
    description: "Keep your GitHub streak unbreakable with CommitScribe AI.",
    images: ["/assets/logo.svg"],
  },
  alternates: {
    canonical: "https://grit.dev",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "Grit",
    operatingSystem: "Linux, macOS, Windows",
    applicationCategory: "DeveloperApplication",
    description:
      "An intelligent git wrapper that uses CommitScribe AI to maintain a consistent contribution graph.",
    softwareVersion: "0.7.89",
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
  };

  return (
    <html lang="en" className="dark">
      <head>
        <link
          rel="alternate"
          type="text/plain"
          href="/llms.txt"
          title="LLM Context"
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="min-h-screen bg-background text-foreground selection:bg-primary/30">
        <Header />
        <div className="pt-16">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
