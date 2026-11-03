import React from 'react';
import {AbsoluteFill, Img, interpolate, OffthreadVideo, Sequence, spring, staticFile, useCurrentFrame, Easing} from 'remotion';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import TL from './timeline.json';
import {clamp, easeOut, LightSweep, GoldDust, Glint} from './fx';
import {zoomBlur} from './zoomBlur';
import {HeroEnd} from './HeroEnd';
import {loadFonts} from './fonts';

loadFonts();

const FPS = TL.fps;
const TF = Math.round(TL.T * FPS);
type Shot = {id: string; src?: string; from?: number; dur: number; z0?: number; z1?: number; fx?: number; fy?: number; warm?: boolean};
const SHOTS = TL.shots as Shot[];
const frames = (s: Shot) => Math.round(s.dur * FPS);
const STARTS = SHOTS.reduce<number[]>((a, s, k) => [...a, k === 0 ? 0 : a[k - 1] + frames(SHOTS[k - 1])], []);
export const totalFrames = () => STARTS[STARTS.length - 1] + frames(SHOTS[SHOTS.length - 1]);
const S = (id: string) => STARTS[SHOTS.findIndex((s) => s.id === id)] / FPS;

/** a clip with an eased (or locked-off) camera and a warm cinematic grade */
const Clip: React.FC<{s: Shot}> = ({s}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, frames(s) - 1], [0, 1], {...clamp, easing: Easing.inOut(Easing.ease)});
  const extra = f > frames(s) ? ((s.z1! - s.z0!) / frames(s)) * (f - frames(s)) : 0;
  const z = s.z0! + (s.z1! - s.z0!) * p + extra;
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#000'}}>
      <AbsoluteFill style={{transform: `scale(${z})`, transformOrigin: `${s.fx! * 100}% ${s.fy! * 100}%`}}>
        {s.src!.endsWith('.png') ? <Img src={staticFile(s.src!)} style={{width: 1080, height: 1920, objectFit: 'cover'}} /> :
        <OffthreadVideo src={staticFile(s.src!)} startFrom={Math.round(s.from! * FPS)} muted
          style={{width: 1080, height: 1920, objectFit: 'cover', filter: 'contrast(1.06) saturate(1.07) brightness(1.01)'}} />}
      </AbsoluteFill>
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(255,170,90,0.05), rgba(255,140,60,0.04))', mixBlendMode: 'soft-light'}} />
      {s.warm && <>
        {/* golden-hour grade for the new model's shots: warm amber soft-light wash + glowing top light (skin brightness unchanged) */}
        <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(255,160,70,0.30), rgba(255,130,50,0.22))', mixBlendMode: 'soft-light'}} />
        <AbsoluteFill style={{background: 'radial-gradient(ellipse 70% 40% at 50% 0%, rgba(255,190,110,0.30), rgba(255,170,90,0) 70%)', mixBlendMode: 'screen'}} />
      </>}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 75% 62% at 50% 48%, rgba(0,0,0,0) 55%, rgba(20,8,0,0.36) 100%)'}} />
    </AbsoluteFill>
  );
};

// ---------- word-by-word captions (timed to the spoken words) ----------
type W = [string, number, number, boolean?];          // word, start, end (global s), gold key word
const Caption: React.FC<{words: W[]; until: number}> = ({words, until}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const s = words[0][1] - 0.08;
  if (t < s || t >= until) return null;
  const a = Math.min(1, (t - s) / 0.1) * (1 - Math.min(1, Math.max(0, (t - (until - 0.15)) / 0.15)));
  return (
    <div style={{position: 'absolute', top: 1600, left: 60, right: 60, textAlign: 'center', opacity: a, display: 'flex', flexWrap: 'wrap',
      justifyContent: 'center', columnGap: 16, rowGap: 4, fontFamily: 'MontBold', fontSize: 64, lineHeight: '78px'}}>
      {words.map(([w, ws, we, gold], i) => {
        const fr = f - Math.round(ws * FPS);
        const sp = fr < 0 ? 0 : spring({frame: fr, fps: FPS, config: {damping: 18, stiffness: 120, mass: 0.8}});
        const active = t >= ws && t < we + 0.08;
        return (
          <span key={i} style={{display: 'inline-block', opacity: Math.min(1, sp * 1.6), transform: `translateY(${(1 - sp) * 12}px) scale(${0.85 + 0.15 * sp})`,
            color: gold ? '#ffcd60' : active ? '#fff3d6' : '#fff', WebkitTextStroke: '1.5px rgba(40,20,4,0.55)',
            textShadow: '0 4px 16px rgba(20,10,0,0.85), 0 0 2px rgba(30,18,8,0.9)'}}>{w}</span>
        );
      })}
    </div>
  );
};

