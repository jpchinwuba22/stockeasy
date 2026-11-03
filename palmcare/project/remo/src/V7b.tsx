import React from 'react';
import {AbsoluteFill, Img, interpolate, random, Sequence, spring, staticFile, useCurrentFrame, Easing} from 'remotion';
import {clamp, easeOut, GoldDust, OrangeBurst} from './fx';
import {loadFonts} from './fonts';
import {EndLux} from './EndLux';
import {Leak} from './LeakTest';

loadFonts();

/** Video 7, new concept "Colour Worlds": every PalmCare product gets its own world in its label colours. Hook: a
 * gold drop hits the frame, colour pops flash every product on the half-beat, the PalmCare title slams while the six
 * bottles fan in. Each product then drops onto a glossy podium on the beat (shockwave ring, colour burst), its giant
 * name drifts behind it, liquid shapes float, a light sweep runs across the real label, and a liquid wave in the next
 * product's colour carries us on. Face care in packs only. Finale lineup -> end card. 112 BPM, cuts on the beat. */
export const FPS = 24;
const B = 60 / 112;
export const bf = (b: number) => Math.round(b * B * FPS);

type Prod = {img: string; kind: 'bottle' | 'pack' | 'box'; word: string; name: [string, string]; c1: string; c2: string; c3: string};
const P: Record<string, Prod> = {
  milky: {img: 'milky.png', kind: 'bottle', word: 'HYDRO-GLOW', name: ['Milky Hydro-Glow', 'Moisturising Body Wash'], c1: '#f6ead9', c2: '#c89466', c3: '#8a5a36'},
  cacao: {img: 'cacao.png', kind: 'bottle', word: 'CACAO', name: ['Cacao & Collagen', 'Body Lotion'], c1: '#d9a072', c2: '#7a4024', c3: '#3d1d0e'},
  citrus: {img: 'citrus_cut.png', kind: 'bottle', word: 'CITRUS', name: ['Citrus Vitamin Glow Infusion', 'Body Wash'], c1: '#ffd36b', c2: '#ff9a1f', c3: '#e0570b'},
  molecular: {img: 'molecular_cut.png', kind: 'bottle', word: 'MOLECULAR', name: ['Molecular Glow', 'Body Lotion'], c1: '#ffc27a', c2: '#f27a12', c3: '#a8420a'},
  tropical: {img: 'tropical_cut.png', kind: 'bottle', word: 'TROPICAL', name: ['Advanced Tropical Glow', 'Exfoliating Lightening Body Wash'], c1: '#ffb347', c2: '#e2601a', c3: '#1f5c3f'},
  dermalight: {img: 'dermalight_cut.png', kind: 'bottle', word: 'DERMALIGHT', name: ['Dermalight', 'Body Lotion'], c1: '#f5d6ad', c2: '#c9813f', c3: '#6e3b17'},
  vitac: {img: 'vitac_real_final.png', kind: 'pack', word: 'VITA C+', name: ['Vita C+ Serum', ''], c1: '#ffd9a0', c2: '#f5891f', c3: '#a64a0c'},
  n10: {img: 'n10_real_final.png', kind: 'pack', word: 'N10', name: ['N10 Niacinamide Serum', ''], c1: '#bff0ee', c2: '#18a6ad', c3: '#0b4f5c'},
  derma: {img: 'dermaluxe_box_final.png', kind: 'pack', word: 'DERMALUXE', name: ['DermaLuxe Pro', 'Hydrating Night Repair Serum'], c1: '#f1d4f7', c2: '#9b4dca', c3: '#3f1561'},
  glow: {img: 'glowshield_box_flat.png', kind: 'pack', word: 'GLOWSHIELD', name: ['GlowShield', 'Broad-Spectrum Daily Defense Sunscreen'], c1: '#fde3d2', c2: '#ec9a6c', c3: '#8c4426'},
  box: {img: 'box_straight.png', kind: 'box', word: 'VITAMIN C', name: ['Vitamin C', 'Face Moisturiser'], c1: '#ffe2b8', c2: '#ff8a3d', c3: '#b24a12'},
};
const AR: Record<string, number> = {'box_straight.png': 1100 / 855, 'cacao.png': 702 / 1908, 'citrus_cut.png': 488 / 1390,
  'dermalight_cut.png': 509 / 1316, 'dermaluxe_box_final.png': 710 / 1248, 'glowshield_box_flat.png': 583 / 1295, 'milky.png': 762 / 1924,
  'molecular_cut.png': 471 / 1384, 'n10_real_final.png': 710 / 1248, 'tropical_cut.png': 495 / 1362, 'vitac_real_final.png': 710 / 1248};
const BOTTLES = ['milky', 'cacao', 'citrus', 'molecular', 'tropical', 'dermalight'];

type Scene = {k: 'drop' | 'pops' | 'title' | 'prod' | 'card' | 'serum' | 'finale' | 'end'; beats: number; id?: string};
export const SCENES: Scene[] = [
  {k: 'drop', beats: 1}, {k: 'pops', beats: 3}, {k: 'title', beats: 4},
  ...BOTTLES.map((id) => ({k: 'prod' as const, beats: 4, id})),
  {k: 'card', beats: 2},
  ...['vitac', 'n10', 'derma', 'glow'].map((id) => ({k: 'serum' as const, beats: 3, id})),
  {k: 'serum', beats: 4, id: 'box'}, {k: 'finale', beats: 4}, {k: 'end', beats: 12},
];
const SB: number[] = SCENES.reduce<number[]>((a, s, i) => [...a, i === 0 ? 0 : a[i - 1] + SCENES[i - 1].beats], []);
export const SF = SB.map(bf);
export const TOTAL_B = SB[SB.length - 1] + SCENES[SCENES.length - 1].beats;
export const TOTAL_F = bf(TOTAL_B);

