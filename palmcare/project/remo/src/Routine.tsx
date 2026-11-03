import React from 'react';
import {AbsoluteFill, Img, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {loadFonts} from './fonts';

loadFonts();

/** Video 7, "The PalmCare Glow Routine" (after the client's Medik8-style reference): one locked camera on a sunlit
 * set (warm wall, window light with soft mullion shadows, travertine table). Each real product is placed into the
 * same pool of light on the beat, the previous one lifted out, with real sun shadows on the table and wall. Minimal
 * type at the top: the product name and its routine slot. Body routine lineup, face routine lineup, then an editorial
 * end card in the same light. 92 BPM: one product every two beats. */
export const FPS = 24;
export const BPM = 92;
const B = 60 / BPM;
export const bf = (b: number) => Math.round(b * B * FPS);
const EASE = Easing.bezier(0.16, 1, 0.3, 1);
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

type Prod = {img: string; ar: number; kind: 'bottle' | 'pack' | 'box'; name: string; slot: string};
const P: Record<string, Prod> = {
  milky: {img: 'milky.png', ar: 762 / 1924, kind: 'bottle', name: 'Milky Hydro-Glow', slot: '(Shower)'},
  cacao: {img: 'cacao.png', ar: 702 / 1908, kind: 'bottle', name: 'Cacao & Collagen', slot: '(After Shower)'},
  citrus: {img: 'citrus_cut.png', ar: 488 / 1390, kind: 'bottle', name: 'Citrus Vitamin Glow Infusion', slot: '(Shower)'},
  molecular: {img: 'molecular_cut.png', ar: 471 / 1384, kind: 'bottle', name: 'Molecular Glow', slot: '(After Shower)'},
  tropical: {img: 'tropical_cut.png', ar: 495 / 1362, kind: 'bottle', name: 'Advanced Tropical Glow', slot: '(Shower)'},
  dermalight: {img: 'dermalight_cut.png', ar: 509 / 1316, kind: 'bottle', name: 'Dermalight', slot: '(After Shower)'},
  vitac: {img: 'vitac_real_final.png', ar: 710 / 1248, kind: 'pack', name: 'Vita C+ Serum', slot: '(AM Routine)'},
  n10: {img: 'n10_real_final.png', ar: 710 / 1248, kind: 'pack', name: 'N10 Niacinamide Serum', slot: '(AM/PM)'},
  glow: {img: 'glowshield_box_flat.png', ar: 583 / 1295, kind: 'pack', name: 'GlowShield Sunscreen', slot: '(AM Routine)'},
  box: {img: 'box_straight.png', ar: 1100 / 855, kind: 'box', name: 'Vitamin C Face Moisturiser', slot: '(AM/PM)'},
  derma: {img: 'dermaluxe_box_final.png', ar: 710 / 1248, kind: 'pack', name: 'DermaLuxe Pro', slot: '(PM Routine)'},
};
const BODY = ['milky', 'cacao', 'citrus', 'molecular', 'tropical', 'dermalight'];
const FACE = ['vitac', 'n10', 'glow', 'box', 'derma'];
const TABLE = 1400;                                   // table edge (horizon) y
const SPOT = 1470;                                    // where products stand

type Scene = {k: 'open' | 'place' | 'lineup' | 'end'; beats: number; id?: string; set?: string[]; title?: string};
export const SCENES: Scene[] = [
  {k: 'open', beats: 1},
  ...BODY.map((id) => ({k: 'place' as const, beats: 3, id})),
  {k: 'lineup', beats: 4, set: BODY, title: 'Your body glow routine'},
  ...FACE.map((id) => ({k: 'place' as const, beats: 3, id})),
  {k: 'lineup', beats: 4, set: FACE, title: 'Your face glow routine'},
  {k: 'end', beats: 9},
];
const SB: number[] = SCENES.reduce<number[]>((a, s, i) => [...a, i === 0 ? 0 : a[i - 1] + SCENES[i - 1].beats], []);
export const SF = SB.map(bf);
export const TOTAL_F = bf(SB[SB.length - 1] + SCENES[SCENES.length - 1].beats);

const sizeOf = (p: Prod, s = 1) => {
  const h = (p.kind === 'bottle' ? 720 : p.kind === 'pack' ? 640 : 520 / p.ar) * s;
  return {h, w: h * p.ar};
};

/** studio set: seamless warm-grey sweep (wall curving into the floor, no hard horizon), a big soft key-light pool
 * behind the product, a soft top light, a gentle glossy floor sheen; slow breathing of the light */
const SunSet: React.FC = () => {
  const f = useCurrentFrame();
  const br = 1 + 0.02 * Math.sin(f / 40);
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#cfc6ba'}}>
      <AbsoluteFill style={{background: 'linear-gradient(180deg, #d8d0c5 0%, #e4ddd3 52%, #efe9e1 70%, #e6dfd5 100%)'}} />
      <AbsoluteFill style={{background: `radial-gradient(ellipse ${62 * br}% ${36 * br}% at 50% 56%, rgba(255,252,246,0.95), rgba(255,250,242,0.5) 45%, rgba(255,250,242,0) 75%)`}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 90% 30% at 50% -4%, rgba(255,255,255,0.55), rgba(255,255,255,0) 70%)'}} />
      {/* the sweep: soft shading where wall bends into floor */}
      <div style={{position: 'absolute', left: 0, right: 0, top: TABLE - 260, height: 300,
        background: 'linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(120,104,86,0.07) 55%, rgba(0,0,0,0) 100%)'}} />
      <div style={{position: 'absolute', left: 0, right: 0, top: TABLE + 40, bottom: 0,
        background: 'radial-gradient(ellipse 60% 40% at 50% 10%, rgba(255,255,255,0.55), rgba(255,255,255,0) 70%)'}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 95% 80% at 50% 52%, rgba(0,0,0,0) 55%, rgba(70,56,40,0.22) 100%)'}} />
    </AbsoluteFill>
  );
};

