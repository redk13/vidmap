import React, {useMemo} from 'react';
import {geoMercator, geoPath} from 'd3-geo';
import {feature} from 'topojson-client';
import type {FeatureCollection, Feature} from 'geojson';
import japanTopo from '../data/japan.json';

export type PrefStyle = {fill: string; stroke?: string; strokeWidth?: number; glow?: boolean};
type Props = {
  width: number; height: number;
  styleFor: (id: number) => PrefStyle;              // JIS 1..47 (Tokyo 13, Okinawa 47)
  okinawaInset?: boolean;                           // Okinawa in a framed inset (bottom-left)
  children?: (centroidOf: (id: number) => [number, number]) => React.ReactNode;
};

export const JapanMap: React.FC<Props> = ({width, height, styleFor, okinawaInset = true, children}) => {
  const M = useMemo(() => {
    const topo = japanTopo as any;
    const fc = feature(topo, topo.objects.japan) as unknown as FeatureCollection;
    // Tokyo (13): keep mainland polygon only — drop Izu/Ogasawara island trail
    for (const f of fc.features) {
      const p: any = f;
      if (p.properties.id === 13 && p.geometry.type === 'MultiPolygon') {
        let best = p.geometry.coordinates[0];
        for (const poly of p.geometry.coordinates) {
          if (JSON.stringify(poly).length > JSON.stringify(best).length) best = poly;
        }
        p.geometry = {type: 'Polygon', coordinates: best};
      }
    }
    const main = fc.features.filter((f: any) => f.properties.id !== 47);
    const oki = fc.features.filter((f: any) => f.properties.id === 47);
    const mainFc = {type: 'FeatureCollection', features: main} as FeatureCollection;
    // fit inset to Okinawa's main island only (geometry stays complete)
    const okiMain = JSON.parse(JSON.stringify(oki[0])) as any;
    if (okiMain.geometry.type === 'MultiPolygon') {
      let best = okiMain.geometry.coordinates[0];
      for (const poly of okiMain.geometry.coordinates) {
        if (JSON.stringify(poly).length > JSON.stringify(best).length) best = poly;
      }
      okiMain.geometry = {type: 'Polygon', coordinates: best};
    }
    const okiFc = {type: 'FeatureCollection', features: [okiMain]} as FeatureCollection;
    const proj = geoMercator().fitExtent([[width * 0.10, height * 0.07], [width * 0.96, height * 0.95]], mainFc as any);
    const path = geoPath(proj);
    const box = {x: width * 0.065, y: height * 0.615, w: width * 0.165, h: height * 0.30};
    const projO = geoMercator().fitExtent([[box.x + 14, box.y + 14], [box.x + box.w - 14, box.y + box.h - 14]], okiFc as any);
    const pathO = geoPath(projO);
    const cents = new Map<number, [number, number]>();
    for (const f of main) cents.set((f as any).properties.id, path.centroid(f as any) as [number, number]);
    cents.set(47, pathO.centroid(okiMain as any) as [number, number]);
    return {main: main as Feature[], oki: oki as Feature[], path, pathO, cents, box};
  }, [width, height]);

  const render = (f: Feature, p: (x: any) => string | null) => {
    const id = (f as any).properties.id as number;
    const s = styleFor(id);
    return <path key={id} d={p(f as any) ?? ''} fill={s.fill}
      stroke={s.stroke ?? '#0a1420'} strokeWidth={s.strokeWidth ?? 1}
      filter={s.glow ? 'url(#prefGlow)' : undefined} />;
  };

  return (
    <svg width={width} height={height} style={{position: 'absolute', top: 0, left: 0}}>
      <defs>
        <filter id="prefGlow" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="10" result="b"/>
          <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <clipPath id="okiClip">
          <rect x={M.box.x} y={M.box.y} width={M.box.w} height={M.box.h} rx={12}/>
        </clipPath>
        <radialGradient id="halo">
          <stop offset="0%" stopColor="#4f9dff" stopOpacity="0.85"/>
          <stop offset="45%" stopColor="#2f86ff" stopOpacity="0.35"/>
          <stop offset="100%" stopColor="#2f86ff" stopOpacity="0"/>
        </radialGradient>
      </defs>
      {M.main.map((f) => render(f, M.path as any))}
      {okinawaInset && (
        <g>
          <rect x={M.box.x} y={M.box.y} width={M.box.w} height={M.box.h} rx={12}
            fill="rgba(13,26,40,0.85)" stroke="#2c4258" strokeWidth={2}/>
          <g clipPath="url(#okiClip)">
            {M.oki.map((f) => {
              const s = styleFor(47);
              return <path key="oki47" d={(M.pathO as any)(f as any) ?? ''} fill={s.fill}
                stroke={s.fill === '#1d2b3a' ? '#3a5570' : s.fill} strokeWidth={3}/>;
            })}
          </g>
          <text x={M.box.x + 16} y={M.box.y + M.box.h - 14} fontSize={22} fontWeight={700}
            fill="#6d8aa6" fontFamily="sans-serif" letterSpacing={2}>OKINAWA</text>
        </g>
      )}
      {children ? children((id) => M.cents.get(id) ?? [0, 0]) : null}
    </svg>
  );
};
