import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring} from 'remotion';
import {ensureFonts} from './fonts';

function shade(hex: string, f: number): string {
  const n = hex.replace('#', '');
  const r = Math.round(parseInt(n.slice(0, 2), 16) * f);
  const g = Math.round(parseInt(n.slice(2, 4), 16) * f);
  const b = Math.round(parseInt(n.slice(4, 6), 16) * f);
  return `rgb(${r},${g},${b})`;
}

export const Stat: React.FC<{stat: string; label: string; accent: string; bg: string}> = ({stat, label, accent}) => {
  ensureFonts();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame, fps, config: {damping: 16, mass: 0.8}});
  const scale = interpolate(s, [0, 1], [0.72, 1]);
  const op = interpolate(frame, [0, 14], [0, 1], {extrapolateRight: 'clamp'});
  const lop = interpolate(frame, [16, 36], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 74% 16%, ${accent}, ${shade(accent, 0.5)})`,
        alignItems: 'center', justifyContent: 'center', flexDirection: 'column',
      }}
    >
      <div style={{fontFamily: 'Inter', fontWeight: 800, fontSize: 240, color: '#fff', letterSpacing: -6, transform: `scale(${scale})`, opacity: op}}>
        {stat}
      </div>
      <div style={{fontFamily: 'Inter', fontWeight: 500, fontSize: 46, color: 'rgba(255,255,255,0.9)', opacity: lop, marginTop: 8}}>
        {label}
      </div>
    </AbsoluteFill>
  );
};
