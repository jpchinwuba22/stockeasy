import React from 'react';
import {AbsoluteFill, Img, interpolate, random, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

export const GOLD = '#ffcd60';
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
export const easeOut = Easing.bezier(0.16, 1, 0.3, 1);

/** rising gold dust, deterministic */
export const GoldDust: React.FC<{n?: number; seed?: string; opacity?: number}> = ({n = 70, seed = 'd', opacity = 0.85}) => {
  const f = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const t = f / fps;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {new Array(n).fill(0).map((_, i) => {
        const x = random(seed + 'x' + i) * width + 12 * Math.sin(t * 1.3 + i);
        const sp = 30 + random(seed + 's' + i) * 80;
        const y = (((random(seed + 'y' + i) * height - sp * t) % height) + height) % height;
        const r = 1.5 + random(seed + 'r' + i) * 3.5;
        const a = (0.45 + 0.55 * Math.sin(t * 3 + i * 1.7)) * opacity;
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, width: r * 2, height: r * 2, borderRadius: '50%',
            background: 'radial-gradient(circle, #fff6d8 0%, #ffcf6a 45%, rgba(255,190,80,0) 75%)', opacity: a}} />
        );
      })}
    </AbsoluteFill>
  );
};

/** one diagonal light sweep across the frame */
export const LightSweep: React.FC<{start: number; dur: number; strength?: number}> = ({start, dur, strength = 0.35}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [start, start + dur], [-0.4, 1.4], clamp);
  if (p <= -0.39 || p >= 1.39) return null;
  return (
    <AbsoluteFill style={{mixBlendMode: 'screen', pointerEvents: 'none',
      background: `linear-gradient(115deg, rgba(255,240,210,0) ${p * 100 - 12}%, rgba(255,240,210,${strength}) ${p * 100}%, rgba(255,240,210,0) ${p * 100 + 12}%)`}} />
  );
};

/** four-point star glint */
export const Glint: React.FC<{x: number; y: number; at: number; size?: number}> = ({x, y, at, size = 90}) => {
  const f = useCurrentFrame();
  const s = Math.sin(Math.PI * interpolate(f, [at, at + 14], [0, 1], clamp));
  if (s <= 0.01) return null;
  const bar = (w: number, h: number, rot: number) => (
    <div style={{position: 'absolute', left: x - w / 2, top: y - h / 2, width: w, height: h, borderRadius: h,
      transform: `rotate(${rot}deg)`, background: 'radial-gradient(ellipse, #fffbea 0%, rgba(255,230,170,0.7) 35%, rgba(255,220,150,0) 70%)'}} />
  );
  return (
    <AbsoluteFill style={{opacity: s, mixBlendMode: 'screen'}}>
      {bar(size * s, 6, 0)}
      {bar(size * s, 6, 90)}
      {bar(size * 0.45 * s, 4, 45)}
      {bar(size * 0.45 * s, 4, -45)}
      <div style={{position: 'absolute', left: x - 14, top: y - 14, width: 28, height: 28, borderRadius: '50%',
        background: 'radial-gradient(circle, #fff 0%, rgba(255,240,200,0) 70%)'}} />
    </AbsoluteFill>
  );
};

/** orange burst: real orange slices + juice drops exploding from a point */
export const OrangeBurst: React.FC<{at: number; cx: number; cy: number; n?: number; seed?: string; fadeAt?: number}> = ({at, cx, cy, n = 16, seed = 'b', fadeAt = 30}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const u = (f - at) / fps;
  if (u < 0) return null;
  const fade = interpolate(f - at, [fadeAt, fadeAt + 12], [1, 0], clamp);
  if (fade <= 0) return null;
  return (
    <AbsoluteFill style={{pointerEvents: 'none', opacity: fade}}>
      {new Array(n).fill(0).map((_, i) => {
        const ang = (i / n) * Math.PI * 2 + (random(seed + 'a' + i) - 0.5) * 0.5;
        const spd = 450 + random(seed + 's' + i) * 550;
        const d = spd * (1 - Math.exp(-u * 3.4));
        const sz = 110 + random(seed + 'z' + i) * 130;
        const sc = interpolate(u, [0, 0.3], [0.3, 1], {...clamp, easing: easeOut});
        const rot = (random(seed + 'r' + i) - 0.5) * 500 * u;
        const blur = interpolate(u, [0, 0.25], [4, 0], clamp) + (i % 4 === 0 ? 2 : 0);
        return (
          <Img key={i} src={staticFile('orange_slice.png')} style={{position: 'absolute', width: sz, height: sz,
            left: cx + Math.cos(ang) * d - sz / 2, top: cy + Math.sin(ang) * d + 240 * u * u - sz / 2,
            transform: `scale(${sc}) rotate(${rot}deg)`, filter: `blur(${blur}px) drop-shadow(0 10px 18px rgba(120,50,0,0.35))`}} />
        );
      })}
      {new Array(n * 3).fill(0).map((_, i) => {
        const ang = random(seed + 'ja' + i) * Math.PI * 2;
        const spd = 250 + random(seed + 'js' + i) * 600;
        const d = spd * (1 - Math.exp(-u * 3.0));
        const r = 4 + random(seed + 'jr' + i) * 9;
        return (
          <div key={'j' + i} style={{position: 'absolute', width: r * 2, height: r * 2.3, borderRadius: '50%',
            left: cx + Math.cos(ang) * d - r, top: cy + Math.sin(ang) * d + 420 * u * u - r,
            background: 'radial-gradient(circle at 35% 30%, #fff1d6 0%, #ffb444 35%, #f07c14 80%)', opacity: 0.92}} />
        );
      })}
      <AbsoluteFill style={{background: '#fff3df', opacity: Math.exp(-u / 0.1) * 0.85}} />
    </AbsoluteFill>
  );
};
