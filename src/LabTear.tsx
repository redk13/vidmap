import React from 'react';
import {AbsoluteFill, Easing, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {loadFont as loadMont} from '@remotion/google-fonts/Montserrat';

const {fontFamily: MONT} = loadMont('normal', {weights: ['600', '700', '800', '900']});
const FPS = 30;
const W = 1500;
const H = 600;
const CARD = 120;

// Shot 06 — real, verified published headlines. Text-only source names; no logos.
const CARDS = [
  {
    source: 'BBC News',
    date: 'AUGUST 7, 2025',
    pre: '',
    mark: 'Nearly a million',
    post: ' more deaths than births in Japan last year',
    fs: 64,
    url: 'https://www.bbc.com/news/articles/c74dnzr4jdvo',
    body1: 'Japan recorded 686,061 births in 2024, the lowest number since records began in 1899, while nearly 1.6 million people died.',
    body2: 'The number of Japanese nationals fell by 908,574. It was the 16th consecutive year of population decline.',
    seed: 17,
  },
  {
    source: 'Reuters',
    date: 'AUGUST 15, 2024',
    pre: "Japan's economy ",
    mark: 'rebounds strongly',
    post: ' on consumption boost, backs case for more rate hikes',
    fs: 58,
    url: 'https://www.reuters.com/markets/asia/japan-q2-gdp-expands-annualised-31-april-june-2024-08-14/',
    body1: "Japan's economy expanded at an annualised 3.1% in the second quarter, rebounding from a slump at the start of the year.",
    body2: 'Private consumption rose 1.0% from the previous quarter, the first gain in five quarters.',
    seed: 41,
  },
  {
    source: 'AP News',
    date: 'JUNE 5, 2024',
    pre: "Japan's birth rate falls to a ",
    mark: 'record low',
    post: ' as the number of marriages also drops',
    fs: 60,
    url: 'https://apnews.com/article/japan-birth-rate-declining-population-82662ea061286cb907fd7d071e5b0b9b',
    body1: 'The data underscores Japan’s long-standing issues of a rapidly aging and shrinking population.',
    body2: 'The number of marriages fell by 6% to 474,717. The fertility rate stood at 1.2.',
    seed: 73,
  },
] as const;

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const mkRng = (seed: number) => {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
};

const edgeArrays = (seed: number) => {
  const r = mkRng(seed);
  const top: number[] = [];
  const bottom: number[] = [];
  const n = Math.ceil(W / 18);
  for (let i = 0; i <= n; i++) {
    top.push(Math.sin(i * 0.47 + seed) * 6 + (r() - 0.5) * 23);
    bottom.push(Math.sin(i * 0.39 + seed * 0.7) * 7 + (r() - 0.5) * 27);
  }
  return {top, bottom, n};
};

const Background: React.FC = () => (
  <AbsoluteFill style={{background: '#a9a9a7', overflow: 'hidden'}}>
    <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 48% 39%, #d0d0cd 0%, #b1b1af 43%, #8a8a89 76%, #696969 100%)'}} />
    <div style={{position: 'absolute', inset: 0, backgroundImage: `url(${staticFile('tear-grain.png')})`, backgroundSize: '360px 360px', opacity: 0.2, mixBlendMode: 'multiply'}} />
    {/* faint paper fibres and scuffs in the gray backdrop */}
    {[
      [307, 156, 19, -72], [1470, 130, 15, -66], [1260, 938, 22, 12],
      [421, 915, 17, 79], [1740, 706, 13, -80], [1060, 74, 18, 4],
      [163, 642, 12, 84], [1518, 494, 16, -11],
    ].map(([x, y, h, rot], i) => (
      <div key={i} style={{position: 'absolute', left: x, top: y, width: 2, height: h, background: i % 2 ? 'rgba(40,40,40,0.22)' : 'rgba(255,255,255,0.2)', transform: `rotate(${rot}deg)`}} />
    ))}
    <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at center, transparent 52%, rgba(0,0,0,0.2) 100%)'}} />
  </AbsoluteFill>
);

type CardData = (typeof CARDS)[number];

