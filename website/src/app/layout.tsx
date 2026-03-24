import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Grit | The Intelligent Git Wrapper",
  description: "Keep your GitHub graph perfectly consistent without destroying your true repository history.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground selection:bg-primary/30">
        {children}
      </body>
    </html>
  );
}