/** a product standing on the table in the sun: cast shadow on the table and on the wall, warm sun rim on the right */
const Placed: React.FC<{p: Prod; x: number; base: number; s?: number; lift?: number}> = ({p, x, base, s = 1, lift = 0}) => {
  const {w, h} = sizeOf(p, s);
  const mask = p.kind === 'bottle' ? {WebkitMaskImage: `url(${staticFile('p/' + p.img)})`, WebkitMaskSize: '100% 100%'} : {};
  const r = p.kind === 'bottle' ? 0 : 6 * s;
  const shadowOp = interpolate(lift, [0, 40], [1, 0.35], cl);
  return (
    <>
      {/* soft studio shadow behind-left + floor reflection */}
      <div style={{position: 'absolute', left: x - w / 2, top: base - h, width: w, height: h, borderRadius: r, transformOrigin: '50% 100%',
        transform: 'skewX(38deg) scaleY(0.2)', background: 'rgba(80,62,44,0.28)', filter: 'blur(10px)', opacity: shadowOp, ...mask} as React.CSSProperties} />
      <div style={{position: 'absolute', left: x - w / 2, top: base + 2, width: w, height: h * 0.3, overflow: 'hidden', opacity: 0.16 * shadowOp,
        WebkitMaskImage: 'linear-gradient(180deg, rgba(0,0,0,1), rgba(0,0,0,0))'}}>
        <Img src={staticFile('p/' + p.img)} style={{width: w, height: h, display: 'block', transform: 'scaleY(-1)', transformOrigin: '50% 50%', marginTop: -h * 0.7, borderRadius: r}} />
      </div>
      <div style={{position: 'absolute', left: x - w * 0.55, top: base - 12 * s, width: w * 1.1, height: 24 * s, borderRadius: '50%',
        background: 'radial-gradient(ellipse, rgba(60,40,22,0.5), rgba(60,40,22,0) 70%)', opacity: shadowOp}} />
      <div style={{position: 'absolute', left: x - w / 2, top: base - h - lift, width: w, height: h}}>
        <Img src={staticFile('p/' + p.img)} style={{width: w, height: h, display: 'block', borderRadius: r}} />
        <div style={{position: 'absolute', inset: 0, borderRadius: r, mixBlendMode: 'soft-light',
          background: 'linear-gradient(90deg, rgba(0,0,0,0.12) 0%, rgba(255,255,255,0.18) 30%, rgba(255,255,255,0) 60%, rgba(0,0,0,0.12) 100%)', ...mask} as React.CSSProperties} />
      </div>
    </>
  );
};

