import type { Metadata } from "next";
import { Outfit, Space_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AutoLance — AI-Powered Upwork Intelligence",
  description:
    "Find your highest-converting Upwork jobs with AI-powered match scoring, client quality analysis, personalized cover letters, and real-time alerts.",
  keywords: "Upwork, freelance, AI, job matching, cover letter, proposal",
  openGraph: {
    title: "AutoLance",
    description: "AI-Powered Upwork Intelligence Engine",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`dark ${outfit.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable}`}>
      <body className="font-sans antialiased bg-surface-900 text-slate-100">{children}</body>
    </html>
  );
}