const sizeOf = (p: Prod) => (p.kind === 'bottle' ? {h: 1060} : p.kind === 'pack' ? {h: 980} : {w: 820});

/** a real product cut-out, standing on its base point, with contact shadow and podium reflection */
const Product: React.FC<{p: Prod; x: number; base: number; scale?: number; sweep?: number; reflect?: boolean; keyLight?: boolean; rim?: string}> = ({p, x, base, scale = 1, sweep = -1, reflect = true, keyLight = false, rim}) => {
  const sz = sizeOf(p);
  const ar = AR[p.img];                                                // exact native aspect: never stretched
  const h = (sz.h ?? (sz.w! / ar)) * scale;
  const w = h * ar;
  const radius = p.kind === 'bottle' ? 0 : 10 * scale;
  const img = (
    <Img src={staticFile('p/' + p.img)} style={{width: w, height: h, display: 'block', borderRadius: radius,
      filter: rim ? `drop-shadow(0 0 18px ${rim}) drop-shadow(0 18px 30px rgba(0,0,0,0.5))` : 'drop-shadow(0 18px 30px rgba(30,12,2,0.35))'}} />
  );
  return (
    <>
      <div style={{position: 'absolute', left: x - w * 0.62, top: base - 34 * scale, width: w * 1.24, height: 68 * scale, borderRadius: '50%',
        background: 'radial-gradient(ellipse, rgba(20,8,0,0.55), rgba(20,8,0,0) 70%)'}} />
      {reflect && (
        <div style={{position: 'absolute', left: x - w / 2, top: base, width: w, height: h * 0.22, overflow: 'hidden', opacity: 0.22,
          WebkitMaskImage: 'linear-gradient(180deg, rgba(0,0,0,1), rgba(0,0,0,0))'}}>
          <div style={{transform: 'scaleY(-1)', transformOrigin: '50% 0%', marginTop: 0, height: h}}>
            <div style={{transform: `translateY(${-h}px)`}}>{img}</div>
          </div>
        </div>
      )}
      <div style={{position: 'absolute', left: x - w / 2, top: base - h, width: w, height: h}}>
        {img}
        {keyLight && (
          <div style={{position: 'absolute', inset: 0, mixBlendMode: 'soft-light',
            background: 'linear-gradient(115deg, rgba(255,250,235,0.55) 0%, rgba(255,250,235,0) 45%, rgba(0,0,0,0.25) 100%)',
            WebkitMaskImage: p.kind === 'bottle' ? `url(${staticFile('p/' + p.img)})` : undefined, WebkitMaskSize: '100% 100%'} as React.CSSProperties} />
        )}
        {sweep > -0.3 && sweep < 1.3 && (
          <div style={{position: 'absolute', inset: 0, mixBlendMode: 'screen', borderRadius: radius,
            background: `linear-gradient(105deg, rgba(255,255,255,0) ${sweep * 100 - 14}%, rgba(255,250,235,0.55) ${sweep * 100}%, rgba(255,255,255,0) ${sweep * 100 + 14}%)`,
            WebkitMaskImage: p.kind === 'bottle' ? `url(${staticFile('p/' + p.img)})` : undefined, WebkitMaskSize: '100% 100%'} as React.CSSProperties} />
        )}
      </div>
    </>
  );
};

const Podium: React.FC<{y: number; w: number; c: string; ring: number}> = ({y, w, c, ring}) => (
  <>
    <div style={{position: 'absolute', left: 540 - w / 2, top: y, width: w, height: 420,
      background: `linear-gradient(90deg, rgba(0,0,0,0.28), rgba(255,255,255,0.12) 35%, rgba(0,0,0,0.05) 60%, rgba(0,0,0,0.35)), ${c}`}} />
    <div style={{position: 'absolute', left: 540 - w / 2, top: y - 60, width: w, height: 120, borderRadius: '50%',
      background: `radial-gradient(ellipse at 45% 40%, rgba(255,255,255,0.65), rgba(255,255,255,0.12) 55%), ${c}`,
      boxShadow: 'inset 0 -6px 14px rgba(0,0,0,0.18)'}} />
    {ring > 0 && ring < 1 && (
      <div style={{position: 'absolute', left: 540 - (w / 2) * (0.6 + ring), top: y - 60 * (0.6 + ring), width: w * (0.6 + ring), height: 120 * (0.6 + ring),
        borderRadius: '50%', border: `${5 * (1 - ring)}px solid rgba(255,248,230,${0.9 * (1 - ring)})`}} />
    )}
  </>
);

