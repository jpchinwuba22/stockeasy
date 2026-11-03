import React from 'react';
import {AbsoluteFill, Img, interpolate, OffthreadVideo, Sequence, spring, staticFile, useCurrentFrame, Easing} from 'remotion';
import TRACKS from './tracks.json';
import {clamp, easeOut, Glint, GoldDust, LightSweep, OrangeBurst} from './fx';
import {loadFonts} from './fonts';

loadFonts();

/** Video 7, "The PalmCare Collection", music-led showcase (client: no product explanations, packs for face care,
 * end card "Pamper your skin with PalmCare"). Every cut lands on the beat (112 BPM). Hook: a half-beat product rush
 * into a PALMCARE title slam. Body: each set opens wide, then a tracked hero camera on every bottle (the camera rides
 * the plate's own motion so the product stays upright and locked) with a designed push + tilt, whip cuts, light
 * glints. Packs punch in on their gold rays, the Vitamin C box, the collection finale, then the end card. */
export const FPS = 24;
export const BPM = 112;
const B = 60 / BPM;
export const bf = (beats: number) => Math.round(beats * B * FPS);

type Plate = 'P1' | 'P2' | 'P3';
const PL: Record<Plate, [number, number, number][]> = {     // (cx, base, h) in plate frame-0 coords
  P1: [[308, 1318, 840], [768, 1415, 820]],
  P2: [[368, 1246, 800], [702, 1358, 790]],
  P3: [[302, 1200, 830], [712, 1322, 800]],
};
const NAMES: Record<string, [string, string]> = {
  P1_0: ['Milky Hydro-Glow', 'Moisturising Body Wash'], P1_1: ['Cacao & Collagen', 'Body Lotion'],
  P2_0: ['Citrus Vitamin Glow Infusion', 'Body Wash'], P2_1: ['Molecular Glow', 'Body Lotion'],
  P3_0: ['Advanced Tropical Glow', 'Exfoliating Lightening Body Wash'], P3_1: ['Dermalight', 'Body Lotion'],
};

type Shot =
  | {k: 'rush'; plate?: Plate; idx?: number; src?: string; t: number; beats: number}
  | {k: 'title'; beats: number}
  | {k: 'wide'; plate: Plate; t: number; beats: number}
  | {k: 'hero'; plate: Plate; idx: number; t: number; beats: number}
  | {k: 'pack'; src: string; t: number; beats: number; name: [string, string]}
  | {k: 'box'; beats: number}
  | {k: 'finale'; beats: number}
  | {k: 'end'; beats: number};

export const SHOTS: Shot[] = [
  {k: 'rush', plate: 'P1', idx: 0, t: 1.0, beats: 0.5}, {k: 'rush', plate: 'P2', idx: 0, t: 2.5, beats: 0.5},
  {k: 'rush', src: 'PS_derma.mp4', t: 1.5, beats: 0.5}, {k: 'rush', plate: 'P3', idx: 1, t: 2.0, beats: 0.5},
  {k: 'rush', plate: 'P1', idx: 1, t: 3.0, beats: 0.5}, {k: 'rush', src: 'PS_vitac.mp4', t: 1.5, beats: 0.5},
  {k: 'rush', plate: 'P2', idx: 1, t: 4.0, beats: 0.5}, {k: 'rush', src: 'C_P9B.mp4', t: 2.0, beats: 0.5},
  {k: 'title', beats: 4},
  {k: 'wide', plate: 'P1', t: 0.4, beats: 2}, {k: 'hero', plate: 'P1', idx: 0, t: 1.5, beats: 4}, {k: 'hero', plate: 'P1', idx: 1, t: 3.6, beats: 4},
  {k: 'wide', plate: 'P2', t: 0.4, beats: 2}, {k: 'hero', plate: 'P2', idx: 0, t: 1.5, beats: 4}, {k: 'hero', plate: 'P2', idx: 1, t: 3.6, beats: 4},
  {k: 'wide', plate: 'P3', t: 0.4, beats: 2}, {k: 'hero', plate: 'P3', idx: 0, t: 1.5, beats: 4}, {k: 'hero', plate: 'P3', idx: 1, t: 3.6, beats: 4},
  {k: 'pack', src: 'PS_vitac.mp4', t: 0.6, beats: 3, name: ['Vita C+ Serum', '']},
  {k: 'pack', src: 'PS_n10.mp4', t: 0.6, beats: 3, name: ['N10 Niacinamide Serum', '']},
  {k: 'pack', src: 'PS_derma.mp4', t: 0.6, beats: 3, name: ['DermaLuxe Pro', 'Hydrating Night Repair Serum']},
  {k: 'pack', src: 'PS_glow.mp4', t: 0.8, beats: 3, name: ['GlowShield', 'Broad-Spectrum Daily Defense Sunscreen']},
  {k: 'box', beats: 4},
  {k: 'finale', beats: 4},
  {k: 'end', beats: 12},
];
// cumulative beat starts -> frames (rounded on the beat grid, so every cut lands on the music)
const BEATS: number[] = SHOTS.reduce<number[]>((a, s, i) => [...a, i === 0 ? 0 : a[i - 1] + SHOTS[i - 1].beats], []);
export const START_F = BEATS.map(bf);
export const TOTAL_F = bf(BEATS[BEATS.length - 1] + SHOTS[SHOTS.length - 1].beats);
export const SECTION_BEATS = {title: 4, p1: 8, p2: 18, p3: 28, packs: 38, box: 50, finale: 54, end: 58};

