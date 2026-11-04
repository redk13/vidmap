import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {JapanMap} from './JapanMap';

const RED = '#c2283a', DRED = '#8a1b28', BLUE = '#2f86ff', INK = '#0a1420', GREY = '#1d2b3a', YEL = '#ffd60a';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

// COLD OPEN — 1023 frames (synced to vo/01, stamp stays at f150 = 0:05)
export const ColdOpen: React.FC = () => {
  const f = useCurrentFrame();
  const W = 1920, H = 1080;
  const fadeIn = interpolate(f, [0, 30], [0, 1], clamp);
  const zoom = interpolate(f, [0, 80], [1.12, 1.0], clamp) * (1 + Math.max(0, f - 200) * 0.00006);
  const sweep = interpolate(f, [420, 540], [0, 46], clamp);
  const counter = Math.round(interpolate(f, [60, 330], [0, 918253], clamp));
  const ignite = f >= 560;
  const pulse = ((f - 560) % 55) / 55;
  // stamp flash: 0:05 = f150, half a second
  const stampIn = interpolate(f, [150, 155], [0, 1], clamp);
  const stampOut = interpolate(f, [166, 172], [1, 0], clamp);
  const stampO = Math.min(stampIn, stampOut);
  const stampS = interpolate(f, [150, 157], [2.4, 1], clamp);
  const whiteFlash = interpolate(f, [150, 153, 160], [0, 0.5, 0], clamp);
  const chipO = interpolate(f, [600, 615], [0, 1], clamp);
  const titleO = interpolate(f, [880, 905], [0, 1], clamp);
  const titleY = interpolate(f, [880, 905], [40, 0], clamp);

  const styleFor = (id: number) => {
    if (id === 13) return ignite
      ? {fill: BLUE, glow: true, stroke: '#bcd9ff', strokeWidth: 3}
      : {fill: GREY};
    const idx = id > 13 ? id - 1 : id;
    return idx <= sweep ? {fill: id % 3 === 0 ? DRED : RED} : {fill: GREY};
  };

  return (
    <AbsoluteFill style={{backgroundColor: INK, fontFamily: 'sans-serif', opacity: fadeIn}}>
      <AbsoluteFill style={{transform: `scale(${zoom})`}}>
        <JapanMap width={W} height={H} styleFor={styleFor}>
          {(centroidOf) => {
            const [tx, ty] = centroidOf(13);
            return (
              <g>
                {ignite && (
                  <g>
                    <circle cx={tx} cy={ty} r={130} fill="url(#halo)"/>
                    <circle cx={tx} cy={ty} r={16 + 90 * pulse} fill="none" stroke={BLUE}
                      strokeWidth={4 * (1 - pulse)} opacity={1 - pulse}/>
                    <circle cx={tx} cy={ty} r={16 + 90 * ((pulse + 0.5) % 1)} fill="none" stroke="#9cc4ff"
                      strokeWidth={3 * (1 - ((pulse + 0.5) % 1))} opacity={0.7 * (1 - ((pulse + 0.5) % 1))}/>
                    <circle cx={tx} cy={ty} r={9} fill="#eaf4ff"/>
                  </g>
                )}
                {chipO > 0 && (
                  <g opacity={chipO}>
                    <line x1={tx + 14} y1={ty - 14} x2={tx + 96} y2={ty - 84} stroke="#ffffff" strokeWidth={3}/>
                    <rect x={tx + 96} y={ty - 142} rx={12} width={565} height={62} fill="#ffffff"/>
                    <text x={tx + 378} y={ty - 99} textAnchor="middle" fontSize={33} fontWeight={900} fill={INK}>
                      ONLY TOKYO GROWS&#160;&#160;+0.09%
                    </text>
                  </g>
                )}
              </g>
            );
          }}
        </JapanMap>
      </AbsoluteFill>

      <div style={{position: 'absolute', top: 64, left: 86}}>
        <div style={{fontSize: 96, fontWeight: 900, color: '#fff', lineHeight: 1, textShadow: '0 4px 24px rgba(0,0,0,0.7)'}}>
          −{counter.toLocaleString('en-US')}
        </div>
        <div style={{fontSize: 30, fontWeight: 700, color: YEL, letterSpacing: 3, marginTop: 10}}>
          DEATHS MINUS BIRTHS — 2025
        </div>
        <div style={{fontSize: 21, color: '#8fa6bd', marginTop: 6}}>Source: MHLW, 2026 · Japanese nationals</div>
      </div>

      {titleO > 0 && (
        <div style={{position: 'absolute', bottom: 90, width: '100%', textAlign: 'center',
          opacity: titleO, transform: `translateY(${titleY}px)`}}>
          <div style={{fontSize: 86, fontWeight: 900, color: '#fff', letterSpacing: 2, textShadow: '0 6px 30px rgba(0,0,0,0.8)'}}>
            WHY TOKYO IS <span style={{color: YEL}}>DELETING</span> JAPAN
          </div>
        </div>
      )}

      {stampO > 0 && (
        <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
          <div style={{position: 'absolute', inset: 0, background: '#fff', opacity: whiteFlash}}/>
          <div style={{opacity: stampO, transform: `scale(${stampS}) rotate(-8deg)`,
            border: `12px solid ${RED}`, borderRadius: 18, padding: '26px 70px',
            background: 'rgba(255,255,255,0.97)', boxShadow: '0 30px 80px rgba(0,0,0,0.6)'}}>
            <div style={{fontSize: 150, fontWeight: 900, color: RED, letterSpacing: 10, lineHeight: 1}}>BLACK HOLE</div>
            <div style={{fontSize: 30, fontWeight: 700, color: '#222', textAlign: 'center', marginTop: 10, letterSpacing: 2}}>
              POPULATION STRATEGY COUNCIL · 2024
            </div>
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