/** soft liquid colour shapes drifting in the world */
const Blobs: React.FC<{c1: string; c2: string; seed: string}> = ({c1, c2, seed}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      {new Array(7).fill(0).map((_, i) => {
        const r = 140 + random(seed + 'r' + i) * 260;
        const x = random(seed + 'x' + i) * 1080 + Math.sin(f / 30 + i) * 40;
        const y = random(seed + 'y' + i) * 1500 - f * (0.6 + random(seed + 's' + i));
        return <div key={i} style={{position: 'absolute', left: x - r, top: y - r, width: 2 * r, height: 2 * r, borderRadius: '50%',
          background: `radial-gradient(circle at 35% 35%, ${i % 2 ? c1 : c2}, rgba(255,255,255,0) 70%)`, opacity: 0.55, filter: 'blur(6px)'}} />;
      })}
    </AbsoluteFill>
  );
};

/** burst of colour droplets when the product lands */
const Splash: React.FC<{at: number; c: string; y: number; seed: string}> = ({at, c, y, seed}) => {
  const f = useCurrentFrame();
  const u = (f - at) / FPS;
  if (u < 0 || u > 0.9) return null;
  return (
    <AbsoluteFill>
      {new Array(26).fill(0).map((_, i) => {
        const a = -Math.PI * (0.05 + 0.9 * random(seed + i));
        const sp = 380 + random(seed + 's' + i) * 620;
        const d = sp * u;
        const r = 5 + random(seed + 'r' + i) * 12;
        return <div key={i} style={{position: 'absolute', left: 540 + Math.cos(a) * d - r, top: y + Math.sin(a) * d + 900 * u * u - r,
          width: 2 * r, height: 2 * r, borderRadius: '50%', background: c, opacity: 1 - u / 0.9,
          boxShadow: 'inset -2px -3px 4px rgba(0,0,0,0.15), inset 2px 2px 3px rgba(255,255,255,0.5)'}} />;
      })}
    </AbsoluteFill>
  );
};

const ProdScene: React.FC<{p: Prod; len: number; idx: number}> = ({p, len, idx}) => {
  const f = useCurrentFrame();
  const land = 7;                                                    // lands a few frames in, on the beat accent
  const sp = spring({frame: f, fps: FPS, config: {damping: 13, stiffness: 150, mass: 0.9}});
  const mode = idx % 3;                                              // 0 drop in, 1 rise up, 2 slide in (alternating sides)
  const dropY = mode === 0 ? (1 - sp) * -1500 : mode === 1 ? (1 - sp) * 1300 : 0;
  const slideX = mode === 2 ? (1 - sp) * (idx % 2 ? -1100 : 1100) : 0;
  const ring = interpolate(f, [land, land + 14], [0, 1], clamp);
  const shake = f >= land && f < land + 5 ? Math.sin(f * 7) * 4 * (1 - (f - land) / 5) : 0;
  const push = 1 + 0.06 * interpolate(f, [0, len], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const wordX = interpolate(f, [0, len], [180, -380]);
  const sweep = interpolate(f, [land + 4, land + 22], [-0.3, 1.3], clamp);
  const base = p.kind === 'box' ? 1300 : 1430;
  const nameA = interpolate(f, [land + 4, land + 12], [0, 1], {...clamp, easing: easeOut}) * interpolate(f, [len - 6, len - 1], [1, 0], clamp);
  const wipe = interpolate(f, [land + 4, land + 16], [0, 100], {...clamp, easing: easeOut});
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: `radial-gradient(ellipse 80% 60% at 50% 42%, ${p.c1} 0%, ${p.c2} 62%, ${p.c3} 100%)`}}>
      <Blobs c1={p.c1} c2={p.c2} seed={p.word} />
      {/* studio floor with perspective + horizon glow, so the world has depth */}
      <div style={{position: 'absolute', left: -200, right: -200, top: 1180, height: 900, transform: 'perspective(900px) rotateX(62deg)', transformOrigin: '50% 0%',
        background: `repeating-linear-gradient(90deg, rgba(255,255,255,0.06) 0 2px, rgba(255,255,255,0) 2px 120px), linear-gradient(180deg, ${p.c2}, ${p.c3})`}} />
      <div style={{position: 'absolute', left: 0, right: 0, top: 1110, height: 160, background: `radial-gradient(ellipse 60% 50% at 50% 50%, ${p.c1}, rgba(255,255,255,0) 70%)`, opacity: 0.9}} />
      <div style={{position: 'absolute', top: 360, left: wordX, whiteSpace: 'nowrap', fontFamily: 'MontBold', fontSize: p.word.length > 8 ? 250 : 330,
        letterSpacing: -4, color: 'transparent', WebkitTextStroke: '3px rgba(255,255,255,0.55)', opacity: 0.9}}>{p.word} {p.word}</div>
      <div style={{position: 'absolute', top: 650, right: interpolate(f, [0, len], [-200, 260]), whiteSpace: 'nowrap', fontFamily: 'MontBold',
        fontSize: p.word.length > 8 ? 250 : 330, letterSpacing: -4, color: 'rgba(255,255,255,0.16)'}}>{p.word}</div>
      <AbsoluteFill style={{transform: `scale(${push}) translate(${shake}px, ${shake * 0.6}px)`, transformOrigin: `50% ${base}px`}}>
        <Podium y={base} w={p.kind === 'box' ? 900 : 700} c={p.c2} ring={ring} />
        <div style={{position: 'absolute', left: 540 - 420, top: base - 1180, width: 840, height: 1100, borderRadius: '50%',
          background: `radial-gradient(ellipse, ${p.c1}cc, rgba(255,255,255,0) 68%)`, filter: 'blur(20px)', opacity: 0.85}} />
        <div style={{position: 'absolute', inset: 0, transform: `translate(${slideX}px, ${dropY}px)`, filter: `blur(${Math.min(12, (Math.abs(dropY) + Math.abs(slideX)) / 60)}px)`}}>
          <Product p={p} x={540} base={base} sweep={sweep} keyLight />
        </div>
      </AbsoluteFill>
      <Splash at={land} c={p.c1} y={base - 40} seed={p.word} />
      <GoldDust n={36} seed={'pd' + idx} opacity={0.6} />
      <div style={{position: 'absolute', top: 1600, width: '100%', textAlign: 'center', opacity: nameA, clipPath: `inset(0 ${100 - wipe}% 0 0)`}}>
        <div style={{fontFamily: 'Corm', fontFeatureSettings: '"lnum" 1', fontSize: p.name[0].length > 20 ? 74 : 92, color: '#fffaf0', lineHeight: 1.05,
          textShadow: '0 4px 24px rgba(20,8,0,0.65)'}}>{p.name[0]}</div>
        {p.name[1] && <div style={{marginTop: 8, fontFamily: 'JostMed', fontSize: p.name[1].length > 26 ? 26 : 32, letterSpacing: 6, color: '#fff3d6',
          textShadow: '0 3px 14px rgba(20,8,0,0.7)'}}>{p.name[1].toUpperCase()}</div>}
      </div>
    </AbsoluteFill>
  );
};

