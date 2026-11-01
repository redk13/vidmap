import React, {useEffect, useMemo, useState} from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame, delayRender, continueRender, interpolate, Easing} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import * as THREE from 'three';

// ---------- deterministic value noise ----------
const mulberry = (seed: number) => {
  let s = seed | 0;
  return () => {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};
const makeNoise = (seed: number, N: number) => {
  const rnd = mulberry(seed);
  const g = new Float32Array(N * N);
  for (let i = 0; i < N * N; i++) g[i] = rnd() * 2 - 1;
  const sm = (x: number) => x * x * (3 - 2 * x);
  return (u: number, v: number) => {
    const x = Math.min(Math.max(u, 0), 0.999) * (N - 1);
    const y = Math.min(Math.max(v, 0), 0.999) * (N - 1);
    const x0 = Math.floor(x), y0 = Math.floor(y);
    const x1 = Math.min(x0 + 1, N - 1), y1 = Math.min(y0 + 1, N - 1);
    const fx = sm(x - x0), fy = sm(y - y0);
    const a = g[y0 * N + x0], b = g[y0 * N + x1], c = g[y1 * N + x0], d = g[y1 * N + x1];
    return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy;
  };
};

// ---------- crumpling sheet ----------
const Sheet: React.FC<{
  tex: THREE.Texture; w: number; h: number; seed: number;
  open: number; ampMax: number; rest: number;
  pos: [number, number, number]; rotZ?: number;
}> = ({tex, w, h, seed, open, ampMax, rest, pos, rotZ = 0}) => {
  const seg = 56;
  const geo = useMemo(() => new THREE.PlaneGeometry(w, h, seg, seg), [w, h]);
  const base = useMemo(() => Float32Array.from(geo.attributes.position.array as Float32Array), [geo]);
  const noises = useMemo(
    () => [makeNoise(seed, 9), makeNoise(seed + 7, 21), makeNoise(seed + 13, 38), makeNoise(seed + 29, 15), makeNoise(seed + 41, 15)],
    [seed]
  );
  const amp = ampMax + (rest - ampMax) * open;
  const s = 0.3 + 0.7 * open;
  const attr = geo.attributes.position as THREE.BufferAttribute;
  const arr = attr.array as Float32Array;
  for (let i = 0; i < arr.length; i += 3) {
    const ox = base[i], oy = base[i + 1];
    const u = ox / w + 0.5, v = oy / h + 0.5;
    const z = (noises[0](u, v) * 0.62 + noises[1](u, v) * 0.3 + noises[2](u, v) * 0.13) * amp;
    const dx = noises[3](u, v) * amp * 0.5;
    const dy = noises[4](u, v) * amp * 0.5;
    arr[i] = ox * s + dx;
    arr[i + 1] = oy * s + dy;
    arr[i + 2] = z;
  }
  attr.needsUpdate = true;
  geo.computeVertexNormals();
  return (
    <mesh geometry={geo} position={pos} rotation={[0, 0, rotZ]}>
      <meshStandardMaterial map={tex} transparent alphaTest={0.3} side={THREE.DoubleSide} roughness={0.92} metalness={0} />
    </mesh>
  );
};

// ---------- main shot ----------
export const LabCrumple: React.FC = () => {
  const frame = useCurrentFrame();
  const [textures, setTextures] = useState<null | {paper: THREE.Texture; strip: THREE.Texture}>(null);
  const [handle] = useState(() => delayRender('crumple-textures'));
  useEffect(() => {
    const l = new THREE.TextureLoader();
    Promise.all([l.loadAsync(staticFile('crump-paper.png')), l.loadAsync(staticFile('crump-strip.png'))]).then(([p, st]) => {
      p.colorSpace = THREE.SRGBColorSpace;
      st.colorSpace = THREE.SRGBColorSpace;
      p.anisotropy = 8; st.anisotropy = 8;
      setTextures({paper: p, strip: st});
      continueRender(handle);
    });
  }, [handle]);

  const io = Easing.inOut(Easing.cubic);
  // openness: wad -> flat -> wad (strip slightly delayed)
  const oPaper = interpolate(frame, [46, 140, 258, 320], [0, 1, 1, 0], {easing: io, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const oStrip = interpolate(frame, [64, 152, 250, 312], [0, 1, 1, 0], {easing: io, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  // fly in / out
  const pin = interpolate(frame, [0, 54], [0, 1], {easing: Easing.out(Easing.cubic), extrapolateRight: 'clamp'});
  const pout = interpolate(frame, [306, 358], [0, 1], {easing: Easing.in(Easing.cubic), extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const gx = (-7.6) * (1 - pin) + 8.2 * pout;
  const gy = 3.4 * (1 - pin) - 3.1 * pout;
  // tumble rotations settle by f~135, return while leaving
  const rin = interpolate(frame, [0, 135], [1, 0], {easing: Easing.out(Easing.cubic), extrapolateRight: 'clamp'});
  const rout = interpolate(frame, [296, 360], [0, 1], {easing: Easing.in(Easing.quad), extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const rx = 2.1 * rin - 1.6 * rout;
  const ry = -2.4 * rin + 2.0 * rout;
  const rz = 1.7 * rin - 1.2 * rout;
  // gentle push while readable (camera always traveling)
  const push = interpolate(frame, [120, 280], [1, 1.07], {easing: io, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const bgScale = interpolate(frame, [0, 360], [1.06, 1.15]);

  return (
    <AbsoluteFill style={{background: '#0c0e10', overflow: 'hidden'}}>
      <Img
        src={staticFile('city-bg.jpg')}
        style={{position: 'absolute', width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${bgScale})`, filter: 'blur(13px) brightness(0.72) saturate(0.8)'}}
      />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 48%, rgba(0,0,0,0.45) 100%)'}} />
      {textures ? (
        <ThreeCanvas width={1920} height={1080} camera={{fov: 33, position: [0, 0, 8]}}>
          <ambientLight intensity={0.78} />
          <directionalLight position={[3, 5, 6]} intensity={1.05} />
          <directionalLight position={[-4, -2, 5]} intensity={0.22} />
          <group position={[gx, gy, 0]} rotation={[rx, ry, rz]} scale={push}>
            <Sheet tex={textures.paper} w={5.45} h={2.44} seed={5} open={oPaper} ampMax={1.35} rest={0.045} pos={[0.1, -0.5, 0]} rotZ={-0.012} />
            <Sheet tex={textures.strip} w={3.95} h={1.77} seed={23} open={oStrip} ampMax={1.1} rest={0.04} pos={[-1.2, 1.08, 0.26]} rotZ={0.03} />
          </group>
        </ThreeCanvas>
      ) : null}
    </AbsoluteFill>
  );
};
