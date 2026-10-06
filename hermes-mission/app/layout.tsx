import type { Metadata } from "next";
import { Hanken_Grotesk, Newsreader, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import "./herald.css";
import { THEME_BOOT } from "@/lib/theme";

// `adjustFontFallback` is off deliberately. next/font otherwise injects a
// metric-adjusted local fallback ahead of the stack, which then renders glyphs
// outside the latin subset (● U+25CF, → U+2192) at different widths than the
// original, whose stack fell through to plain monospace / sans-serif.
const hanken = Hanken_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
  variable: "--font-sans",
  adjustFontFallback: false,
});

// The Assistant's greeting only.
const newsreader = Newsreader({
  subsets: ["latin"],
  axes: ["opsz"],
  display: "swap",
  variable: "--font-serif",
  adjustFontFallback: false,
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
  variable: "--font-mono",
  adjustFontFallback: false,
});

export const metadata: Metadata = {
  title: "Herald",
  description: "Researches your market, writes posts, checks every claim, and waits for your approval.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${hanken.variable} ${newsreader.variable} ${plexMono.variable}`}
      suppressHydrationWarning
    >
      <head>
        {/* The saved light/dark choice, applied before first paint (lib/theme.ts). */}
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOT }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
