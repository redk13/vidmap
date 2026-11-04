import React from 'react';
import {AbsoluteFill, Audio, Easing, OffthreadVideo, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, delayRender, continueRender, cancelRender} from 'remotion';
const registerLocalFont = (family: string, file: string, weight = '400 900') => {
  const handle = delayRender(`Loading local font: ${family}`);
  const face = new FontFace(family, `url("${staticFile(file)}")`, {style: 'normal', weight});
  face.load().then((loaded) => {
    document.fonts.add(loaded);
    continueRender(handle);
  }).catch(cancelRender);
};

registerLocalFont('Montserrat', 'Montserrat-Variable.ttf');
const MONT = 'Montserrat';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const YELLOW = '#edff69';
const CYAN = '#79f4f2';

const IconStage: React.FC<{start: number; x: number; y: number; children: React.ReactNode}> = ({start, x, y, children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const local = frame - start;
  if (local < 0) return null;
  const enter = spring({frame: local, fps, config: {damping: 13, stiffness: 155, mass: 0.78}});
  const opacity = interpolate(local, [0, 3], [0, 1], clamp);
  const scale = interpolate(enter, [0, 1], [0.32, 1]);
  const lift = (1 - enter) * 42;
  const rotate = (1 - enter) * -5;
  return (
    <g transform={`translate(${x} ${y + lift}) rotate(${rotate}) scale(${scale}) translate(-150 -120)`} opacity={opacity} filter="url(#yellowNeon)">
      {children}
    </g>
  );
};

const Label: React.FC<{start: number; x: number; y: number; width?: number; lines: string[]}> = ({start, x, y, width = 500, lines}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const local = frame - start;
  if (local < 0) return null;
  const enter = spring({frame: local, fps, config: {damping: 16, stiffness: 145, mass: 0.72}});
  const opacity = interpolate(local, [0, 4], [0, 1], clamp);
  return (
    <div
      style={{
        position: 'absolute',
        left: x - width / 2,
        top: y + (1 - enter) * 28,
        width,
        opacity,
        transform: `scale(${interpolate(enter, [0, 1], [0.82, 1])})`,
        transformOrigin: 'center top',
        fontFamily: MONT,
        fontSize: lines.length > 2 || lines.some((line) => line.length > 22) ? 43 : 48,
        fontWeight: 800,
        lineHeight: 1.16,
        letterSpacing: -1.25,
        textAlign: 'center',
        color: '#ffffff',
        textShadow: '0 3px 7px rgba(0,0,0,.95), 0 0 18px rgba(0,0,0,.72)',
      }}
    >
      {lines.map((line) => <div key={line}>{line}</div>)}
    </div>
  );
};

const PropertyIcon: React.FC = () => (
  <g>
    <path d="M112 84 L158 45 L184 67 L253 10" fill="none" stroke={YELLOW} strokeWidth={15} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M235 8 L270 0 L263 35 Z" fill={YELLOW} />
    <path
      fill={YELLOW}
      fillRule="evenodd"
      d="M23 116 L119 35 L215 116 L195 116 L195 215 L55 215 L55 116 Z M100 215 L100 151 L139 151 L139 215 Z M153 137 L180 137 L180 164 L153 164 Z M19 215 L205 215 L205 226 L19 226 Z"
    />
    <path d="M30 116 L119 42 L208 116" fill="none" stroke={YELLOW} strokeWidth={12} strokeLinecap="round" strokeLinejoin="round" />
    <text x="195" y="128" fill={YELLOW} fontFamily={MONT} fontWeight={800} fontSize={103} letterSpacing={-7}>$</text>
  </g>
);

const CoinStack: React.FC<{x: number; y: number; count: number; scale?: number}> = ({x, y, count, scale = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`} fill="none" stroke={YELLOW} strokeWidth={5} strokeLinecap="round">
    {Array.from({length: count}).map((_, i) => (
      <g key={i} transform={`translate(0 ${-i * 12})`}>
        <ellipse cx="0" cy="0" rx="23" ry="8" />
        <path d="M-23 0 L-23 10 M23 0 L23 10" />
        <path d="M-23 10 C-14 20 14 20 23 10" />
      </g>
    ))}
  </g>
);

const TaxIcon: React.FC = () => (
  <g fill="none" stroke={YELLOW} strokeLinecap="round" strokeLinejoin="round">
    <path d="M161 107 L203 71 L224 87 L273 28" strokeWidth={14} />
    <path d="M256 24 L286 19 L280 50 Z" fill={YELLOW} stroke="none" />
    <path d="M103 75 C124 86 163 86 185 75 M115 64 L100 90 M174 64 L190 90" strokeWidth={7} />
    <path d="M106 88 C76 120 60 166 68 203 C98 221 190 221 222 203 C229 165 209 119 183 88 C161 99 129 99 106 88 Z" strokeWidth={8} fill="rgba(237,255,105,.055)" />
    <path d="M68 203 C45 202 32 211 26 226 C63 231 89 226 108 215 M221 203 C242 206 255 215 262 229 C231 230 208 225 190 215" strokeWidth={6} />
    <text x="143" y="181" textAnchor="middle" fill={YELLOW} stroke="none" fontFamily={MONT} fontWeight={800} fontSize={91}>$</text>
    <CoinStack x={104} y={62} count={3} scale={0.83} />
    <CoinStack x={137} y={47} count={4} scale={0.83} />
    <CoinStack x={218} y={198} count={3} scale={0.92} />
    <CoinStack x={249} y={215} count={2} scale={0.78} />
    <path d="M77 51 L77 35 M69 43 L85 43 M202 55 L202 42 M195 48 L209 48" strokeWidth={4} />
  </g>
);

const ServicesIcon: React.FC = () => (
  <g fill="none" stroke={YELLOW} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round">
    <path d="M48 113 C51 54 101 20 161 24 C196 26 222 39 239 61" />
    <path d="M220 55 L244 72 L251 44" />
    <path d="M42 113 C72 82 113 75 151 86 C176 93 190 105 206 119" strokeWidth={5} />
    <path d="M58 132 L139 80 L220 132 Z" fill="rgba(237,255,105,.07)" />
    <path d="M66 140 L212 140 M61 211 L217 211 M51 224 L227 224" />
    <path d="M79 145 L79 204 M108 145 L108 204 M139 145 L139 204 M170 145 L170 204 M199 145 L199 204" />
    <path d="M128 111 L139 103 L150 111 L150 122 L128 122 Z" strokeWidth={5} />
    <path d="M174 146 L211 116 L231 128 L273 78" strokeWidth={13} />
    <path d="M254 75 L283 68 L278 98 Z" fill={YELLOW} stroke="none" />
    <circle cx="239" cy="163" r="12" fill={YELLOW} stroke="none" />
    <circle cx="269" cy="171" r="10" fill={YELLOW} stroke="none" />
    <path d="M239 180 L239 218 M225 194 L239 184 L252 195 M239 218 L227 237 M239 218 L250 237" />
    <path d="M269 185 L269 219 M257 198 L269 189 L281 199 M269 219 L259 237 M269 219 L279 237" strokeWidth={6} />
  </g>
);

const NeonArrow: React.FC<{
  start: number;
  end: number;
  d: string;
  tip: {x: number; y: number; angle: number};
}> = ({start, end, d, tip}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (frame < start) return null;
  const progress = interpolate(frame, [start, end], [0, 1], {...clamp, easing: Easing.bezier(0.32, 0.02, 0.18, 1)});
  const headLocal = frame - (end - 3);
  const head = headLocal < 0 ? 0 : spring({frame: headLocal, fps, config: {damping: 12, stiffness: 190, mass: 0.6}});
  return (
    <g fill="none" stroke={CYAN} strokeLinecap="round" strokeLinejoin="round" filter="url(#cyanNeon)">
      <path d={d} pathLength={1} strokeWidth={16} opacity={0.18} strokeDasharray={1} strokeDashoffset={1 - progress} />
      <path d={d} pathLength={1} strokeWidth={6} strokeDasharray={1} strokeDashoffset={1 - progress} />
      <g transform={`translate(${tip.x} ${tip.y}) rotate(${tip.angle}) scale(${head})`} opacity={headLocal < 0 ? 0 : 1}>
        <path d="M-27 -22 L0 0 L-27 22" strokeWidth={7} />
      </g>
    </g>
  );
};

export const LabNeonSequence: React.FC = () => {
  return (
    <AbsoluteFill style={{backgroundColor: '#0b1210', overflow: 'hidden'}}>
      <OffthreadVideo
        src={staticFile('lab12-aerial.mp4')}
        muted
        style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'brightness(.57) saturate(.72) contrast(1.12)'}}
      />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at 52% 42%, rgba(0,0,0,.05) 20%, rgba(0,0,0,.30) 100%), linear-gradient(180deg, rgba(2,9,10,.14), rgba(2,9,10,.04) 52%, rgba(2,9,10,.22))'}} />
      <Audio src={staticFile('lab12-sound.wav')} volume={0.72} />

      <svg width="1920" height="1080" viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
        <defs>
          <filter id="yellowNeon" x="-70%" y="-70%" width="240%" height="240%" colorInterpolationFilters="sRGB">
            <feGaussianBlur in="SourceGraphic" stdDeviation="7" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="cyanNeon" x="-60%" y="-60%" width="220%" height="220%" colorInterpolationFilters="sRGB">
            <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        <NeonArrow start={48} end={78} d="M820 316 C915 254 1035 263 1135 330" tip={{x: 1135, y: 330, angle: 36}} />
        <NeonArrow start={144} end={174} d="M1530 515 C1605 570 1600 650 1530 705" tip={{x: 1530, y: 705, angle: 142}} />

        <IconStage start={4} x={580} y={255}><PropertyIcon /></IconStage>
        <IconStage start={84} x={1350} y={255}><TaxIcon /></IconStage>
        <IconStage start={180} x={1350} y={710}><ServicesIcon /></IconStage>
      </svg>

      <Label start={10} x={580} y={397} lines={['High Property', 'Values']} />
      <Label start={90} x={1350} y={397} lines={['Large Local', 'Tax Base']} />
      <Label start={186} x={1350} y={852} width={650} lines={['High Funding for', 'Schools & Public Services']} />

      <div style={{position: 'absolute', left: 60, bottom: 30, fontFamily: MONT, fontSize: 17, fontWeight: 500, letterSpacing: 0.5, color: 'rgba(255,255,255,.72)', textShadow: '0 2px 5px rgba(0,0,0,.9)'}}>
        Aerial: David McBee / Pexels · 4770380
      </div>
    </AbsoluteFill>
  );
};
