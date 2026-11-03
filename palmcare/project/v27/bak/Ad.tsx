import React from 'react';
import {AbsoluteFill, interpolate, OffthreadVideo, Sequence, spring, staticFile, useCurrentFrame, Easing} from 'remotion';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import TL from './timeline.json';
import {clamp, easeOut, LightSweep} from './fx';
import {zoomBlur} from './zoomBlur';
import {HeroEnd} from './HeroEnd';
import {loadFonts} from './fonts';

loadFonts();

const FPS = TL.fps;
const TF = Math.round(TL.T * FPS);
type Shot = {id: string; src?: string; from?: number; dur: number; z0?: number; z1?: number; fx?: number; fy?: number};
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
        <OffthreadVideo src={staticFile(s.src!)} startFrom={Math.round(s.from! * FPS)} muted
          style={{width: 1080, height: 1920, objectFit: 'cover', filter: 'contrast(1.06) saturate(1.07) brightness(1.01)'}} />
      </AbsoluteFill>
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(255,170,90,0.05), rgba(255,140,60,0.04))', mixBlendMode: 'soft-light'}} />
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
        const sp = fr < 0 ? 0 : spring({frame: fr, fps: FPS, config: {damping: 9, stiffness: 220, mass: 0.6}});
        const active = t >= ws && t < we + 0.08;
        return (
          <span key={i} style={{display: 'inline-block', opacity: Math.min(1, sp * 1.6), transform: `translateY(${(1 - sp) * 26}px) scale(${0.55 + 0.45 * sp})`,
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
      fontFamily: 'MontSemi', fontSize: 30, color: '#180e06', whiteSpace: 'nowrap'}}>
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
  const hook = S('hook'), name = S('name'), review = S('review'), swatch = S('swatch'), jar = S('jar'), swirl = S('swirl'), trust = S('trust');
  const dw = (t: number) => hook + t - 1.8;
  const dw2 = (t: number) => name + t - 6.3;
  const ew = (t: number) => review + t;
  const ew2 = (t: number) => trust + t - 7.6;
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <TransitionSeries>
        {SHOTS.map((s, k) => {
          const last = k === SHOTS.length - 1;
          const len = frames(s) + (last ? 0 : TF);
          const node = s.id === 'heroend' ? <HeroEnd /> : <Clip s={s} />;
          const next = SHOTS[k + 1]?.id;
          return (
            <React.Fragment key={s.id}>
              <TransitionSeries.Sequence durationInFrames={len}>{node}</TransitionSeries.Sequence>
              {!last && (
                <TransitionSeries.Transition presentation={next === 'jar' ? fade() : zoomBlur()} timing={linearTiming({durationInFrames: TF})} />
              )}
            </React.Fragment>
          );
        })}
      </TransitionSeries>
      <Flash at={jar} />
      <Sequence from={Math.round((jar + 0.8) * FPS)} durationInFrames={Math.round(1.6 * FPS)} layout="none">
        <LightSweep start={0} dur={Math.round(1.3 * FPS)} strength={0.22} />
      </Sequence>
      <Caption until={dw(2.95)} words={[['Wait…', dw(2.06), dw(2.7)]]} />
      <Caption until={dw(4.7)} words={[['Your', dw(3.32), dw(3.54)], ['face', dw(3.54), dw(3.86), true], ['is', dw(3.84), dw(4.02)], ['glowing!', dw(4.02), dw(4.38), true]]} />
      <Caption until={dw(5.62)} words={[['What', dw(4.86), dw(4.98)], ['do', dw(4.98), dw(5.1)], ['you', dw(5.1), dw(5.2)], ['use?', dw(5.2), dw(5.56)]]} />
      <Caption until={dw2(9.25)} words={[['PalmCare', dw2(6.48), dw2(7.08), true], ['Vitamin', dw2(7.08), dw2(7.4)], ['C', dw2(7.4), dw2(7.78)],
        ['Face', dw2(7.78), dw2(8.08)], ['Moisturiser', dw2(8.08), dw2(8.56)]]} />
      <Caption until={Math.min(ew(8.0), trust - 0.05)} words={[['for', ew(4.9), ew(5.38)], ['brighter,', ew(5.38), ew(5.86), true],
        ['even,', ew(6.36), ew(6.78), true], ['hydrated', ew(6.78), ew(7.3), true], ['skin.', ew(7.3), ew(7.82)]]} />
      <Caption until={ew2(9.95)} words={[['Trust', ew2(8.34), ew2(8.5)], ['me,', ew2(8.5), ew2(8.84)], ['you', ew2(9.02), ew2(9.14), true],
        ['need', ew2(9.14), ew2(9.36), true], ['this!', ew2(9.36), ew2(9.66), true]]} />
      {[['VITAMIN C', 0.0], ['NIACINAMIDE', 1.26], ['ALPHA ARBUTIN', 2.56], ['TRANEXAMIC ACID', 3.72]].map(([txt, at], k) => (
        <Chip key={k} text={txt as string} s={ew(at as number)} e={ew(4.85)} cx={1080 * (k % 2 === 0 ? 0.3 : 0.7)} cy={1610 + Math.floor(k / 2) * 86} />
      ))}
      {POPS(jar, swirl, S('lift')).map((p, i) => <Pop key={i} {...p} />)}
      <Title text="4 POWER ACTIVES. ONE JAR." s={jar + 0.35} e={swirl - 0.1} top={300} size={52} track={5} />
    </AbsoluteFill>
  );
};

export const TIMES = {S};
