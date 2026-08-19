import React from 'react';
import {Composition} from 'remotion';
import {Stat} from './Stat';
import {Kinetic} from './Kinetic';
import {Mockup} from './Mockup';

const VANNA = {accent: '#8B5CF6', bg: '#0D0616'};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Stat"
        component={Stat}
        durationInFrames={150}
        fps={30}
        width={1080}
        height={1080}
        defaultProps={{stat: '$92M+', label: 'Total XLM Supplied on Vanna', accent: VANNA.accent, bg: VANNA.bg}}
      />
      <Composition
        id="Kinetic"
        component={Kinetic}
        durationInFrames={210}
        fps={30}
        width={1080}
        height={1080}
        defaultProps={{
          words: ['Payments were the easy half.', 'Credit is the wedge.', 'Vanna gives agents a balance sheet.'],
          hexTag: '0xVANNA',
          accent: VANNA.accent,
        }}
      />
      <Composition
        id="Mockup"
        component={Mockup}
        durationInFrames={210}
        fps={30}
        width={1080}
        height={1080}
        defaultProps={{
          title: 'Vanna · Farm', statLabel: 'Supply APY', statValue: '378.88%',
          token: 'XLM', balance: '1,307.36 XLM', cta: 'Supply XLM', wallet: 'GC2D…PY6X',
          accent: VANNA.accent, bg: VANNA.bg,
        }}
      />
    </>
  );
};