/** FACE CARE section card: black, a gold hairline draws, the title resolves out of blur */
const FaceCard: React.FC<{len: number}> = ({len}) => {
  const f = useCurrentFrame();
  const line = interpolate(f, [0, 10], [0, 1], {...clamp, easing: easeOut});
  const tIn = interpolate(f, [4, 16], [0, 1], {...clamp, easing: easeOut});
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse 60% 40% at 50% 50%, #1b120c, #050304)'}}>
      <GoldDust n={40} seed="fc" opacity={0.5} />
      <div style={{position: 'absolute', top: 930, left: 540 - 300 * line, width: 600 * line, height: 1.5,
        background: 'linear-gradient(90deg, rgba(255,205,96,0), #ffd88a, rgba(255,205,96,0))', boxShadow: '0 0 18px rgba(255,200,110,0.6)'}} />
      <div style={{position: 'absolute', top: 800, width: '100%', textAlign: 'center', fontFamily: 'Corm', fontSize: 120, letterSpacing: 10 + 14 * (1 - tIn),
        color: '#f6e7cf', opacity: tIn, filter: `blur(${(1 - tIn) * 8}px)`}}>Face Care</div>
      <div style={{position: 'absolute', top: 960, width: '100%', textAlign: 'center', fontFamily: 'JostLight', fontSize: 30, letterSpacing: 14,
        color: '#d9b37a', opacity: interpolate(f, [12, 22], [0, 1], clamp)}}>SERUMS · SUN · MOISTURE</div>
    </AbsoluteFill>
  );
};

/** serum world: black liquid mirror floor, spotlight beam, a glowing droplet falls, the floor ripples and the pack rises
 * out of the liquid with a full mirror reflection and a coloured rim light; slow push, caustic light play */
