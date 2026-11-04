import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
// Deterministic smoke test: everything derives from the frame number only.
export const Smoke: React.FC = () => {
  const f = useCurrentFrame();
  const pop = interpolate(f, [0, 149], [126.2, 87.0]);
  const sweep = interpolate(f, [0, 149], [-400, 1920]);
  const bar = interpolate(f, [0, 149], [0, 1520]);
  return (
    <AbsoluteFill style={{backgroundColor: '#0a1420', justifyContent: 'center', alignItems: 'center', fontFamily: 'sans-serif'}}>
      <div style={{position: 'absolute', left: sweep, top: 0, width: 420, height: 1080,
        background: 'linear-gradient(90deg, rgba(226,38,52,0.0), rgba(226,38,52,0.45), rgba(30,111,217,0.45), rgba(30,111,217,0.0))'}} />
      <div style={{fontSize: 180, fontWeight: 900, color: '#ffffff', textShadow: '0 6px 30px rgba(0,0,0,0.6)'}}>
        {pop.toFixed(1)}M
      </div>
      <div style={{fontSize: 44, fontWeight: 700, color: '#ffd60a', letterSpacing: 2}}>
        VIDMAP RENDER FARM — SMOKE TEST — frame {f}
      </div>
      <div style={{position: 'absolute', bottom: 120, left: 200, width: 1520, height: 10, background: '#223344'}} />
      <div style={{position: 'absolute', bottom: 120, left: 200, width: bar, height: 10, background: '#e22634'}} />
    </AbsoluteFill>
  );
};