const TopText: React.FC<{a: string; b?: string; len: number; inAt?: number; outAt?: number}> = ({a, b, len, inAt = 2, outAt}) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [inAt, inAt + 7], [0, 1], {...cl, easing: EASE}) * (outAt !== undefined ? interpolate(f, [outAt, outAt + 6], [1, 0], cl) : 1);
  return (
    <div style={{position: 'absolute', top: 220, width: '100%', textAlign: 'center', opacity: o, translate: `0px ${(1 - o) * 10}px`, padding: '0 60px', boxSizing: 'border-box'}}>
      <div style={{fontFamily: 'JostMed', fontSize: a.length > 22 ? 58 : 68, lineHeight: 1.1, color: '#2b2017', letterSpacing: 0.5}}>{a}</div>
      {b && <div style={{marginTop: 14, fontFamily: 'JostReg', fontSize: 40, color: '#8a5a2e', letterSpacing: 2}}>{b}</div>}
    </div>
  );
};

/** the hand (real photo, dark skin, pinch grip) holds products by the top. HAND_PX/PY = pinch point in the image */
const HAND = {w: 1988, h: 2356, px: 506, py: 2004, scale: 0.5};
const Hand: React.FC<{x: number; y: number; vx: number; vy: number}> = ({x, y, vx, vy}) => {
  const s = HAND.scale;
  const blur = Math.min(10, Math.hypot(vx, vy) / 6);
  return (
    <Img src={staticFile('hand.png')} style={{position: 'absolute', left: x - HAND.px * s, top: y - HAND.py * s, width: HAND.w * s, height: HAND.h * s,
      filter: `blur(${blur}px) drop-shadow(-10px 16px 18px rgba(40,26,14,0.25))`}} />
  );
};

/** one smooth arc: start -> end with a curved path (control point raised), eased like a real reach */
const arc = (t: number, x0: number, y0: number, x1: number, y1: number, lift: number) => {
  const e = Easing.bezier(0.45, 0, 0.2, 1)(Math.min(1, Math.max(0, t)));
  const cx = (x0 + x1) / 2 + 120, cy = Math.min(y0, y1) - lift;
  const u = 1 - e;
  return [u * u * x0 + 2 * u * e * cx + e * e * x1, u * u * y0 + 2 * u * e * cy + e * e * y1];
};

/** placing one product: the hand lifts the previous product out to the top right, comes back with the next one on an
 * arc, sets it down softly in the light, lets go and leaves. Velocity-matched motion blur on everything that moves. */
const PlaceScene: React.FC<{id: string; prev?: string; len: number}> = ({id, prev, len}) => {
  const f = useCurrentFrame();
  const p = P[id];
  const {h} = sizeOf(p);
  const pp = prev ? P[prev] : null;
  const REACH = [0, 7], OUT = [7, 16], IN = [15, 28], REL = [28, 36];
  const topY = (q: Prod) => SPOT - sizeOf(q).h + (q.kind === "bottle" ? 22 : 14);
  const offX = 1500, offY = -500;
  // previous product leaves with the hand
  let hand: [number, number] | null = null, hv: [number, number] = [0, 0];
  const pos = (fr: number): [number, number, string] => {
    if (pp && fr < REACH[1]) {
      const [hx, hy] = arc((fr - REACH[0]) / (REACH[1] - REACH[0]), offX, offY, 540, topY(pp), 60);
      return [hx, hy, 'reach'];
    }
    if (pp && fr <= OUT[1]) {
      const [hx, hy] = arc((fr - OUT[0]) / (OUT[1] - OUT[0]), 540, topY(pp), offX, offY, 60);
      return [hx, hy, 'out'];
    }
    if (!pp && fr < IN[0]) return [offX, offY, 'wait'];
    if (fr <= IN[1]) {
      const [hx, hy] = arc((fr - IN[0]) / (IN[1] - IN[0]), offX, offY, 540, topY(p), 140);
      return [hx, hy, 'in'];
    }
    const t = (fr - REL[0]) / (REL[1] - REL[0]);
    const e = Easing.bezier(0.5, 0, 0.75, 0)(Math.min(1, Math.max(0, t)));
    return [540 + e * 900, topY(p) - 30 * Math.min(1, t * 4) - e * 900, 'rel'];
  };
  const [hx, hy, phase] = pos(f);
  const [hx0, hy0] = pos(Math.max(0, f - 1));
  hand = [hx, hy]; hv = [hx - hx0, hy - hy0];
  const prodBlur = (vx: number, vy: number) => Math.min(9, Math.hypot(vx, vy) / 7);
  let prodNode: React.ReactNode = null;
  if (phase === 'out' && pp) {
    const dx = hx - 540, dy = hy - topY(pp);
    prodNode = <div style={{position: 'absolute', inset: 0, translate: `${dx}px ${dy}px`, filter: `blur(${prodBlur(hv[0], hv[1])}px)`}}><Placed p={pp} x={540} base={SPOT} lift={Math.min(40, -dy)} /></div>;
  } else if (phase === 'reach' && pp) {
    prodNode = <Placed p={pp} x={540} base={SPOT} />;
  } else if (phase === 'wait') {
    prodNode = null;
  } else if (phase === 'in') {
    const dx = hx - 540, dy = hy - topY(p);
    prodNode = f >= IN[0] ? <div style={{position: 'absolute', inset: 0, translate: `${dx}px ${dy}px`, filter: `blur(${prodBlur(hv[0], hv[1])}px)`}}><Placed p={p} x={540} base={SPOT} lift={Math.min(40, -dy)} /></div> : null;
  } else {
    prodNode = <Placed p={p} x={540} base={SPOT} />;
  }
  const showHand = phase !== 'wait' && !(phase === 'rel' && f > REL[1] + 1);
  return (
    <AbsoluteFill>
      <SunSet />
      {prodNode}
      {showHand && <Hand x={hand[0]} y={hand[1]} vx={hv[0]} vy={hv[1]} />}
      {pp && <TopText a={pp.name} b={pp.slot} len={len} inAt={-20} outAt={6} />}
      <TopText a={p.name} b={p.slot} len={len} inAt={pp ? 22 : 16} />
    </AbsoluteFill>
  );
};

