import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring} from 'remotion';
import {ensureFonts} from './fonts';

function countUp(value: string, f: number): string {
  const m = value.match(/[-+]?\d[\d,]*\.?\d*/);
  if (!m) return value;
  const target = parseFloat(m[0].replace(/,/g, ''));
  const dec = m[0].includes('.') ? 2 : 0;
  const cur = (target * Math.max(0, Math.min(1, f))).toLocaleString(undefined, {minimumFractionDigits: dec, maximumFractionDigits: dec});
  return value.slice(0, m.index) + cur + value.slice((m.index ?? 0) + m[0].length);
}

export const Mockup: React.FC<{
  title: string; statLabel: string; statValue: string; token: string;
  balance: string; cta: string; wallet: string; accent: string; bg: string;
}> = ({title, statLabel, statValue, token, balance, cta, wallet, accent, bg}) => {
  ensureFonts();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const cardS = spring({frame, fps, config: {damping: 18}});
  const cardY = interpolate(cardS, [0, 1], [50, 0]);
  const cardOp = interpolate(frame, [0, 12], [0, 1], {extrapolateRight: 'clamp'});
  const countF = interpolate(frame, [12, 60], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const rowOp = interpolate(frame, [55, 75], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const ctaOp = interpolate(frame, [75, 90], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const rip = interpolate(frame, [140, 180], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{background: `radial-gradient(circle at 50% 30%, #1a1230, ${bg})`, alignItems: 'center', justifyContent: 'center'}}>
      <div style={{width: 780, background: '#18122a', border: `2px solid ${accent}55`, borderRadius: 30, padding: 40,
        opacity: cardOp, transform: `translateY(${cardY}px)`, fontFamily: 'Inter'}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <span style={{fontWeight: 700, fontSize: 34, color: '#f5f2fa'}}>{title}</span>
          <span style={{background: '#2a2340', color: '#968fa5', borderRadius: 22, padding: '8px 18px', fontSize: 22}}>{wallet}</span>
        </div>
        <div style={{marginTop: 34, color: '#968fa5', fontSize: 30}}>{statLabel}</div>
        <div style={{fontWeight: 800, fontSize: 118, color: accent, lineHeight: 1}}>{countUp(statValue, countF)}</div>
        <div style={{marginTop: 30, background: '#221c32', borderRadius: 16, padding: '18px 22px', display: 'flex',
          alignItems: 'center', justifyContent: 'space-between', opacity: rowOp}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <div style={{width: 48, height: 48, borderRadius: 24, background: accent, color: bg, fontWeight: 800,
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24}}>{token[0]}</div>
            <span style={{fontWeight: 700, fontSize: 32, color: '#f5f2fa'}}>{token}</span>
          </div>
          <span style={{fontSize: 26, color: '#968fa5'}}>{balance}</span>
        </div>
        <div style={{position: 'relative', marginTop: 40, background: accent, borderRadius: 18, padding: '22px 0',
          textAlign: 'center', opacity: ctaOp, overflow: 'hidden'}}>
          <span style={{fontWeight: 700, fontSize: 36, color: bg}}>{cta}</span>
          {rip > 0 && rip < 1 && (
            <div style={{position: 'absolute', left: '50%', top: '50%', width: 40 + rip * 260, height: 40 + rip * 260,
              borderRadius: '50%', border: '4px solid rgba(255,255,255,0.7)', transform: 'translate(-50%,-50%)', opacity: 1 - rip}} />
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