const SerumScene: React.FC<{p: Prod; len: number; idx: number}> = ({p, len, idx}) => {
  const f = useCurrentFrame();
  const FLOOR = 1430;
  const hit = 6;
  const dropY = interpolate(f, [0, hit], [-80, FLOOR - 10], {...clamp, easing: Easing.in(Easing.quad)});
  const rise = interpolate(f, [hit + 1, hit + 16], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const push = 1 + 0.07 * interpolate(f, [0, len], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const beam = interpolate(f, [hit, hit + 10], [0, 1], clamp);
  const sweep = interpolate(f, [hit + 16, hit + 34], [-0.3, 1.3], clamp);
  const sz = sizeOf(p);
  const ar = AR[p.img];
  const h = (sz.h ?? (sz.w! / ar)) * (p.kind === 'box' ? 0.95 : 0.82);
  const w = h * ar;
  const nameA = interpolate(f, [hit + 14, hit + 22], [0, 1], {...clamp, easing: easeOut}) * interpolate(f, [len - 6, len - 1], [1, 0], clamp);
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#050304'}}>
      <AbsoluteFill style={{background: `radial-gradient(ellipse 55% 38% at 50% 52%, ${p.c2}55, rgba(0,0,0,0) 70%)`}} />
      {new Array(14).fill(0).map((_, i) => {                       // bokeh in the product colour
        const r = 18 + random(p.word + 'b' + i) * 50;
        return <div key={i} style={{position: 'absolute', left: random(p.word + 'x' + i) * 1080 - r + Math.sin(f / 25 + i) * 20,
          top: 200 + random(p.word + 'y' + i) * 1100 - r - f * 0.5, width: 2 * r, height: 2 * r, borderRadius: '50%',
          background: `radial-gradient(circle, ${p.c1}aa, rgba(0,0,0,0) 70%)`, opacity: 0.55}} />;
      })}
      <AbsoluteFill style={{transform: `scale(${push})`, transformOrigin: `50% ${FLOOR}px`}}>
        {/* spotlight beam */}
        <div style={{position: 'absolute', left: 540 - 380, top: -100, width: 760, height: FLOOR + 140, opacity: 0.55 * beam,
          clipPath: 'polygon(42% 0, 58% 0, 100% 100%, 0 100%)', background: `linear-gradient(180deg, rgba(255,250,235,0.0), ${p.c1}55 60%, ${p.c1}88)`, filter: 'blur(8px)'}} />
        {/* liquid mirror floor */}
        <div style={{position: 'absolute', left: 0, right: 0, top: FLOOR, bottom: 0, background: `linear-gradient(180deg, #120c0a, #030202 70%)`}} />
        <div style={{position: 'absolute', left: 0, right: 0, top: FLOOR - 1, height: 2, background: `linear-gradient(90deg, rgba(0,0,0,0), ${p.c1}, rgba(0,0,0,0))`, opacity: 0.7}} />
        {[0, 1].map((k) => {                                         // ripple rings on impact
          const r = interpolate(f, [hit + k * 3, hit + k * 3 + 18], [0, 1], clamp);
          return r > 0 && r < 1 ? <div key={k} style={{position: 'absolute', left: 540 - 520 * r, top: FLOOR - 60 * r, width: 1040 * r, height: 120 * r,
            borderRadius: '50%', border: `${3 * (1 - r)}px solid ${p.c1}`, opacity: 1 - r}} /> : null;
        })}
        {/* the pack rising out of the liquid, with its reflection */}
        <div style={{position: 'absolute', left: 540 - w / 2 - 40, top: FLOOR - h - 40, width: w + 80, height: h + 40, overflow: 'hidden'}}>
          <div style={{position: 'absolute', left: 40, top: 40 + (1 - rise) * (h + 20), width: w, height: h}}>
            <Img src={staticFile('p/' + p.img)} style={{width: w, height: h, display: 'block', borderRadius: 8,
              filter: `drop-shadow(0 0 22px ${p.c2}) drop-shadow(0 0 4px ${p.c1})`}} />
            {sweep > -0.3 && sweep < 1.3 && <div style={{position: 'absolute', inset: 0, mixBlendMode: 'screen', borderRadius: 8,
              background: `linear-gradient(105deg, rgba(255,255,255,0) ${sweep * 100 - 12}%, rgba(255,250,235,0.5) ${sweep * 100}%, rgba(255,255,255,0) ${sweep * 100 + 12}%)`}} />}
          </div>
        </div>
        <div style={{position: 'absolute', left: 540 - w / 2, top: FLOOR, width: w, height: h * 0.55, overflow: 'hidden', opacity: 0.32 * rise,
          WebkitMaskImage: 'linear-gradient(180deg, rgba(0,0,0,1), rgba(0,0,0,0))'}}>
          <Img src={staticFile('p/' + p.img)} style={{width: w, height: h, display: 'block', transform: 'scaleY(-1)', borderRadius: 8}} />
        </div>
        {f < hit + 1 && <div style={{position: 'absolute', left: 540 - 14, top: dropY - 20, width: 28, height: 40, borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
          background: `radial-gradient(circle at 35% 30%, #fff, ${p.c1} 45%, ${p.c2})`, boxShadow: `0 0 30px ${p.c1}`}} />}
      </AbsoluteFill>
      <div style={{position: 'absolute', top: 1640, width: '100%', textAlign: 'center', opacity: nameA, transform: `translateY(${(1 - nameA) * 14}px)`}}>
        <div style={{fontFamily: 'Corm', fontFeatureSettings: '"lnum" 1', fontSize: p.name[0].length > 18 ? 70 : 84, color: '#f6e7cf', letterSpacing: 2}}>{p.name[0]}</div>
        {p.name[1] && <div style={{marginTop: 8, fontFamily: 'JostLight', fontSize: p.name[1].length > 26 ? 24 : 30, letterSpacing: 7, color: '#d9b37a'}}>{p.name[1].toUpperCase()}</div>}
      </div>
      <GoldDust n={24} seed={'sd' + idx} opacity={0.45} />
    </AbsoluteFill>
  );
};

/** anamorphic light-flare cut between serums */
const Flare: React.FC<{c: string}> = ({c}) => {
  const f = useCurrentFrame();
  const a = Math.sin(Math.PI * interpolate(f, [0, 8], [0, 1], clamp));
  return a > 0.01 ? (
    <AbsoluteFill style={{mixBlendMode: 'screen', opacity: a}}>
      <div style={{position: 'absolute', left: -200, right: -200, top: 940, height: 40, background: `linear-gradient(90deg, rgba(0,0,0,0), ${c}, #ffffff, ${c}, rgba(0,0,0,0))`, filter: 'blur(6px)'}} />
      <AbsoluteFill style={{background: `radial-gradient(circle at 50% 50%, rgba(255,250,240,0.9), ${c}66 25%, rgba(0,0,0,0) 60%)`}} />
    </AbsoluteFill>
  ) : null;
};

/** wave wipe in the next scene's colour; covers the frame exactly at the cut */
const Wave: React.FC<{c: string; c2: string; dur?: number}> = ({c, c2, dur = 10}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, dur], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const y = 1920 - p * 2400;                                          // top edge sweeps from bottom to above the top
  if (p <= 0 || p >= 1) return null;
  const amp = 70, ph = f * 0.9;
  const tail = y + 1150;                                              // the cover lifts off after the cut, wavy both edges
  let d = `M0 ${y}`;
  for (let x = 0; x <= 1080; x += 40) d += ` L${x} ${y + Math.sin(x / 140 + ph) * amp}`;
  for (let x = 1080; x >= 0; x -= 40) d += ` L${x} ${tail + Math.sin(x / 160 - ph) * amp}`;
  d += ' Z';
  return (
    <AbsoluteFill>
      <svg width={1080} height={1920} style={{position: 'absolute'}}>
        <defs><linearGradient id="wg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={c} /><stop offset="1" stopColor={c2} /></linearGradient></defs>
        <path d={d} fill="url(#wg)" />
      </svg>
    </AbsoluteFill>
  );
};

