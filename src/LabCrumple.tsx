import React, {useEffect, useMemo, useState} from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame, delayRender, continueRender, interpolate, Easing} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import * as THREE from 'three';

// Professional pipeline: Blender cloth-sim crumple (central attractor + turbulence,
// self-collision), baked vertex animation played back in three.js. Un-crumple = reversed sim.
const SIM_RANGE = 30; // sim frames 0..30 = flat -> wad

type SimData = {pos: Float32Array; faces: Uint32Array; nV: number; frames: number};

const useSim = (): SimData | null => {
  const [data, setData] = useState<SimData | null>(null);
  const [handle] = useState(() => delayRender('sim-data'));
  useEffect(() => {
    Promise.all([
      fetch(staticFile('crump.bin')).then((r) => r.arrayBuffer()),
      fetch(staticFile('crump-meta.json')).then((r) => r.json()),
    ]).then(([buf, meta]) => {
      setData({pos: new Float32Array(buf), faces: Uint32Array.from(meta.faces), nV: meta.nV, frames: meta.frames});
      continueRender(handle);
    });
  }, [handle]);
  return data;
};

const Sheet: React.FC<{
  sim: SimData; tex: THREE.Texture; simIdx: number; scale: number;
  pos: [number, number, number]; rotZ?: number; flip?: boolean;
}> = ({sim, tex, simIdx, scale, pos, rotZ = 0, flip}) => {
  const geo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setIndex(new THREE.BufferAttribute(sim.faces, 1));
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(sim.nV * 3), 3));
    const uv = new Float32Array(sim.nV * 2);
    for (let i = 0; i < sim.nV; i++) {
      const x = sim.pos[i * 3], y = sim.pos[i * 3 + 1]; // frame 0 = flat
      uv[i * 2] = x / 1.12 + 0.5;
      uv[i * 2 + 1] = y / 0.5 + 0.5;
    }
    g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    return g;
  }, [sim]);
  // lerp between baked sim frames
  const s = Math.min(Math.max(simIdx, 0), sim.frames - 1.001);
  const i0 = Math.floor(s), t = s - i0;
  const attr = geo.attributes.position as THREE.BufferAttribute;
  const arr = attr.array as Float32Array;
  const a = sim.pos.subarray(i0 * sim.nV * 3, (i0 + 1) * sim.nV * 3);
  const b = sim.pos.subarray((i0 + 1) * sim.nV * 3, (i0 + 2) * sim.nV * 3);
  for (let i = 0; i < arr.length; i++) arr[i] = a[i] + (b[i] - a[i]) * t;
  attr.needsUpdate = true;
  geo.computeVertexNormals();
  if (flip) {
    tex.center.set(0.5, 0.5);
    tex.rotation = Math.PI;
  }
  return (
    <mesh geometry={geo} position={pos} rotation={[0, 0, rotZ + (flip ? Math.PI : 0)]} scale={scale}>
      <meshStandardMaterial map={tex} transparent alphaTest={0.25} side={THREE.DoubleSide} roughness={0.9} metalness={0} />
    </mesh>
  );
};

export const LabCrumple: React.FC = () => {
  const frame = useCurrentFrame();
  const sim = useSim();
  const [textures, setTextures] = useState<null | {paper: THREE.Texture; strip: THREE.Texture}>(null);
  const [handle] = useState(() => delayRender('crumple-textures'));
  useEffect(() => {
    const l = new THREE.TextureLoader();
    Promise.all([l.loadAsync(staticFile('crump-paper.png')), l.loadAsync(staticFile('crump-strip.png'))]).then(([p, st]) => {
      p.colorSpace = THREE.SRGBColorSpace; st.colorSpace = THREE.SRGBColorSpace;
      p.anisotropy = 8; st.anisotropy = 8;
      setTextures({paper: p, strip: st});
      continueRender(handle);
    });
  }, [handle]);

  const io = Easing.inOut(Easing.cubic);
  // FAST open/close in place, like hands opening then re-crumpling the paper.
  // appear f0-5 (wad pops in) | open f6-32 | hold | close f196-222 (exact mirror) | vanish f224-234
  const oPaper = interpolate(frame, [6, 32, 196, 222], [0, 1, 1, 0], {easing: io, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const oStrip = interpolate(frame, [12, 38, 190, 216], [0, 1, 1, 0], {easing: io, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const simPaper = (1 - oPaper) * SIM_RANGE;
  const simStrip = (1 - oStrip) * SIM_RANGE;

  // pop in / pop out, in place (no floating across the screen)
  const aIn = interpolate(frame, [0, 6], [0, 1], {easing: Easing.out(Easing.quad), extrapolateRight: 'clamp'});
  const aOut = interpolate(frame, [224, 234], [1, 0], {easing: Easing.in(Easing.quad), extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const appear = Math.min(aIn, aOut);
  const gx = 0;
  const gy = 0.08 * (1 - aIn); // tiny settle
  // small settle twist while opening, mirrored while closing — no tumbling flight
  const rz = 0.22 * (1 - oPaper) * (frame < 120 ? 1 : -1);
  const rx = 0.1 * (1 - oPaper);
  const ry = 0;
  const push = interpolate(frame, [40, 200], [1, 1.06], {easing: io, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const scaleAll = push * (0.85 + 0.15 * appear);
  const bgScale = interpolate(frame, [0, 240], [1.06, 1.13]);

  return (
    <AbsoluteFill style={{background: '#0c0e10', overflow: 'hidden'}}>
      <Img src={staticFile('city-bg.jpg')} style={{position: 'absolute', width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${bgScale})`, filter: 'blur(13px) brightness(0.72) saturate(0.8)'}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 48%, rgba(0,0,0,0.45) 100%)'}} />
      {textures && sim ? (
        <ThreeCanvas width={1920} height={1080} camera={{fov: 33, position: [0, 0, 8]}}>
          <ambientLight intensity={0.8} />
          <directionalLight position={[3, 5, 6]} intensity={1.0} />
          <directionalLight position={[-4, -2, 5]} intensity={0.22} />
          <group position={[gx, gy, 0]} rotation={[rx, ry, rz]} scale={scaleAll}>
            <Sheet sim={sim} tex={textures.paper} simIdx={simPaper} scale={4.86} pos={[0.1, -0.5, 0]} rotZ={-0.012} />
            <Sheet sim={sim} tex={textures.strip} simIdx={simStrip} scale={3.53} pos={[-1.2, 1.08, 0.3]} rotZ={0.03} flip />
          </group>
        </ThreeCanvas>
      ) : null}
    </AbsoluteFill>
  );
};