const M = (p: Plate, fr: number) => {
  const T = (TRACKS as Record<string, number[][][]>)[p];
  return T[Math.max(0, Math.min(T.length - 1, fr))];
};

/** video layer whose camera locks onto a bottle: rides the plate track, then a designed push + tilt */
const HeroCam: React.FC<{plate: Plate; idx: number; t: number; len: number; z0: number; z1: number; tilt?: number}> = ({plate, idx, t, len, z0, z1, tilt = 70}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, len], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const [cx, base, h] = PL[plate][idx];
  const m = M(plate, Math.round(t * FPS) + f);
  const ax0 = cx, ay0 = base - h * 0.52 + tilt * (0.5 - p);       // tilt: from lower body up toward the cap
  const ax = m[0][0] * ax0 + m[0][1] * ay0 + m[0][2];
  const ay = m[1][0] * ax0 + m[1][1] * ay0 + m[1][2];
  const s = Math.sqrt(Math.abs(m[0][0] * m[1][1] - m[0][1] * m[1][0]));
  const Z = (z0 + (z1 - z0) * p) / s;
  const vx = Math.min(Math.max(ax, 540 / Z), 1080 - 540 / Z);
  const vy = Math.min(Math.max(ay, 960 / Z), 1920 - 960 / Z);
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <AbsoluteFill style={{transformOrigin: '0 0', transform: `translate(540px, 960px) scale(${Z}) translate(${-vx}px, ${-vy}px)`}}>
        <OffthreadVideo src={staticFile(`C_${plate}.mp4`)} startFrom={Math.round(t * FPS)} muted style={{width: 1080, height: 1920}} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Plain: React.FC<{src: string; t: number; len: number; z0: number; z1: number; ox?: number; oy?: number}> = ({src, t, len, z0, z1, ox = 50, oy = 50}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, len], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `scale(${z0 + (z1 - z0) * p})`, transformOrigin: `${ox}% ${oy}%`}}>
        <OffthreadVideo src={staticFile(src)} startFrom={Math.round(t * FPS)} muted style={{width: 1080, height: 1920}} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** beat punch + whip in / whip out + grade, around any shot */
const Cut: React.FC<{len: number; dir: number; whip?: boolean; punch?: number; children: React.ReactNode}> = ({len, dir, whip = true, punch = 0.06, children}) => {
  const f = useCurrentFrame();
  const inP = interpolate(f, [0, 4], [1, 0], {...clamp, easing: Easing.out(Easing.cubic)});
  const outP = whip ? interpolate(f, [len - 3, len], [0, 1], {...clamp, easing: Easing.in(Easing.cubic)}) : 0;
  const tx = (whip ? inP * 170 * dir : 0) - outP * 170 * dir;
  const blur = (whip ? inP * 14 : inP * 4) + outP * 14;
  const sc = 1 + punch * Math.exp(-f / 4);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <AbsoluteFill style={{transform: `translateX(${tx}px) scale(${sc})`, filter: `blur(${blur}px) contrast(1.07) saturate(1.1)`}}>{children}</AbsoluteFill>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 78% 64% at 50% 48%, rgba(0,0,0,0) 56%, rgba(18,8,0,0.38) 100%)'}} />
    </AbsoluteFill>
  );
};