const Heart: React.FC<{size: number; color: string}> = ({size, color}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={{display: 'inline-block', verticalAlign: '-4px', marginLeft: 10}}>
    <path d="M12 21s-7.5-4.6-9.6-9.2C.9 8.4 3 5 6.5 5c2 0 3.6 1.1 4.5 2.6C11.9 6.1 13.5 5 15.5 5 19 5 21.1 8.4 19.6 11.8 17.5 16.4 12 21 12 21z" fill="none" stroke={color} strokeWidth={1.6} />
  </svg>
);

const Lineup: React.FC<{set: string[]; title: string; len: number}> = ({set, title, len}) => {
  const f = useCurrentFrame();
  const n = set.length;
  const s = n > 5 ? 0.6 : 0.62;
  const widths = set.map((id) => sizeOf(P[id], s).w);
  const gap = 22;
  const total = widths.reduce((a, b) => a + b, 0) + gap * (n - 1);
  let x = 540 - total / 2;
  const o = interpolate(f, [2, 10], [0, 1], {...cl, easing: EASE}) * interpolate(f, [len - 4, len], [1, 0], cl);
  return (
    <AbsoluteFill>
      <SunSet />
      {set.map((id, i) => {
        const cx = x + widths[i] / 2;
        x += widths[i] + gap;
        return <Placed key={id} p={P[id]} x={cx} base={SPOT} s={s} />;
      })}
      <div style={{position: 'absolute', top: 250, width: '100%', textAlign: 'center', opacity: o, fontFamily: 'JostMed', fontSize: 62,
        color: '#2b2017'}}>{title}<Heart size={50} color="#8a5a2e" /></div>
    </AbsoluteFill>
  );
};

