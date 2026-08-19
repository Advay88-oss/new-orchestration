"use client";

import { useState } from "react";
import type { CSSProperties, ReactNode } from "react";

/**
 * The original template expressed hover with a `style-hover` attribute alongside
 * the inline `style`. Inline styles cannot carry `:hover`, so the same merge is
 * done in JS: base style, overlaid with the hover style while pointed at.
 */
export function useHover() {
  const [hovered, setHovered] = useState(false);
  return {
    hovered,
    handlers: {
      onMouseEnter: () => setHovered(true),
      onMouseLeave: () => setHovered(false),
    },
  };
}

interface HoverButtonProps {
  style: CSSProperties;
  hoverStyle?: CSSProperties;
  onClick?: () => void;
  title?: string;
  children: ReactNode;
}

export function HoverButton({
  style,
  hoverStyle,
  onClick,
  title,
  children,
}: HoverButtonProps) {
  const { hovered, handlers } = useHover();
  return (
    <button
      onClick={onClick}
      title={title}
      style={hovered && hoverStyle ? { ...style, ...hoverStyle } : style}
      {...handlers}
    >
      {children}
    </button>
  );
}

interface HoverDivProps {
  style: CSSProperties;
  hoverStyle?: CSSProperties;
  onClick?: () => void;
  title?: string;
  children: ReactNode;
}

export function HoverDiv({
  style,
  hoverStyle,
  onClick,
  title,
  children,
}: HoverDivProps) {
  const { hovered, handlers } = useHover();
  return (
    <div
      onClick={onClick}
      title={title}
      style={hovered && hoverStyle ? { ...style, ...hoverStyle } : style}
      {...handlers}
    >
      {children}
    </div>
  );
}

interface HoverLinkProps {
  href: string;
  style?: CSSProperties;
  onClick?: (e: React.MouseEvent<HTMLAnchorElement>) => void;
  children: ReactNode;
}

export function HoverLink({ href, style, onClick, children }: HoverLinkProps) {
  return (
    <a href={href} onClick={onClick} style={style}>
      {children}
    </a>
  );
}