const Chip: React.FC<{text: string; s: number; e: number; cx: number; cy: number}> = ({text, s, e, cx, cy}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  if (t < s || t >= e) return null;
  const u = t - s;
  const a = Math.min(1, u / 0.18) * (1 - Math.min(1, Math.max(0, (t - (e - 0.25)) / 0.25)));
  const sc = 0.8 + 0.2 * easeOut(Math.min(1, u / 0.3));
  return (
    <div style={{position: 'absolute', left: cx, top: cy, transform: `translate(-50%, -50%) scale(${sc})`, opacity: a,
      display: 'flex', alignItems: 'center', gap: 12, padding: '12px 26px 12px 14px', borderRadius: 40,
      background: 'rgba(255,250,240,0.94)', border: '2px solid #e8a03c', boxShadow: '0 6px 20px rgba(80,40,0,0.25)',
      fontFamily: 'MontBold', fontSize: 34, color: '#180e06', whiteSpace: 'nowrap'}}>
      <span style={{width: 26, height: 26, borderRadius: '50%', background: '#f08c1e', color: '#fff', fontSize: 18,
        display: 'flex', alignItems: 'center', justifyContent: 'center'}}>✓</span>{text}
    </div>
  );
};

const Title: React.FC<{text: string; s: number; e: number; top: number; size: number; track?: number}> = ({text, s, e, top, size, track = 6}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  if (t < s || t >= e) return null;
  const u = t - s;
  const a = Math.min(1, u / 0.25) * (1 - Math.min(1, Math.max(0, (t - (e - 0.2)) / 0.2)));
  return (
    <div style={{position: 'absolute', top: top + 12 * (1 - easeOut(Math.min(1, u / 0.4))), width: '100%', textAlign: 'center',
      opacity: a, fontFamily: 'MontSemi', fontSize: size, letterSpacing: track * (1 + 0.4 * (1 - easeOut(Math.min(1, u / 0.8)))),
      color: '#fff', textShadow: '0 4px 22px rgba(60,25,0,0.5)'}}>{text}</div>
  );
};

/** timed benefit pop-up: glass pill with a gold icon, springs in from the side with a slight tilt, shimmer sweep */
const Pop: React.FC<{text: string; icon: string; at: number; until: number; x: number; y: number; from: -1 | 1}> = ({text, icon, at, until, x, y, from}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  if (t < at || t >= until) return null;
  const sp = spring({frame: f - Math.round(at * FPS), fps: FPS, config: {damping: 11, stiffness: 170, mass: 0.7}});
  const out = 1 - Math.min(1, Math.max(0, (t - (until - 0.22)) / 0.22));
  const sh = interpolate(t - at, [0.25, 0.9], [-30, 130], clamp);
  return (
    <div style={{position: 'absolute', left: x, top: y, opacity: Math.min(1, sp * 1.5) * out,
      transform: `translate(-50%, -50%) translateX(${(1 - sp) * 140 * from}px) scale(${0.6 + 0.4 * sp}) rotate(${(1 - sp) * 6 * from}deg)`,
      display: 'flex', alignItems: 'center', gap: 16, padding: '16px 34px 16px 16px', borderRadius: 48, overflow: 'hidden',
      background: 'linear-gradient(180deg, rgba(255,252,246,0.95), rgba(255,240,220,0.92))', border: '2px solid #e9a440',
      boxShadow: '0 12px 30px rgba(90,40,0,0.3)', fontFamily: 'MontBold', fontSize: 34, letterSpacing: 2, color: '#2a1406', whiteSpace: 'nowrap'}}>
      <span style={{width: 44, height: 44, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24,
        color: '#fff', background: 'radial-gradient(circle at 35% 30%, #ffd27a, #f08c1e 70%)'}}>{icon}</span>{text}
      <div style={{position: 'absolute', top: 0, bottom: 0, left: `${sh}%`, width: '22%',
        background: 'linear-gradient(100deg, rgba(255,255,255,0), rgba(255,255,255,0.75), rgba(255,255,255,0))'}} />
    </div>
  );
};

