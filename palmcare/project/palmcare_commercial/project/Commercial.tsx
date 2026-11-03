import React from 'react';
import {AbsoluteFill, Img, interpolate, OffthreadVideo, Sequence, spring, staticFile, useCurrentFrame, Easing} from 'remotion';
import {loadFonts} from './fonts';

loadFonts();

/** PalmCare 10-second luxury commercial (silent, 30 fps, 1080x1920).
 * Backgrounds: the two Flow clips (batch 1 = golden sweep / arched stage, batch 2 = gold silk over a mirror floor),
 * prepared as 30 fps plates. Foreground: the 11 ORIGINAL product photographs, locked (native proportions, never
 * regenerated, rotated or warped), animated with varied camera moves, contact shadows, reflections, a light sweep
 * across each label, golden liquid sweeps on every cut, a liquid wipe between the two batches, the collection
 * showcase and the brand frame. */
export const FPS = 30;
const S = (s: number) => Math.round(s * FPS);
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

type P = {img: string; ar: number; kind: 'bottle' | 'pack' | 'box'};
const PR: P[] = [
  {img: 'milky.png', ar: 762 / 1924, kind: 'bottle'},
  {img: 'cacao.png', ar: 702 / 1908, kind: 'bottle'},
  {img: 'citrus_cut.png', ar: 488 / 1390, kind: 'bottle'},
  {img: 'molecular_cut.png', ar: 471 / 1384, kind: 'bottle'},
  {img: 'tropical_cut.png', ar: 495 / 1362, kind: 'bottle'},
  {img: 'dermalight_cut.png', ar: 509 / 1316, kind: 'bottle'},
  {img: 'vitac_real_final.png', ar: 710 / 1248, kind: 'pack'},
  {img: 'n10_real_final.png', ar: 710 / 1248, kind: 'pack'},
  {img: 'dermaluxe_box_final.png', ar: 710 / 1248, kind: 'pack'},
  {img: 'glowshield_box_flat.png', ar: 583 / 1295, kind: 'pack'},
  {img: 'box_straight.png', ar: 1100 / 855, kind: 'box'},
];
// reveal windows (seconds) from the brief
const T = [0.4, 1.05, 1.65, 2.25, 2.85, 3.45, 4.05, 4.65, 5.15, 5.85, 6.55, 7.25, 7.95];
const WIN = [...T.slice(0, 7).map((s, i) => [s, T[i + 1]]), ...T.slice(8, 12).map((s, i) => [s, T[i + 9]])];
const GROUP = [7.95, 9.4], CLOSE = [9.4, 10.0];
export const TOTAL = S(10.0);
// camera move per product: [enter dx, enter dy, scale0, scale1, drift dx]
const MOVES: [number, number, number, number, number][] = [
  [0, 60, 0.9, 1.0, 0], [420, 0, 1.0, 1.03, -20], [0, 380, 0.97, 1.02, 0], [-420, 0, 1.0, 1.03, 20], [0, 0, 1.14, 1.0, 0],
  [260, 0, 0.96, 1.02, -40], [0, -360, 1.0, 1.03, 0],
  [0, 60, 0.9, 1.0, 0], [420, 0, 1.0, 1.03, -20], [0, 380, 0.97, 1.02, 0], [0, 0, 1.14, 1.0, 0],
];
const hasFloor = (i: number) => i !== 5 && i !== 6;            // batch-1 bubbles section has no floor

const sizeOf = (p: P, s = 1) => {
  const h = (p.kind === 'bottle' ? 1150 : p.kind === 'pack' ? 1060 : 880 / p.ar) * s;
  return {h, w: h * p.ar};
};

