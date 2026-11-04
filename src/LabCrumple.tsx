import React, {useEffect, useMemo, useState} from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame, delayRender, continueRender, interpolate, Easing} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import * as THREE from 'three';

// Blender JOINT cloth sim: paper + strip crumple INTO EACH OTHER as one wad
// (cloth-cloth collision), baked vertex animation. Open = reversed sim.
const SIM_RANGE = 28;
const WORLD = 4.6;

type SimData = {pos: Float32Array; faces: Uint32Array; nV: number; frames: number};

const useAssets = () => {
  const [out, setOut] = useState<null | {s1: SimData; s2: SimData; t1: THREE.Texture; t2: THREE.Texture}>(null);
  const [handle] = useState(() => delayRender('crumple-assets'));
  useEffect(() => {
    const l = new THREE.TextureLoader();
    Promise.all([
      fetch(staticFile('crump1.bin')).then((r) => r.arrayBuffer()),
      fetch(staticFile('crump1-meta.json')).then((r) => r.json()),
      fetch(staticFile('crump2.bin')).then((r) => r.arrayBuffer()),
      fetch(staticFile('crump2-meta.json')).then((r) => r.json()),
      l.loadAsync(staticFile('crump-paper.png')),
      l.loadAsync(staticFile('crump-strip.png')),
    ]).then(([b1, m1, b2, m2, t1, t2]) => {
      [t1, t2].forEach((t) => {
        t.colorSpace = THREE.SRGBColorSpace;
        t.anisotropy = 8;
      });
      setOut({
        s1: {pos: new Float32Array(b1), faces: Uint32Array.from(m1.faces), nV: m1.nV, frames: m1.frames},
        s2: {pos: new Float32Array(b2), faces: Uint32Array.from(m2.faces), nV: m2.nV, frames: m2.frames},
        t1, t2,
      });
      continueRender(handle);
    });
  }, [handle]);
  return out;
};

const Sheet: React.FC<{sim: SimData; tex: THREE.Texture; simIdx: number; opacity: number}> = ({sim, tex, simIdx, opacity}) => {
  const geo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setIndex(new THREE.BufferAttribute(sim.faces, 1));
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(sim.nV * 3), 3));
    // UVs from flat frame 0 bbox
    let minX = 1e9, maxX = -1e9, minY = 1e9, maxY = -1e9;
    for (let i = 0; i < sim.nV; i++) {
      const x = sim.pos[i * 3], y = sim.pos[i * 3 + 1];
      if (x < minX) minX = x; if (x > maxX) maxX = x;
      if (y < minY) minY = y; if (y > maxY) maxY = y;
    }
    const uv = new Float32Array(sim.nV * 2);
    for (let i = 0; i < sim.nV; i++) {
      uv[i * 2] = (sim.pos[i * 3] - minX) / (maxX - minX);
      uv[i * 2 + 1] = (sim.pos[i * 3 + 1] - minY) / (maxY - minY);
    }
    g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    return g;
  }, [sim]);
  const s = Math.min(Math.max(simIdx, 0), sim.frames - 1.001);
  const i0 = Math.floor(s), t = s - i0;
  const attr = geo.attributes.position as THREE.BufferAttribute;
  const arr = attr.array as Float32Array;
  const a = sim.pos.subarray(i0 * sim.nV * 3, (i0 + 1) * sim.nV * 3);
  const b = sim.pos.subarray((i0 + 1) * sim.nV * 3, (i0 + 2) * sim.nV * 3);
  for (let i = 0; i < arr.length; i++) arr[i] = a[i] + (b[i] - a[i]) * t;
  attr.needsUpdate = true;
  geo.computeVertexNormals();
  return (
    <mesh geometry={geo} castShadow receiveShadow>
      <meshStandardMaterial map={tex} bumpMap={tex} bumpScale={0.006} transparent opacity={opacity} alphaTest={0.2} side={THREE.DoubleSide} roughness={0.88} metalness={0} />
    </mesh>
  );
};

const GRAIN =
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="420" height="420"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="7"/><feColorMatrix type="saturate" values="0"/></filter><rect width="420" height="420" filter="url(#n)" opacity="0.5"/></svg>`
  );

export const LabCrumple: React.FC = () => {
  const frame = useCurrentFrame();
  const assets = useAssets();
  const io = Easing.inOut(Easing.cubic);

  // appear from nothing f0-6 | fast open f8-34 | hold | fast close f196-222 | vanish f224-232
  const o = interpolate(frame, [8, 34, 196, 222], [0, 1, 1, 0], {easing: io, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const simIdx = (1 - o) * SIM_RANGE;
  const aIn = interpolate(frame, [0, 6], [0, 1], {easing: Easing.out(Easing.quad), extrapolateRight: 'clamp'});
  const aOut = interpolate(frame, [224, 232], [1, 0], {easing: Easing.in(Easing.quad), extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const appear = Math.min(aIn, aOut);
  // small settle twist while opening, mirrored while closing
  const rz = 0.2 * (1 - o) * (frame < 120 ? 1 : -1);
  const rx = 0.09 * (1 - o);
  const push = interpolate(frame, [40, 200], [1, 1.06], {easing: io, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const scaleAll = push * (0.88 + 0.12 * appear);
  const bgScale = interpolate(frame, [0, 240], [1.06, 1.13]);

  return (
    <AbsoluteFill style={{background: '#0c0e10', overflow: 'hidden'}}>
      <Img src={staticFile('city-bg.jpg')} style={{position: 'absolute', width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${bgScale})`, filter: 'blur(13px) brightness(0.72) saturate(0.8)'}} />
      {assets ? (
        <ThreeCanvas shadows width={1920} height={1080} camera={{fov: 33, position: [0, 0, 8]}}>
          <ambientLight intensity={0.55} />
          <directionalLight
            position={[3.5, 5, 6]}
            intensity={1.35}
            castShadow
            shadow-mapSize-width={1024}
            shadow-mapSize-height={1024}
            shadow-camera-left={-5}
            shadow-camera-right={5}
            shadow-camera-top={5}
            shadow-camera-bottom={-5}
            shadow-camera-near={1}
            shadow-camera-far={20}
            shadow-bias={-0.0004}
            shadow-normalBias={0.05}
          />
          <directionalLight position={[-4, -2, 5]} intensity={0.18} />
          <group position={[0, -0.28, 0]} rotation={[rx, 0, rz]} scale={scaleAll * WORLD}>
            <Sheet sim={assets.s1} tex={assets.t1} simIdx={simIdx} opacity={appear} />
            <Sheet sim={assets.s2} tex={assets.t2} simIdx={simIdx} opacity={appear} />
          </group>
        </ThreeCanvas>
      ) : null}
      <AbsoluteFill style={{backgroundImage: `url("${GRAIN}")`, opacity: 0.05, mixBlendMode: 'overlay', pointerEvents: 'none'}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 48%, rgba(0,0,0,0.45) 100%)', pointerEvents: 'none'}} />
    </AbsoluteFill>
  );
};