const DropHook: React.FC<{len: number}> = ({len}) => {
  const f = useCurrentFrame();
  const fall = interpolate(f, [0, len - 2], [-120, 960], {...clamp, easing: Easing.in(Easing.quad)});
  const hit = f >= len - 2;
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 50%, #1d1209, #070402)'}}>
      <div style={{position: 'absolute', left: 540 - 22, top: fall - 30, width: 44, height: 60, borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
        background: 'radial-gradient(circle at 35% 30%, #fff6d0, #ffc94d 45%, #c9780e 100%)', boxShadow: '0 0 40px rgba(255,190,80,0.6)'}} />
      {!hit && <div style={{position: 'absolute', left: 540 - 2, top: fall - 260, width: 4, height: 230,
        background: 'linear-gradient(180deg, rgba(255,200,90,0), rgba(255,200,90,0.5))'}} />}
    </AbsoluteFill>
  );
};

const Pops: React.FC<{len: number}> = ({len}) => {
  const f = useCurrentFrame();
  const per = bf(0.5);
  const i = Math.min(5, Math.floor(f / per));
  const p = P[BOTTLES[i]];
  const lf = f - i * per;
  const sp = spring({frame: lf, fps: FPS, config: {damping: 10, stiffness: 260, mass: 0.5}});
  const ring = interpolate(f, [0, 10], [0, 1], clamp);
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: `radial-gradient(circle at 50% 48%, ${p.c1}, ${p.c2} 55%, ${p.c3})`}}>
      {f < 10 && <div style={{position: 'absolute', left: 540 - 1400 * ring, top: 960 - 1400 * ring, width: 2800 * ring, height: 2800 * ring,
        borderRadius: '50%', border: `${30 * (1 - ring)}px solid rgba(255,230,170,${1 - ring})`}} />}
      <div style={{position: 'absolute', top: 700, width: '100%', textAlign: 'center', fontFamily: 'MontBold', fontSize: 300, color: 'rgba(255,255,255,0.18)',
        transform: `scale(${1.4 - 0.4 * sp})`}}>{p.word.split('-')[0]}</div>
      <AbsoluteFill style={{transform: `scale(${0.7 + 0.3 * sp})`, transformOrigin: '50% 60%'}}>
        <Product p={p} x={540} base={1500} scale={1.05} reflect={false} />
      </AbsoluteFill>
      <AbsoluteFill style={{background: '#fff8ea', opacity: interpolate(lf, [0, 3], [0.7, 0], clamp)}} />
    </AbsoluteFill>
  );
};

