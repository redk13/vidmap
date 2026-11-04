import meta from './satmeta2.json';

export const lonLatToPx2 = (lon: number, lat: number): [number, number] => {
  const world = 256 * Math.pow(2, meta.z);
  const x = ((lon + 180) / 360) * world - meta.x0 * 256;
  const r = (lat * Math.PI) / 180;
  const y = ((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2) * world - meta.y0 * 256;
  return [x, y];
};
export const SAT2_W = meta.w, SAT2_H = meta.h;