export const POPS = (jar: number, swirl: number, lift: number) => [
  {text: 'BRIGHTENING', icon: '✦', at: jar + 1.15, until: swirl - 0.05, x: 540, y: 1470, from: -1 as const},
  {text: 'HYDRATING', icon: '◆', at: jar + 1.75, until: swirl - 0.05, x: 540, y: 1580, from: 1 as const},
  {text: 'TONE REFINING', icon: '✓', at: jar + 2.35, until: swirl - 0.05, x: 540, y: 1690, from: -1 as const},
  {text: 'VITAMIN C POWERED', icon: '✦', at: swirl + 0.15, until: lift + 1.95, x: 540, y: 1650, from: 1 as const},
];

const Flash: React.FC<{at: number}> = ({at}) => {
  const f = useCurrentFrame();
  const u = f / FPS - at;
  if (u < -0.2 || u > 0.5) return null;
  const a = u < 0 ? interpolate(u, [-0.2, 0], [0, 0.85]) : interpolate(u, [0, 0.45], [0.85, 0], clamp);
  return <AbsoluteFill style={{background: '#fff6e6', opacity: a}} />;
};

export const Ad: React.FC = () => {
  const hook = S('hook'), jar = S('jar'), actA = S('activesA'), prodA = S('prodA'), actB = S('activesB'), swirl = S('swirl');
  const appA = S('applyA'), prodB = S('prodB'), appB = S('applyB'), hero = S('heroend');
  const h = (t: number) => hook + t - 0.55;          // hook1.mp4 source time -> timeline
  const a = (t: number) => actA + t;                  // actives1.mp4 voice runs continuously under activesA / prodA / activesB
  const p = (t: number) => appA + t - 1.25;           // apply1.mp4 voice runs continuously under applyA / prodB / applyB
  const lit = (at: number, d = 1.1, k = 0.3) => (
    <Sequence from={Math.round(at * FPS)} durationInFrames={Math.round((d + 0.3) * FPS)} layout="none"><LightSweep start={0} dur={Math.round(d * FPS)} strength={k} /></Sequence>);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <TransitionSeries>
        {SHOTS.map((s, k) => {
          const last = k === SHOTS.length - 1;
          const len = frames(s) + (last ? 0 : TF);
          const node = s.id === 'heroend' ? <HeroEnd /> : <Clip s={s} />;
          return (
            <React.Fragment key={s.id}>
              <TransitionSeries.Sequence durationInFrames={len}>{node}</TransitionSeries.Sequence>
              {!last && <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames: TF})} />}
            </React.Fragment>
          );
        })}
      </TransitionSeries>
      {/* product moments: warm flash on the jar reveal, gold dust + light sweeps + glints on every product shot */}
      <Flash at={jar} />
      {lit(jar + 0.8, 1.3, 0.24)}
      <Sequence from={Math.round(jar * FPS)} durationInFrames={Math.round((actA - jar) * FPS)} layout="none"><GoldDust n={40} seed="j" opacity={0.6} /></Sequence>
      <Sequence from={Math.round(prodA * FPS)} durationInFrames={Math.round((actB - prodA) * FPS)} layout="none"><GoldDust n={55} seed="pa" opacity={0.75} /></Sequence>
      {lit(prodA + 0.1, 1.4, 0.3)}
      <Glint x={560} y={1080} at={Math.round((prodA + 1.6) * FPS)} size={110} />
      <Sequence from={Math.round(prodB * FPS)} durationInFrames={Math.round((appB - prodB) * FPS)} layout="none"><GoldDust n={55} seed="pb" opacity={0.75} /></Sequence>
      {lit(prodB, 1.2, 0.32)}
      {/* street hook */}
      <Caption until={h(1.95)} words={[['Wait!', h(0.74), h(1.38)]]} />
      <Caption until={h(3.6)} words={[['Your', h(2.14), h(2.38)], ['face', h(2.38), h(2.68), true], ['is', h(2.68), h(2.84)], ['glowing!', h(2.84), h(3.2), true]]} />
      <Caption until={h(4.66)} words={[['What', h(3.78), h(3.88)], ['do', h(3.88), h(4.02)], ['you', h(4.02), h(4.1)], ['use?', h(4.1), h(4.46)]]} />
      <Caption until={jar - 0.1} words={[['PalmCare', h(4.76), h(5.16), true], ['Vitamin', h(5.16), h(5.54)], ['C', h(5.54), h(5.92)],
        ['Face', h(5.92), h(6.24)], ['Moisturiser', h(6.24), h(6.74)]]} />
      {/* actives, part 1 */}
      <Caption until={a(1.0)} words={[['At', a(0.02), a(0.48)], ['the', a(0.48), a(0.6)], ['heart', a(0.6), a(0.84)], ['of', a(0.84), a(1.0)]]} />
      <Caption until={a(2.3)} words={[['PalmCare', a(1.02), a(1.42), true], ['Face', a(1.42), a(1.68)], ['Moisturiser', a(1.68), a(2.3)]]} />
      <Caption until={a(3.56)} words={[['is', a(2.3), a(2.52)], ['Vitamin', a(2.52), a(2.82), true], ['C,', a(2.82), a(3.0), true],
        ['our', a(3.02), a(3.14)], ['hero', a(3.14), a(3.3), true], ['ingredient,', a(3.3), a(3.56)]]} />
      <Caption until={a(4.92)} words={[['boosted', a(3.58), a(4.0)], ['with', a(4.0), a(4.16)], ['Alpha', a(4.16), a(4.42), true], ['Arbutin', a(4.42), a(4.92), true]]} />
      <Caption until={a(5.96)} words={[['and', a(4.92), a(5.04)], ['Tranexamic', a(5.04), a(5.54), true], ['Acid', a(5.54), a(5.96), true]]} />
      <Caption until={swirl - 0.05} words={[['for', a(5.96), a(6.18)], ['brighter,', a(6.18), a(6.54), true], ['more', a(6.9), a(6.98)],
        ['even-looking', a(6.98), a(7.54), true], ['skin.', a(7.54), a(7.86)]]} />
      {/* actives, part 2 + trust */}
      <Caption until={p(2.66)} words={[['while', p(1.68), p(1.82)], ['Squalane', p(1.82), p(2.44), true], ['and', p(2.44), p(2.66)]]} />
      <Caption until={p(3.72)} words={[['Hyaluronic', p(2.66), p(3.22), true], ['Acid', p(3.22), p(3.72), true]]} />
      <Caption until={p(6.6)} words={[['deliver', p(3.72), p(4.24)], ['deep,', p(4.24), p(4.7), true], ['lasting', p(4.7), p(5.46), true], ['hydration.', p(5.46), p(6.1), true]]} />
      <Caption until={p(9.45)} words={[['Trust', p(7.55), p(7.94)], ['me,', p(7.94), p(8.24)], ['you', p(8.48), p(8.58), true],
        ['need', p(8.58), p(8.82), true], ['this!', p(8.82), p(9.14), true]]} />
      {/* ingredient labels: on her white top (never on her face) or around the real jar */}
      <Chip text="VITAMIN C · HERO INGREDIENT" s={a(2.52)} e={prodA} cx={540} cy={1440} />
      <Chip text="ALPHA ARBUTIN" s={a(4.16)} e={actB} cx={1080 * 0.3} cy={520} />
      <Chip text="TRANEXAMIC ACID" s={a(5.04)} e={actB} cx={1080 * 0.7} cy={610} />
      <Chip text="SQUALANE" s={p(1.82)} e={prodB} cx={1080 * 0.3} cy={1440} />
      <Chip text="HYALURONIC ACID" s={p(2.66)} e={prodB} cx={1080 * 0.7} cy={1440} />
      <Pop text="DEEP, LASTING HYDRATION" icon="◆" at={prodB + 0.1} until={appB - 0.05} x={540} y={1450} from={1} />
      {[{text: 'BRIGHTENING', icon: '✦', at: jar + 1.15, x: 540, y: 1470, from: -1 as const}, {text: 'HYDRATING', icon: '◆', at: jar + 1.75, x: 540, y: 1580, from: 1 as const},
        {text: 'TONE REFINING', icon: '✓', at: jar + 2.35, x: 540, y: 1690, from: -1 as const}].map((pp, i) => <Pop key={i} {...pp} until={actA - 0.05} />)}
      <Pop text="VITAMIN C POWERED" icon="✦" at={swirl + 0.2} until={appA - 0.05} x={540} y={1650} from={1} />
      <Title text="5 POWER INGREDIENTS. ONE JAR." s={jar + 0.35} e={actA - 0.1} top={300} size={42} track={3} />
    </AbsoluteFill>
  );
};

export const TIMES = {S};
