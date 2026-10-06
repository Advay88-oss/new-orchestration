import type { Metadata } from "next";
import { Inter, Newsreader, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { THEME_BOOT } from "@/lib/theme";

// `adjustFontFallback` is off deliberately. next/font otherwise injects a
// metric-adjusted local fallback ahead of the stack, which then renders glyphs
// outside the latin subset (● U+25CF, → U+2192) at different widths than the
// original, whose stack fell through to plain monospace / sans-serif.
const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
  variable: "--font-sans",
  adjustFontFallback: false,
});

// The Assistant's greeting only.
const newsreader = Newsreader({
  subsets: ["latin"],
  weight: ["400", "500"],
  style: ["normal", "italic"],
  display: "swap",
  variable: "--font-serif",
  adjustFontFallback: false,
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
  variable: "--font-jetbrains-mono",
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
      className={`${inter.variable} ${newsreader.variable} ${jetbrainsMono.variable}`}
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