const TitleScene: React.FC<{len: number}> = ({len}) => {
  const f = useCurrentFrame();
  const letters = 'PalmCare'.split('');
  const sub = interpolate(f, [16, 28], [0, 1], {...clamp, easing: easeOut});
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: 'radial-gradient(ellipse 80% 60% at 50% 40%, #fff8ec 0%, #f6dfc0 55%, #d9a46c 100%)'}}>
      <GoldDust n={50} seed="ttl" opacity={0.7} />
      <div style={{position: 'absolute', top: 250, width: '100%', display: 'flex', justifyContent: 'center'}}>
        {letters.map((ch, i) => {
          const s = spring({frame: f - i * 2, fps: FPS, config: {damping: 11, stiffness: 180, mass: 0.6}});
          return <span key={i} style={{display: 'inline-block', fontFamily: 'Corm', fontSize: 210, lineHeight: 1,
            transform: `translateY(${(1 - s) * -260}px)`, opacity: Math.min(1, s * 2),
            background: 'linear-gradient(180deg, #8a5a2b 0%, #c98a3c 50%, #6e3f17 100%)', WebkitBackgroundClip: 'text', color: 'transparent'}}>{ch}</span>;
        })}
      </div>
      <div style={{position: 'absolute', top: 490, width: '100%', textAlign: 'center', fontFamily: 'JostMed', fontSize: 40, letterSpacing: 22 + 14 * (1 - sub),
        color: '#5a3416', opacity: sub}}>THE COLLECTION</div>
      {BOTTLES.map((id, i) => {
        const s = spring({frame: f - 6 - i * 2, fps: FPS, config: {damping: 13, stiffness: 140, mass: 0.8}});
        const x = 115 + i * 170;
        const lift = Math.abs(i - 2.5) * 36;
        return (
          <div key={id} style={{position: 'absolute', inset: 0, transform: `translateY(${(1 - s) * 1200}px)`}}>
            <Product p={P[id]} x={x} base={1640 + lift} scale={0.55} reflect={false} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const Finale: React.FC<{len: number}> = ({len}) => {
  const f = useCurrentFrame();
  const packs = ['n10', 'vitac', 'box', 'derma', 'glow'];
  const flash = interpolate(f, [0, 10], [0.85, 0], clamp);
  const push = 1 + 0.05 * interpolate(f, [0, len], [0, 1], clamp);
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: 'radial-gradient(ellipse 80% 55% at 50% 45%, #ffe7c2 0%, #e9a35c 55%, #7a3e14 100%)'}}>
      <AbsoluteFill style={{transform: `scale(${push})`, transformOrigin: '50% 60%'}}>
        <div style={{position: 'absolute', left: 0, right: 0, top: 1060, height: 18, background: 'linear-gradient(180deg, #fff4e0, #c98a4a)', boxShadow: '0 12px 30px rgba(60,25,0,0.35)'}} />
        <div style={{position: 'absolute', left: 0, right: 0, top: 1560, height: 360, background: 'linear-gradient(180deg, #f3d7b0, #b9773d)'}} />
        {packs.map((id, i) => {
          const s = spring({frame: f - i * 2, fps: FPS, config: {damping: 13, stiffness: 150}});
          return <div key={id} style={{position: 'absolute', inset: 0, transform: `translateY(${(1 - s) * -900}px)`}}>
            <Product p={P[id]} x={120 + i * 210} base={1062} scale={id === 'box' ? 0.27 : 0.3} reflect={false} />
          </div>;
        })}
        {BOTTLES.map((id, i) => {
          const s = spring({frame: f - 6 - i * 2, fps: FPS, config: {damping: 13, stiffness: 150}});
          return <div key={id} style={{position: 'absolute', inset: 0, transform: `translateY(${(1 - s) * 900}px)`}}>
            <Product p={P[id]} x={95 + i * 178} base={1565} scale={0.45} reflect={false} />
          </div>;
        })}
      </AbsoluteFill>
      <GoldDust n={90} seed="fn" opacity={0.95} />
      <AbsoluteFill style={{background: '#fff6e6', opacity: flash}} />
    </AbsoluteFill>
  );
};

const EndScene: React.FC<{len: number}> = ({len}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const fin = (s: number, d = 0.4) => interpolate(t, [s, s + d], [0, 1], {...clamp, easing: easeOut});
  const slog2 = spring({frame: f - Math.round(1.0 * FPS), fps: FPS, config: {damping: 12, stiffness: 120}});
  const btn = spring({frame: f - Math.round(3.0 * FPS), fps: FPS, config: {damping: 11, stiffness: 140}});
  const pulse = 1 + 0.035 * Math.max(0, Math.sin((2 * Math.PI * t) / B)) * fin(3.6);
  const rise = (i: number) => spring({frame: f - 4 - i * 2, fps: FPS, config: {damping: 14, stiffness: 120}});
  const row = ['milky', 'cacao', 'citrus', 'box', 'molecular', 'tropical', 'dermalight'];
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: 'radial-gradient(ellipse 75% 50% at 50% 50%, #8c4a1a 0%, #3a1a08 55%, #140803 100%)'}}>
      <GoldDust n={70} seed="end" opacity={0.85} />
      <div style={{position: 'absolute', left: 0, right: 0, top: 1300, height: 620, background: 'linear-gradient(180deg, #2c1306, #120602)'}} />
      <div style={{position: 'absolute', left: 60, right: 60, top: 1299, height: 2, background: 'linear-gradient(90deg, rgba(255,205,96,0), #ffcd60, rgba(255,205,96,0))'}} />
      {row.map((id, i) => {
        const s = rise(Math.abs(i - 3));
        const x = 90 + i * 150;
        return <div key={id} style={{position: 'absolute', inset: 0, opacity: Math.min(1, s * 1.5), transform: `translateY(${(1 - s) * 140}px)`}}>
          <Product p={P[id]} x={x} base={1300} scale={id === 'box' ? 0.4 : 0.5} reflect />
        </div>;
      })}
      <OrangeBurst at={2} cx={540} cy={1050} n={14} seed="v7e" fadeAt={24} />
      <div style={{position: 'absolute', top: 150, width: '100%', textAlign: 'center', fontFamily: 'JostMed', fontSize: 30, letterSpacing: 16, color: '#ffd27a', opacity: fin(0.3)}}>PALMCARE</div>
      <div style={{position: 'absolute', top: 198, left: '50%', width: 220 * fin(0.4, 0.5), height: 2, transform: 'translateX(-50%)',
        background: 'linear-gradient(90deg, rgba(255,205,96,0), #ffcd60, rgba(255,205,96,0))'}} />
      <div style={{position: 'absolute', top: 240, width: '100%', textAlign: 'center', fontFamily: 'Corm', fontSize: 108, color: '#fff7ea',
        opacity: fin(0.5), transform: `translateY(${(1 - fin(0.5)) * 18}px)`}}>Pamper your skin</div>
      <div style={{position: 'absolute', top: 350, width: '100%', textAlign: 'center', fontFamily: 'CormItalic', fontSize: 140,
        opacity: Math.min(1, slog2 * 2), transform: `scale(${0.85 + 0.15 * slog2})`,
        background: 'linear-gradient(180deg, #fff3cc 10%, #ffcd60 55%, #e8902e 100%)', WebkitBackgroundClip: 'text', color: 'transparent'}}>with PalmCare.</div>
      <div style={{position: 'absolute', left: 80, width: 920, top: 1400, height: 320, borderRadius: 34,
        opacity: fin(1.7), transform: `translateY(${(1 - fin(1.7, 0.5)) * 60}px)`,
        background: 'linear-gradient(180deg, rgba(70,34,12,0.9), rgba(30,14,5,0.95))', border: '1.5px solid rgba(255,205,96,0.8)',
        boxShadow: '0 20px 60px rgba(0,0,0,0.5)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
        {['0903 055 5424', '0809 361 2901'].map((n, i) => (
          <div key={n} style={{fontFamily: 'JostMed', fontSize: 60, letterSpacing: 2, color: '#fff4e2', opacity: fin(2.0 + 0.25 * i),
            display: 'flex', alignItems: 'center', gap: 18, lineHeight: '82px'}}>
            <span style={{width: 32, height: 32, borderRadius: '50%', display: 'inline-block', background: 'radial-gradient(circle, #ffd58a 0 45%, #f08024 47% 100%)'}} />{n}
          </div>
        ))}
        <div style={{width: 760, height: 1, background: 'rgba(255,205,96,0.5)', margin: '12px 0', opacity: fin(2.5)}} />
        <div style={{fontFamily: 'JostLight', fontSize: 33, color: '#fff4e2', opacity: fin(2.55), lineHeight: '46px'}}>Shop A67, Kogi Plaza, BBA Market,</div>
        <div style={{fontFamily: 'JostLight', fontSize: 33, color: '#ffcd60', opacity: fin(2.7), lineHeight: '46px'}}>Trade Fair Complex, Lagos</div>
      </div>
      <div style={{position: 'absolute', top: 1775, left: '50%', transform: `translateX(-50%) scale(${(0.6 + 0.4 * btn) * pulse})`,
        opacity: Math.min(1, btn * 2), padding: '22px 70px', borderRadius: 60, fontFamily: 'JostMed', fontSize: 34, letterSpacing: 9,
        color: '#2a1406', background: 'linear-gradient(180deg, #ffe39a, #ffc04d 55%, #e9902c)', boxShadow: '0 10px 30px rgba(0,0,0,0.4)'}}>ORDER NOW</div>
    </AbsoluteFill>
  );
};

