import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {ensureFonts} from './fonts';

export const Kinetic: React.FC<{words: string[]; hexTag: string; accent: string}> = ({words, hexTag, accent}) => {
  ensureFonts();
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const seg = durationInFrames / words.length;
  const idx = Math.min(words.length - 1, Math.floor(frame / seg));
  const local = (frame - idx * seg) / seg; // 0..1
  const inOp = interpolate(local, [0, 0.2], [0, 1], {extrapolateRight: 'clamp'});
  const outOp = interpolate(local, [0.82, 1], [1, 0], {extrapolateLeft: 'clamp'});
  const rise = interpolate(local, [0, 0.25], [26, 0], {extrapolateRight: 'clamp'});
  const squares = [
    {x: '16%', y: '20%', s: 26}, {x: '82%', y: '28%', s: 34},
    {x: '70%', y: '72%', s: 22}, {x: '26%', y: '78%', s: 18},
  ];
  return (
    <AbsoluteFill style={{background: '#e8e8ea', alignItems: 'center', justifyContent: 'center'}}>
      {squares.map((q, i) => (
        <div key={i} style={{position: 'absolute', left: q.x, top: q.y, width: q.s, height: q.s, background: accent,
          transform: `translateY(${Math.sin((frame / 30) * Math.PI * 2 + i) * 14}px)`}} />
      ))}
      <div style={{fontFamily: 'Inter', fontWeight: 800, fontSize: 100, color: '#141418', textAlign: 'center',
        maxWidth: 900, lineHeight: 1.05, opacity: Math.min(inOp, outOp), transform: `translateY(${rise}px)`}}>
        {words[idx]}
      </div>
      <div style={{position: 'absolute', right: 60, bottom: 60, display: 'flex', alignItems: 'center', gap: 10}}>
        <div style={{width: 18, height: 18, background: accent}} />
        <span style={{fontFamily: 'Inter', fontWeight: 600, fontSize: 24, color: '#5a5a64'}}>{hexTag}</span>
      </div>
    </AbsoluteFill>
  );
};
