import type { Metadata } from "next";
import { Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// `adjustFontFallback` is off deliberately. next/font otherwise injects a
// metric-adjusted local fallback ahead of the stack, which then renders glyphs
// outside the latin subset (● U+25CF, → U+2192) at different widths than the
// original, whose stack fell through to plain monospace / sans-serif.
const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
  display: "swap",
  variable: "--font-plus-jakarta-sans",
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
  title: "Mission Control",
  description: "Read-only observability for a 7-agent content pipeline.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${plusJakartaSans.variable} ${jetbrainsMono.variable}`}
    >
      <body>{children}</body>
    </html>
  );
}
