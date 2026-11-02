import React from 'react';
import {AbsoluteFill, Audio, Easing, Img, cancelRender, continueRender, delayRender, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const fontGate = delayRender('Loading Shot 14 online font');
const onlineFont = new FontFace('Shot14OnlineMontserrat', `url(${staticFile('lab14-Montserrat-Variable.ttf')})`, {weight: '100 900', style: 'normal'});
onlineFont.load().then((font) => {document.fonts.add(font); continueRender(fontGate);}).catch((error) => cancelRender(error));

const DATA = [
  [2005, 15.6], [2006, 17.2], [2007, 20.2], [2008, 22.8], [2009, 25.3],
  [2010, 28.4], [2011, 30.9], [2012, 33.3], [2013, 35.3], [2014, 37.4],
  [2015, 39.9], [2016, 43.6], [2017, 46.3], [2018, 49.4], [2019, 53.9],
  [2020, 60.1], [2021, 63.8], [2022, 67.0], [2023, 69.2], [2024, 71.2], [2025, 73.6],
] as const;
const X0 = 650;
const WIDTH = 1090;
const BASE = 820;
const HEIGHT = 570;
const point = (year: number, value: number) => ({x: X0 + (year - 2005) / 20 * WIDTH, y: BASE - value / 100 * HEIGHT});
const points = DATA.map(([year, value]) => point(year, value));
const LINE = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(' ');
const AREA = `M${X0} ${BASE} ${points.map((p) => `L${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(' ')} L${X0 + WIDTH} ${BASE} Z`;
const pointFrame = (year: number) => 40 + (year - 2005) / 20 * 125;

const WriteText: React.FC<{start: number; end: number; children: string; style: React.CSSProperties}> = ({start, end, children, style}) => {
  const frame = useCurrentFrame();
  if (frame < start) return null;
  const progress = interpolate(frame, [start, end], [0, 1], {...clamp, easing: Easing.bezier(0.25, 0.02, 0.25, 1)});
  return <div style={{...style, clipPath: `inset(-15% ${100 - progress * 100}% -20% 0)`, whiteSpace: 'nowrap'}}>{children}</div>;
};

const DataPoint: React.FC<{year: number; value: number; accent?: boolean}> = ({year, value, accent = false}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const at = pointFrame(year);
  if (frame < at) return null;
  const p = point(year, value);
  const scale = spring({frame: frame - at, fps, config: {damping: 12, stiffness: 190, mass: 0.6}});
  const ring = interpolate(frame, [at, at + 25], [0, 1], clamp);
  return (
    <g transform={`translate(${p.x} ${p.y})`}>
      {accent && ring < 1 ? <circle r={12 + ring * 34} fill="none" stroke="#e66d53" strokeWidth={3} opacity={1 - ring} /> : null}
      <g transform={`scale(${scale})`}>
        <circle r={accent ? 13 : 9} fill={accent ? '#e66d53' : '#ffffff'} stroke={accent ? '#ffffff' : '#3552a4'} strokeWidth={accent ? 4 : 4} />
      </g>
    </g>
  );
};

export const LabOnlineLine: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const gridProgress = interpolate(frame, [8, 36], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const lineProgress = interpolate(frame, [40, 165], [0, 1], clamp);
  const statSpring = spring({frame: Math.max(0, frame - 188), fps, config: {damping: 14, stiffness: 125, mass: 0.72}});
  const endPoint = point(2025, 73.6);
  const projection = interpolate(frame, [165, 184], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});

  return (
    <AbsoluteFill style={{backgroundColor: '#edf4f2', overflow: 'hidden', fontFamily: 'Shot14OnlineMontserrat'}}>
      <Img src={staticFile('lab14-online-paper.png')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      <Audio src={staticFile('lab14-online.wav')} volume={1.1} />

      <WriteText start={0} end={25} style={{position: 'absolute', left: 310, top: 68, width: 1300, textAlign: 'center', fontSize: 55, fontWeight: 800, letterSpacing: -1.7, color: '#111715'}}>
        People using the internet - World
      </WriteText>

      <svg width="1920" height="1080" viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
        <defs>
          <clipPath id="onlineGridReveal"><rect x={535} y={225} width={1260 * gridProgress} height={625} /></clipPath>
          <clipPath id="onlineAreaReveal"><rect x={635} y={225} width={1120 * lineProgress} height={610} /></clipPath>
          <linearGradient id="onlineArea" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#4f9fb5" stopOpacity={0.34} />
            <stop offset="100%" stopColor="#4f9fb5" stopOpacity={0.035} />
          </linearGradient>
        </defs>
        <g clipPath="url(#onlineGridReveal)" fill="none" stroke="#3b4b47" strokeWidth={2}>
          {[0, 25, 50, 75, 100].map((value) => {
            const y = BASE - value / 100 * HEIGHT;
            return <path key={value} d={`M650 ${y} H1740`} strokeDasharray="1 8" strokeLinecap="round" opacity={value === 0 ? 0.9 : 0.55} />;
          })}
        </g>
        <path d="M650 820 H1740" pathLength={1} fill="none" stroke="#33413d" strokeWidth={2.6} strokeDasharray={1} strokeDashoffset={1 - gridProgress} />
        <path d={AREA} fill="url(#onlineArea)" clipPath="url(#onlineAreaReveal)" />
        <path d={`M${endPoint.x} ${endPoint.y} V${endPoint.y + (BASE - endPoint.y) * projection}`} fill="none" stroke="#e66d53" strokeWidth={2} strokeDasharray="3 8" opacity={0.45} />
        <path d={LINE} pathLength={1} fill="none" stroke="#3552a4" strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={1} strokeDashoffset={1 - lineProgress} />
        {[2005, 2010, 2015, 2020].map((year) => {
          const row = DATA.find((d) => d[0] === year)!;
          return <DataPoint key={year} year={year} value={row[1]} />;
        })}
        <DataPoint year={2025} value={73.6} accent />
      </svg>

      {[0, 25, 50, 75, 100].map((value, i) => (
        <WriteText key={value} start={8 + i * 3} end={22 + i * 3} style={{position: 'absolute', left: 540, top: BASE - value / 100 * HEIGHT - 17, width: 85, textAlign: 'right', fontSize: 23, fontWeight: 500, color: '#33413d'}}>
          {`${value}%`}
        </WriteText>
      ))}
      {[2005, 2010, 2015, 2020, 2025].map((year) => (
        <WriteText key={year} start={pointFrame(year) + 2} end={pointFrame(year) + 14} style={{position: 'absolute', left: point(year, 0).x - 60, top: 842, width: 120, textAlign: 'center', fontSize: 23, fontWeight: 650, color: '#26332f'}}>
          {String(year)}
        </WriteText>
      ))}
      {[2010, 2015, 2020].map((year) => {
        const row = DATA.find((d) => d[0] === year)!;
        const p = point(year, row[1]);
        return <WriteText key={year} start={pointFrame(year) + 5} end={pointFrame(year) + 18} style={{position: 'absolute', left: p.x - 75, top: p.y - 58, width: 150, textAlign: 'center', fontSize: 25, fontWeight: 750, color: '#3552a4'}}>{`${row[1]}%`}</WriteText>;
      })}

      <div style={{position: 'absolute', left: 130, top: 390, width: 440, color: '#111715', transform: `translateY(${(1 - statSpring) * 20}px) scale(${0.92 + statSpring * 0.08})`, transformOrigin: 'left center'}}>
        <WriteText start={188} end={210} style={{fontSize: 112, fontWeight: 850, lineHeight: 1.05, letterSpacing: -6}}>73.6%</WriteText>
        <WriteText start={205} end={222} style={{fontSize: 42, fontWeight: 450, lineHeight: 1.25, letterSpacing: -1}}>of the world</WriteText>
        <WriteText start={216} end={234} style={{fontSize: 42, fontWeight: 750, lineHeight: 1.25, letterSpacing: -1, color: '#3552a4'}}>online in 2025</WriteText>
      </div>

      <div style={{position: 'absolute', left: 60, bottom: 34, fontSize: 17, fontWeight: 500, lineHeight: 1.45, color: 'rgba(30,42,38,.58)'}}>
        <div>Source: ITU via World Bank · 2005-2025</div>
        <div>IT.NET.USER.ZS · updated October 2026</div>
      </div>
    </AbsoluteFill>
  );
};