const Name: React.FC<{name: [string, string]; len: number; top?: number}> = ({name, len, top = 1560}) => {
  const f = useCurrentFrame();
  const a = interpolate(f, [5, 13], [0, 1], {...clamp, easing: easeOut}) * interpolate(f, [len - 7, len - 2], [1, 0], clamp);
  const wipe = interpolate(f, [5, 17], [0, 100], {...clamp, easing: easeOut});
  return (
    <div style={{position: 'absolute', top, width: '100%', textAlign: 'center', opacity: a, clipPath: `inset(0 ${100 - wipe}% 0 0)`}}>
      <div style={{fontFamily: 'Corm', fontSize: name[0].length > 20 ? 78 : 98, color: '#fff8ec', lineHeight: 1.05,
        textShadow: '0 4px 26px rgba(20,8,0,0.75)'}}>{name[0]}</div>
      {name[1] && <div style={{marginTop: 10, fontFamily: 'JostMed', fontSize: name[1].length > 26 ? 27 : 33, letterSpacing: 6,
        color: '#ffd27a', textShadow: '0 3px 14px rgba(20,8,0,0.8)'}}>{name[1].toUpperCase()}</div>}
      <div style={{margin: '14px auto 0', width: 180 * wipe / 100, height: 2,
        background: 'linear-gradient(90deg, rgba(255,205,96,0), #ffcd60, rgba(255,205,96,0))'}} />
    </div>
  );
};

const TitleSlam: React.FC = () => {
  const f = useCurrentFrame();
  const sp = spring({frame: f - 2, fps: FPS, config: {damping: 14, stiffness: 160, mass: 0.8}});
  const ring = interpolate(f, [2, 18], [0, 1], clamp);
  const sub = interpolate(f, [12, 22], [0, 1], {...clamp, easing: easeOut});
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: 540 - 520 * ring, top: 390 - 520 * ring, width: 1040 * ring, height: 1040 * ring, borderRadius: '50%',
        border: `${6 * (1 - ring)}px solid rgba(255,214,140,${0.8 * (1 - ring)})`}} />
      <div style={{position: 'absolute', top: 250, width: '100%', textAlign: 'center', fontFamily: 'Corm', fontSize: 178, letterSpacing: 6,
        transform: `scale(${2.2 - 1.2 * sp})`, opacity: Math.min(1, sp * 1.8), filter: `blur(${(1 - sp) * 10}px) drop-shadow(0 8px 30px rgba(20,8,0,0.6))`,
        background: 'linear-gradient(180deg, #fff6d8 0%, #ffd06a 55%, #e0892a 100%)', WebkitBackgroundClip: 'text', color: 'transparent'}}>PalmCare</div>
      <div style={{position: 'absolute', top: 478, width: '100%', textAlign: 'center', fontFamily: 'JostMed', fontSize: 40,
        letterSpacing: 22 + 14 * (1 - sub), color: '#fff8ec', opacity: sub, textShadow: '0 3px 18px rgba(20,8,0,0.8)'}}>THE COLLECTION</div>
    </AbsoluteFill>
  );
};

const Flash: React.FC<{len?: number; strength?: number}> = ({len = 9, strength = 0.85}) => {
  const f = useCurrentFrame();
  const a = interpolate(f, [0, len], [strength, 0], clamp);
  return a > 0.01 ? <AbsoluteFill style={{background: '#fff6e6', opacity: a}} /> : null;
};

