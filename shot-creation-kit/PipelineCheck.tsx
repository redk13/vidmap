import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';

// Diagnostic only: confirms that a user-provided GitHub repository can render Remotion.
// Replace/add a real composition after the pipeline succeeds; never present this as a creative shot.
export const PipelineCheck: React.FC = () => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [0, 29], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{backgroundColor: '#101820', color: 'white', fontFamily: 'Arial, sans-serif', alignItems: 'center', justifyContent: 'center'}}>
      <div style={{fontSize: 64, fontWeight: 700}}>GitHub Actions render OK</div>
      <div style={{marginTop: 28, fontSize: 30, color: '#b9c7d4'}}>Pipeline diagnostic — not a creative sample</div>
      <div style={{marginTop: 52, width: 720, height: 12, backgroundColor: '#2b3b49'}}>
        <div style={{width: `${progress * 100}%`, height: '100%', backgroundColor: '#e7b62b'}} />
      </div>
      <div style={{marginTop: 24, fontSize: 26, color: '#b9c7d4'}}>Frame {frame} / 29</div>
    </AbsoluteFill>
  );
};