const Prod: React.FC<{p: P; x: number; base: number; s?: number; floor?: boolean; sweep?: number}> = ({p, x, base, s = 1, floor = true, sweep = -1}) => {
  const {w, h} = sizeOf(p, s);
  const r = p.kind === 'bottle' ? 0 : 6 * s;
  const mask = p.kind === 'bottle' ? {WebkitMaskImage: `url(${staticFile('p/' + p.img)})`, WebkitMaskSize: '100% 100%'} : {};
  return (
    <>
      {floor && <div style={{position: 'absolute', left: x - w * 0.62, top: base - 16 * s, width: w * 1.24, height: 32 * s, borderRadius: '50%',
        background: 'radial-gradient(ellipse, rgba(70,48,20,0.5), rgba(70,48,20,0) 70%)'}} />}
      {floor && <div style={{position: 'absolute', left: x - w / 2, top: base + 2, width: w, height: h * 0.3, overflow: 'hidden', opacity: 0.22,
        WebkitMaskImage: 'linear-gradient(180deg, rgba(0,0,0,1), rgba(0,0,0,0))'}}>
        <Img src={staticFile('p/' + p.img)} style={{width: w, height: h, display: 'block', transform: 'scaleY(-1)', marginTop: -h * 0.7, borderRadius: r}} />
      </div>}
      <div style={{position: 'absolute', left: x - w / 2, top: base - h, width: w, height: h,
        filter: `drop-shadow(0 ${18 * s}px ${26 * s}px rgba(70,46,18,0.28))${floor ? '' : ` drop-shadow(0 0 ${30 * s}px rgba(255,236,190,0.55))`}`}}>
        <Img src={staticFile('p/' + p.img)} style={{width: w, height: h, display: 'block', borderRadius: r}} />
        <div style={{position: 'absolute', inset: 0, borderRadius: r, mixBlendMode: 'soft-light',
          background: 'linear-gradient(100deg, rgba(255,250,235,0.35) 0%, rgba(255,255,255,0) 38%, rgba(0,0,0,0) 72%, rgba(60,40,10,0.18) 100%)', ...mask} as React.CSSProperties} />
        {sweep > -0.3 && sweep < 1.3 && <div style={{position: 'absolute', inset: 0, borderRadius: r, mixBlendMode: 'screen',
          background: `linear-gradient(108deg, rgba(255,255,255,0) ${sweep * 100 - 10}%, rgba(255,246,222,0.5) ${sweep * 100}%, rgba(255,255,255,0) ${sweep * 100 + 10}%)`,
          ...mask} as React.CSSProperties} />}
      </div>
    </>
  );
};

/** one product reveal: varied entrance (slide / rise / drop / pull-back), gentle continuous camera, exit drift */
const Reveal: React.FC<{i: number; len: number}> = ({i, len}) => {
  const f = useCurrentFrame();
  const p = PR[i];
  const [dx, dy, s0, s1, drift] = MOVES[i];
  const e = Easing.bezier(0.16, 1, 0.3, 1);
  const inP = interpolate(f, [0, 8], [0, 1], {...cl, easing: e});
  const prog = interpolate(f, [0, len], [0, 1], cl);
  const sc = s0 + (s1 - s0) * interpolate(f, [0, len], [0, 1], {...cl, easing: Easing.out(Easing.quad)});
  // exit: the last 4 frames continue out, motion-blurred, under the gold sweep (no product ever pops off)
  const outP = interpolate(f, [len - 4, len], [0, 1], {...cl, easing: Easing.in(Easing.cubic)});
  const ex = dx !== 0 ? -Math.sign(dx) * 320 : (i % 2 ? 300 : -300);
  const x = 540 + dx * (1 - inP) + drift * prog + ex * outP;
  const y = dy * (1 - inP) - (dy !== 0 ? Math.sign(dy) * 120 * outP : 0);
  const vel = Math.hypot(dx, dy) * (inP < 1 ? (1 - inP) * 0.12 : 0) + outP * 14;
  const base = p.kind === 'box' ? 1420 : 1560;
  const sweep = interpolate(f, [5, len - 2], [-0.3, 1.3], cl);
  return (
    <AbsoluteFill style={{translate: `0px ${y}px`, scale: `${sc}`, transformOrigin: `540px ${base - 500}px`, opacity: interpolate(f, [0, 3], [0, 1], cl) * interpolate(f, [len - 3, len], [1, 0.2], cl),
      filter: vel > 0.3 ? `blur(${Math.min(10, vel)}px)` : undefined}}>
      <Prod p={p} x={x} base={base} floor={hasFloor(i)} sweep={sweep} />
    </AbsoluteFill>
  );
};