const EndCard: React.FC<{len: number}> = ({len}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const p = interpolate(f, [0, len], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const fin = (s: number, d = 0.4) => interpolate(t, [s, s + d], [0, 1], {...clamp, easing: easeOut});
  const slog2 = spring({frame: f - Math.round(1.0 * FPS), fps: FPS, config: {damping: 12, stiffness: 120}});
  const btn = spring({frame: f - Math.round(3.0 * FPS), fps: FPS, config: {damping: 11, stiffness: 140}});
  const pulse = 1 + 0.035 * Math.max(0, Math.sin((2 * Math.PI * t) / B)) * fin(3.6);
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#2a1408'}}>
      <AbsoluteFill style={{transform: `scale(${1.04 + 0.06 * p}) translateY(${-30 * p}px)`, transformOrigin: '50% 60%'}}>
        <Img src={staticFile('group_last.png')} style={{width: 1080, height: 1920}} />
      </AbsoluteFill>
      <GoldDust n={50} seed="v7e" opacity={0.6} />
      <AbsoluteFill style={{opacity: fin(0, 0.6), background: 'linear-gradient(180deg, rgba(40,18,5,0.78) 0%, rgba(40,18,5,0.35) 25%, rgba(0,0,0,0) 38%, rgba(0,0,0,0) 62%, rgba(28,12,4,0.6) 78%, rgba(22,9,3,0.88) 100%)'}} />
      <OrangeBurst at={0} cx={540} cy={1000} n={16} seed="v7" fadeAt={24} />
      <div style={{position: 'absolute', top: 128, width: '100%', textAlign: 'center', fontFamily: 'JostMed', fontSize: 30, letterSpacing: 16,
        color: '#ffd27a', opacity: fin(0.3)}}>PALMCARE</div>
      <div style={{position: 'absolute', top: 176, left: '50%', width: 220 * fin(0.4, 0.5), height: 2, transform: 'translateX(-50%)',
        background: 'linear-gradient(90deg, rgba(255,205,96,0), #ffcd60, rgba(255,205,96,0))'}} />
      <div style={{position: 'absolute', top: 214, width: '100%', textAlign: 'center', fontFamily: 'Corm', fontSize: 104, color: '#fff7ea',
        opacity: fin(0.5), transform: `translateY(${(1 - fin(0.5)) * 18}px)`, textShadow: '0 4px 26px rgba(40,15,0,0.55)'}}>Pamper your skin</div>
      <div style={{position: 'absolute', top: 322, width: '100%', textAlign: 'center', fontFamily: 'CormItalic', fontSize: 136,
        opacity: Math.min(1, slog2 * 2), transform: `scale(${0.85 + 0.15 * slog2})`,
        background: 'linear-gradient(180deg, #fff3cc 10%, #ffcd60 55%, #e8902e 100%)', WebkitBackgroundClip: 'text', color: 'transparent',
        filter: 'drop-shadow(0 6px 20px rgba(40,15,0,0.55))'}}>with PalmCare.</div>
      <div style={{position: 'absolute', left: 80, width: 920, top: 1430, height: 320, borderRadius: 34, overflow: 'hidden',
        opacity: fin(1.7), transform: `translateY(${(1 - fin(1.7, 0.5)) * 60}px)`,
        background: 'linear-gradient(180deg, rgba(58,28,10,0.86), rgba(26,12,4,0.93))', border: '1.5px solid rgba(255,205,96,0.8)',
        boxShadow: '0 20px 60px rgba(0,0,0,0.45)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
        {['0903 055 5424', '0809 361 2901'].map((n, i) => (
          <div key={n} style={{fontFamily: 'JostMed', fontSize: 60, letterSpacing: 2, color: '#fff4e2', opacity: fin(2.0 + 0.25 * i),
            display: 'flex', alignItems: 'center', gap: 18, lineHeight: '82px'}}>
            <span style={{width: 32, height: 32, borderRadius: '50%', display: 'inline-block',
              background: 'radial-gradient(circle, #ffd58a 0 45%, #f08024 47% 100%)'}} />{n}
          </div>
        ))}
        <div style={{width: 760, height: 1, background: 'rgba(255,205,96,0.5)', margin: '12px 0', opacity: fin(2.5)}} />
        <div style={{fontFamily: 'JostLight', fontSize: 33, color: '#fff4e2', opacity: fin(2.55), lineHeight: '46px'}}>Shop A67, Kogi Plaza, BBA Market,</div>
        <div style={{fontFamily: 'JostLight', fontSize: 33, color: '#ffcd60', opacity: fin(2.7), lineHeight: '46px'}}>Trade Fair Complex, Lagos</div>
      </div>
      <div style={{position: 'absolute', top: 1785, left: '50%', transform: `translateX(-50%) scale(${(0.6 + 0.4 * btn) * pulse})`,
        opacity: Math.min(1, btn * 2), padding: '22px 70px', borderRadius: 60, fontFamily: 'JostMed', fontSize: 34, letterSpacing: 9,
        color: '#2a1406', background: 'linear-gradient(180deg, #ffe39a, #ffc04d 55%, #e9902c)', boxShadow: '0 10px 30px rgba(0,0,0,0.35)'}}>
        ORDER NOW</div>
    </AbsoluteFill>
  );
};

export const V7: React.FC = () => (
  <AbsoluteFill style={{background: '#000'}}>
    {SHOTS.map((s, i) => {
      const from = START_F[i];
      const len = (i + 1 < SHOTS.length ? START_F[i + 1] : TOTAL_F) - from;
      const dir = i % 2 === 0 ? 1 : -1;
      let body: React.ReactNode = null;
      let over: React.ReactNode = null;
      let whip = true;
      if (s.k === 'rush') {
        body = s.plate ? <HeroCam plate={s.plate} idx={s.idx!} t={s.t} len={len} z0={1.75} z1={1.6} tilt={0} />
          : <Plain src={s.src!} t={s.t} len={len} z0={1.35} z1={1.25} />;
      } else if (s.k === 'title') {
        body = <Plain src="L_hook2.mp4" t={2.2} len={len} z0={1.14} z1={1.02} oy={60} />;
        over = <><Flash /><TitleSlam /><GoldDust n={50} seed="tt" opacity={0.7} /></>;
      } else if (s.k === 'wide') {
        body = <Plain src={`C_${s.plate}.mp4`} t={s.t} len={len} z0={1.0} z1={1.07} oy={62} />;
        over = <><Flash len={6} strength={0.5} /><LightSweep start={2} dur={len} strength={0.2} /></>;
      } else if (s.k === 'hero') {
        body = <HeroCam plate={s.plate} idx={s.idx} t={s.t} len={len} z0={1.42} z1={1.58} />;
        over = <><Glint x={540 + 60 * dir} y={760} at={Math.round(len * 0.45)} size={110} /><Name name={NAMES[`${s.plate}_${s.idx}`]} len={len} /></>;
      } else if (s.k === 'pack') {
        body = <Plain src={s.src} t={s.t} len={len} z0={1.18} z1={1.04} oy={45} />;
        over = <><Flash len={7} strength={0.6} /><Name name={s.name} len={len} top={1540} /></>;
      } else if (s.k === 'box') {
        body = <Plain src="C_P9B.mp4" t={1.0} len={len} z0={1.0} z1={1.12} oy={58} />;
        over = <><LightSweep start={6} dur={30} strength={0.25} /><Name name={['Vitamin C', 'Face Moisturiser']} len={len} top={1540} /></>;
      } else if (s.k === 'finale') {
        body = <Plain src="L_group.mp4" t={0} len={len} z0={1.0} z1={1.08} oy={58} />;
        over = <><Flash len={10} /><GoldDust n={90} seed="fin" opacity={0.9} /><LightSweep start={4} dur={30} strength={0.3} /></>;
        whip = false;
      } else if (s.k === 'end') {
        body = <EndCard len={len} />;
        whip = false;
      }
      return (
        <Sequence key={i} from={from} durationInFrames={len}>
          <Cut len={len} dir={dir} whip={whip && s.k !== 'end'} punch={s.k === 'rush' ? 0.12 : s.k === 'end' ? 0 : 0.05}>{body}</Cut>
          {over}
        </Sequence>
      );
    })}
  </AbsoluteFill>
);