const EndCard: React.FC<{len: number}> = ({len}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const fin = (d: number, dur = 10) => interpolate(f, [d, d + dur], [0, 1], {...cl, easing: EASE});
  const back = FACE, front = BODY;
  const sb = 0.5, sf = 0.44;
  const row = (ids: string[], s: number, base: number, gap: number, delay: number) => {
    const ws = ids.map((id) => sizeOf(P[id], s).w);
    const tot = ws.reduce((a, b) => a + b, 0) + gap * (ids.length - 1);
    let x = 540 - tot / 2;
    return ids.map((id, i) => {
      const cx = x + ws[i] / 2;
      x += ws[i] + gap;
      const sp = spring({frame: f - delay - i * 2, fps, config: {damping: 16, stiffness: 140}});
      return <div key={id} style={{position: 'absolute', inset: 0, opacity: Math.min(1, sp * 1.5), translate: `0px ${(1 - sp) * 30}px`}}>
        <Placed p={P[id]} x={cx} base={base} s={s} />
      </div>;
    });
  };
  const pulse = 1 + 0.025 * Math.max(0, Math.sin((2 * Math.PI * t) / B)) * fin(60);
  return (
    <AbsoluteFill>
      <SunSet />
      {row(back, sb, 1395, 18, 0)}
      {row(front, sf, 1600, 16, 4)}
      <div style={{position: 'absolute', top: 150, width: '100%', textAlign: 'center', fontFamily: 'JostMed', fontSize: 28, letterSpacing: 16, color: '#7a6450', opacity: fin(8)}}>PALMCARE</div>
      <div style={{position: 'absolute', top: 196, left: 540 - 90 * fin(10), width: 180 * fin(10), height: 1.5, background: '#9a7a55'}} />
      <div style={{position: 'absolute', top: 236, width: '100%', textAlign: 'center', fontFamily: 'Corm', fontSize: 98, color: '#3b2a1e',
        opacity: fin(14), translate: `0px ${(1 - fin(14)) * 14}px`}}>Pamper your skin</div>
      <div style={{position: 'absolute', top: 340, width: '100%', textAlign: 'center', fontFamily: 'CormItalic', fontSize: 124, color: '#9a6430',
        opacity: fin(22), translate: `0px ${(1 - fin(22)) * 14}px`}}>with PalmCare.</div>
      <div style={{position: 'absolute', left: 90, right: 90, top: 1660, height: 1.5, background: '#9a7a55', opacity: fin(36), scale: `${fin(36)} 1`}} />
      <div style={{position: 'absolute', top: 1680, width: '100%', display: 'flex', justifyContent: 'center', gap: 50, opacity: fin(40),
        fontFamily: 'JostMed', fontSize: 46, color: '#3b2a1e', letterSpacing: 1}}>
        {['0903 055 5424', '0809 361 2901'].map((n) => (
          <span key={n} style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <svg width={30} height={30} viewBox="0 0 24 24"><path fill="#9a6430" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1l-2.3 2.2z" /></svg>{n}
          </span>
        ))}
      </div>
      <div style={{position: 'absolute', top: 1752, width: '100%', textAlign: 'center', fontFamily: 'JostReg', fontSize: 32, color: '#2b2017', opacity: fin(46)}}>
        Shop A67, Kogi Plaza, BBA Market, Trade Fair Complex, Lagos</div>
      <div style={{position: 'absolute', top: 1802, left: '50%', translate: '-50% 0px', scale: `${(0.85 + 0.15 * fin(54)) * pulse}`, opacity: fin(54),
        padding: '18px 70px', borderRadius: 50, background: '#3b2a1e', color: '#f6ead8', fontFamily: 'JostMed', fontSize: 30, letterSpacing: 10,
        boxShadow: '0 10px 24px rgba(59,42,30,0.3)'}}>ORDER NOW</div>
    </AbsoluteFill>
  );
};

const Finish: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 85% 70% at 50% 50%, rgba(0,0,0,0) 60%, rgba(40,26,14,0.22) 100%)'}} />
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, opacity: 0.06, mixBlendMode: 'overlay'}}>
        <filter id="g2"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={f % 40} /></filter>
        <rect width="100%" height="100%" filter="url(#g2)" />
      </svg>
    </AbsoluteFill>
  );
};

export const Routine: React.FC = () => (
  <AbsoluteFill style={{background: '#000'}}>
    {SCENES.map((s, i) => {
      const from = SF[i];
      const len = (i + 1 < SCENES.length ? SF[i + 1] : TOTAL_F) - from;
      const prev = i > 0 && SCENES[i - 1].k === 'place' ? SCENES[i - 1].id : undefined;
      const node = s.k === 'open' ? <SunSet /> : s.k === 'place' ? <PlaceScene id={s.id!} prev={prev} len={len} />
        : s.k === 'lineup' ? <Lineup set={s.set!} title={s.title!} len={len} /> : <EndCard len={len} />;
      return <Sequence key={i} from={from} durationInFrames={len}>{node}</Sequence>;
    })}
    <Finish />
  </AbsoluteFill>
);