/** golden liquid sweep across the cut: a translucent wavy gold band + a specular edge, screen-blended */
const GoldSweep: React.FC<{dir: number}> = ({dir}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, 9], [-0.35, 1.35], {...cl, easing: Easing.inOut(Easing.cubic)});
  const a = Math.sin(Math.PI * interpolate(f, [0, 9], [0, 1], cl));
  if (a <= 0.01) return null;
  const cx = (dir > 0 ? p : 1 - p) * 1400 - 160;
  let d = '';
  for (let y = -100; y <= 2020; y += 40) d += `${y === -100 ? 'M' : 'L'}${cx + Math.sin(y / 170 + f * 0.7) * 60 - y * 0.35} ${y} `;
  let d2 = '';
  for (let y = 2020; y >= -100; y -= 40) d2 += `L${cx + 260 + Math.sin(y / 150 + f * 0.6) * 60 - y * 0.35} ${y} `;
  return (
    <AbsoluteFill style={{mixBlendMode: 'screen', opacity: 0.85 * a, pointerEvents: 'none'}}>
      <svg width={1080} height={1920}>
        <defs>
          <linearGradient id={`gs${dir}`} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#000" /><stop offset="0.35" stopColor="#c99a4a" /><stop offset="0.55" stopColor="#ffe9b8" /><stop offset="0.75" stopColor="#b8852f" /><stop offset="1" stopColor="#000" />
          </linearGradient>
          <filter id="gsb"><feGaussianBlur stdDeviation="14" /></filter>
        </defs>
        <path d={d + d2 + 'Z'} fill={`url(#gs${dir})`} filter="url(#gsb)" />
      </svg>
    </AbsoluteFill>
  );
};

/** the two Flow plates: batch 1 (golden sweep) to 4.65 s, liquid wipe to batch 2 (gold silk, slowed to ~0.9x) */
const Backgrounds: React.FC = () => {
  const f = useCurrentFrame();
  const w = interpolate(f, [S(4.65), S(5.15)], [0, 1], {...cl, easing: Easing.inOut(Easing.cubic)});
  const grade = 'saturate(0.96) contrast(1.04) brightness(1.02) sepia(0.06)';
  const edge = w * 160 - 30;                                      // wipe front, in % of a diagonal gradient
  return (
    <AbsoluteFill>
      {f < S(5.2) && <AbsoluteFill style={{filter: grade}}><OffthreadVideo src={staticFile('cm/batch1_golden.mp4')} muted style={{width: 1080, height: 1920}} /></AbsoluteFill>}
      {f >= S(4.6) && (
        <AbsoluteFill style={{filter: grade, WebkitMaskImage: f < S(5.15) ? `linear-gradient(32deg, #000 ${edge - 18}%, rgba(0,0,0,0) ${edge + 18}%)` : undefined}}>
          <Sequence from={S(4.6)} layout="none">
            <OffthreadVideo src={staticFile('cm/batch2_liquid.mp4')} muted playbackRate={0.88} style={{width: 1080, height: 1920}} />
          </Sequence>
        </AbsoluteFill>
      )}
      {f >= S(4.65) && f < S(5.15) && (
        <AbsoluteFill style={{mixBlendMode: 'screen', opacity: Math.sin(Math.PI * w) * 0.75,
          background: `linear-gradient(32deg, rgba(0,0,0,0) ${edge - 10}%, rgba(255,228,170,0.9) ${edge}%, rgba(0,0,0,0) ${edge + 10}%)`}} />
      )}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 85% 70% at 50% 46%, rgba(0,0,0,0) 58%, rgba(70,48,22,0.28) 100%)'}} />
    </AbsoluteFill>
  );
};

