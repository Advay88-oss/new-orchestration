import type { Metadata } from "next";
import { Instrument_Sans, Instrument_Serif, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// `adjustFontFallback` is off deliberately. next/font otherwise injects a
// metric-adjusted local fallback ahead of the stack, which then renders glyphs
// outside the latin subset (● U+25CF, → U+2192) at different widths than the
// original, whose stack fell through to plain monospace / sans-serif.
const instrumentSans = Instrument_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
  display: "swap",
  variable: "--font-sans",
  adjustFontFallback: false,
});

// Display headings only: page titles and section heads.
const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: ["400"],
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
  title: "Mission Control",
  description: "Production observability for the Vanna autonomous GTM pipeline.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${instrumentSans.variable} ${instrumentSerif.variable} ${jetbrainsMono.variable}`}
    >
      <body>{children}</body>
    </html>
  );
}