const colorOf = (s?: Scene): [string, string] => (s?.id ? [P[s.id].c2, P[s.id].c3] : s?.k === 'finale' ? ['#ffe7c2', '#e9a35c'] : ['#fff8ec', '#d9a46c']);

/** premium finish over everything: soft vignette + fine animated film grain */
const FilmFinish: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 80% 66% at 50% 48%, rgba(0,0,0,0) 58%, rgba(10,4,0,0.34) 100%)'}} />
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0, opacity: 0.07, mixBlendMode: 'overlay'}}>
        <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={f % 50} /></filter>
        <rect width="100%" height="100%" filter="url(#grain)" />
      </svg>
    </AbsoluteFill>
  );
};

export const V7b: React.FC = () => (
  <AbsoluteFill style={{background: '#000'}}>
    {SCENES.map((s, i) => {
      const from = SF[i];
      const len = (i + 1 < SCENES.length ? SF[i + 1] : TOTAL_F) - from;
      const node = s.k === 'drop' ? <DropHook len={len} /> : s.k === 'pops' ? <Pops len={len} /> : s.k === 'title' ? <TitleScene len={len} />
        : s.k === 'prod' ? <ProdScene p={P[s.id!]} len={len} idx={i - 3} /> : s.k === 'card' ? <FaceCard len={len} />
        : s.k === 'serum' ? <SerumScene p={P[s.id!]} len={len} idx={i} /> : s.k === 'finale' ? <Finale len={len} /> : <EndLux />;
      return <Sequence key={i} from={from} durationInFrames={len}>{node}</Sequence>;
    })}
    {/* liquid wave wipes into each product world (and the finale), centred on the cut */}
    {SCENES.map((s, i) => (i >= 3 && (s.k === 'prod' || s.k === 'finale')) ? (
      <Sequence key={'w' + i} from={SF[i] - 5} durationInFrames={10}>
        <Wave c={colorOf(s)[0]} c2={colorOf(s)[1]} />
      </Sequence>
    ) : (s.k === 'serum' || s.k === 'card') ? (
      <Sequence key={'f' + i} from={SF[i] - 4} durationInFrames={8}>
        <Flare c={s.id ? P[s.id].c1 : '#ffd88a'} />
      </Sequence>
    ) : null)}
    {/* Remotion light leaks over the big moments */}
    {SCENES.map((s, i) => (s.k === 'title' || s.k === 'card' || s.k === 'finale' || s.k === 'end') ? (
      <Sequence key={'lk' + i} from={SF[i] - 6} durationInFrames={16}>
        <AbsoluteFill style={{mixBlendMode: 'screen', opacity: 0.5}}><Leak seed={i} hueShift={s.k === 'card' ? 330 : 0} /></AbsoluteFill>
      </Sequence>
    ) : null)}
    <FilmFinish />
  </AbsoluteFill>
);