const Group: React.FC<{len: number}> = ({len}) => {
  const f = useCurrentFrame();
  const UP = 1110, LOW = 1460;
  const push = 1 + 0.035 * interpolate(f, [0, len], [0, 1], cl);
  const sp = (k: number) => spring({frame: f - k, fps: FPS, config: {damping: 16, stiffness: 160}});
  const plinth = interpolate(f, [0, 6], [0, 1], cl);
  const back: [number, number, number][] = [[7, -268, 300], [6, -96, 300], [8, 96, 300], [9, 262, 300]];
  const front: [number, number, number][] = [[0, -445, 320], [1, -322, 320], [2, -205, 312], [10, 0, 250], [3, 205, 312], [4, 320, 320], [5, 443, 312]];
  return (
    <AbsoluteFill style={{scale: `${push}`, transformOrigin: '540px 1300px'}}>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 70% 40% at 50% 62%, rgba(255,246,226,0.55), rgba(255,246,226,0) 70%)'}} />
      <div style={{opacity: plinth}}>
        <div style={{position: 'absolute', left: 170, width: 740, top: UP, height: LOW - UP - 20,
          background: 'linear-gradient(90deg, #cdb79a, #f6ecdc 35%, #ecdcc6 65%, #bea688)', boxShadow: '0 20px 40px rgba(80,54,24,0.25)'}} />
        <div style={{position: 'absolute', left: 170, width: 740, top: UP - 1, height: 3, background: 'linear-gradient(90deg, #b9822f, #fff1c8, #b9822f)'}} />
        <div style={{position: 'absolute', left: 20, width: 1040, top: LOW - 20, height: 70,
          background: 'linear-gradient(90deg, #c2ad92, #f7eee2 35%, #eee2d2 65%, #b49d80)', boxShadow: '0 30px 60px rgba(80,54,24,0.32)'}} />
        <div style={{position: 'absolute', left: 20, width: 1040, top: LOW - 21, height: 3, background: 'linear-gradient(90deg, #b9822f, #fff1c8, #b9822f)'}} />
      </div>
      {back.map(([i, dx, h], k) => (
        <div key={i} style={{position: 'absolute', inset: 0, opacity: Math.min(1, sp(k * 2) * 1.6), translate: `0px ${(1 - sp(k * 2)) * 40}px`}}>
          <Prod p={PR[i]} x={540 + dx} base={UP} s={h / sizeOf(PR[i]).h} />
        </div>
      ))}
      {front.map(([i, dx, h], k) => {
        const s = PR[i].kind === 'box' ? h / sizeOf(PR[i]).w : h / sizeOf(PR[i]).h;
        return (
          <div key={i} style={{position: 'absolute', inset: 0, opacity: Math.min(1, sp(3 + Math.abs(k - 3) * 2) * 1.6), translate: `0px ${(1 - sp(3 + Math.abs(k - 3) * 2)) * 50}px`}}>
            <Prod p={PR[i]} x={540 + dx} base={LOW - 20} s={s} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const Closing: React.FC = () => {
  const f = useCurrentFrame();
  const bg = interpolate(f, [0, 5], [0, 1], {...cl, easing: Easing.out(Easing.cubic)});
  const t1 = interpolate(f, [2, 8], [0, 1], {...cl, easing: Easing.out(Easing.cubic)});
  const t2 = interpolate(f, [5, 11], [0, 1], {...cl, easing: Easing.out(Easing.cubic)});
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{opacity: bg, background: 'radial-gradient(ellipse 80% 55% at 50% 48%, #fbf3e3 0%, #ecd9b6 50%, #c9a46a 100%)'}} />
      <AbsoluteFill style={{opacity: bg * 0.5, background: 'radial-gradient(ellipse 50% 22% at 50% 50%, rgba(255,255,255,0.9), rgba(255,255,255,0) 70%)'}} />
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <defs>
          <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#d9ac5c" /><stop offset="0.5" stopColor="#a8742c" /><stop offset="1" stopColor="#7d5220" /></linearGradient>
        </defs>
        <text x={540} y={905} textAnchor="middle" fontFamily="Corm" fontSize={132} letterSpacing={30} fill="url(#cg)" opacity={t1}
          style={{transform: `translateY(${(1 - t1) * 14}px)`}}>PALMCARE</text>
        <line x1={540 - 170 * t2} y1={968} x2={540 + 170 * t2} y2={968} stroke="#b8862f" strokeWidth={2} />
        <text x={540} y={1050} textAnchor="middle" fontFamily="CormItalic" fontSize={64} fill="#5a3a1a" opacity={t2}>Pamper your skin with PalmCare.</text>
      </svg>
    </AbsoluteFill>
  );
};

export const Commercial: React.FC = () => (
  <AbsoluteFill style={{background: '#e9dcc6'}}>
    <Backgrounds />
    {WIN.map(([a, b], i) => (
      <Sequence key={i} from={S(a)} durationInFrames={S(b) - S(a)}>
        <Reveal i={i} len={S(b) - S(a)} />
      </Sequence>
    ))}
    {/* golden liquid sweeps on every product cut (not on the batch transition, which has its own liquid wipe) */}
    {[...T.slice(1, 7), ...T.slice(9, 12), T[12]].map((t, k) => (
      <Sequence key={'s' + k} from={S(t) - 5} durationInFrames={10}><GoldSweep dir={k % 2 ? -1 : 1} /></Sequence>
    ))}
    <Sequence from={S(GROUP[0])} durationInFrames={S(GROUP[1]) - S(GROUP[0]) + 8}><Group len={S(GROUP[1]) - S(GROUP[0]) + 8} /></Sequence>
    <Sequence from={S(CLOSE[0])} durationInFrames={S(CLOSE[1]) - S(CLOSE[0])}><Closing /></Sequence>
  </AbsoluteFill>
);