const TearCard: React.FC<{data: CardData; local: number}> = ({data, local}) => {
  const {top, bottom, n} = edgeArrays(data.seed);
  const enter = interpolate(local, [4, 25], [0, 1], {...clamp, easing: Easing.bezier(0.2, 0.75, 0.25, 1)});
  const leave = interpolate(local, [98, 116], [0, 1], {...clamp, easing: Easing.bezier(0.2, 0.75, 0.25, 1)});
  const open = local < 98 ? enter : 1 - leave;
  const opacity = interpolate(local, [0, 4], [0, 1], clamp) * interpolate(local, [116, 119], [1, 0], clamp);
  const contentOpacity = interpolate(open, [0.12, 0.62], [0, 1], clamp);
  const highlight = interpolate(local, [31, 46], [0, 1], {...clamp, easing: Easing.bezier(0.25, 0, 0.35, 1)});

  const points: string[] = [];
  for (let i = 0; i <= n; i++) {
    const x = (i / n) * W;
    const closedY = H / 2 - 34;
    const y = closedY * (1 - open) + top[i] * (0.35 + open * 0.65);
    points.push(`${x.toFixed(1)},${y.toFixed(1)}`);
  }
  for (let i = n; i >= 0; i--) {
    const x = (i / n) * W;
    const closedY = H / 2 + 34;
    const y = H - (H - closedY) * (1 - open) + bottom[i] * (0.35 + open * 0.65);
    points.push(`${x.toFixed(1)},${y.toFixed(1)}`);
  }
  const clipPath = `polygon(${points.join(',')})`;

  return (
    <div style={{position: 'absolute', left: (1920 - W) / 2, top: (1080 - H) / 2, width: W, height: H, opacity, filter: 'drop-shadow(0 19px 17px rgba(0,0,0,0.35))'}}>
      <div style={{position: 'absolute', inset: 0, clipPath, background: 'linear-gradient(102deg, #efefeb 0%, #e2e2de 48%, #d8d8d4 73%, #e9e9e5 100%)', overflow: 'hidden'}}>
        <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 27% 16%, rgba(255,255,255,0.48), transparent 48%), radial-gradient(ellipse at 78% 90%, rgba(70,70,70,0.11), transparent 54%)'}} />
        <div style={{position: 'absolute', inset: 0, backgroundImage: `url(${staticFile('tear-grain.png')})`, backgroundSize: '360px 360px', opacity: 0.16, mixBlendMode: 'multiply'}} />
        {/* quiet dotted newspaper grid, like the reference */}
        <div style={{position: 'absolute', inset: 0, backgroundImage: 'radial-gradient(circle, rgba(55,55,55,0.25) 1.2px, transparent 1.5px)', backgroundSize: '63px 63px', backgroundPosition: '19px 17px', opacity: 0.68}} />

        <div style={{position: 'absolute', left: 90, right: 90, top: 55, opacity: contentOpacity, color: '#171717', mixBlendMode: 'multiply'}}>
          <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 54, lineHeight: 1, letterSpacing: -2.2}}>{data.source}</div>
          <div style={{fontFamily: MONT, fontWeight: 800, fontSize: data.fs, lineHeight: 1.12, letterSpacing: -1.5, marginTop: 27}}>
            {data.pre}
            <span style={{backgroundImage: 'linear-gradient(100deg, #e7ef32, #dfe82c)', backgroundRepeat: 'no-repeat', backgroundPosition: '0 0', backgroundSize: `${highlight * 100}% 100%`, padding: '0 5px', boxDecorationBreak: 'clone', WebkitBoxDecorationBreak: 'clone'}}>{data.mark}</span>
            {data.post}
          </div>
          <div style={{fontFamily: MONT, fontWeight: 600, fontSize: 27, lineHeight: 1.2, letterSpacing: 0.2, marginTop: 19, color: '#343434'}}>{data.date}</div>
        </div>

        {/* two small newspaper columns; real excerpts, deliberately secondary */}
        <div style={{position: 'absolute', right: 90, bottom: 48, width: 475, display: 'flex', gap: 27, opacity: contentOpacity * 0.66, color: '#343434', mixBlendMode: 'multiply'}}>
          {[data.body1, data.body2].map((body, i) => (
            <div key={i} style={{width: 224, fontFamily: MONT, fontWeight: 600, fontSize: 11.5, lineHeight: 1.38, textAlign: 'justify'}}>{body}</div>
          ))}
        </div>
      </div>
    </div>
  );
};

export const LabTear: React.FC = () => {
  const frame = useCurrentFrame();
  const index = Math.min(CARDS.length - 1, Math.floor(frame / CARD));
  const local = frame - index * CARD;
  return (
    <AbsoluteFill style={{background: '#a9a9a7'}}>
      <Background />
      <TearCard key={index} data={CARDS[index]} local={local} />
    </AbsoluteFill>
  );
};
