import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {clamp, easeOut, Glint, GoldDust, LightSweep, OrangeBurst} from './fx';
import {loadFonts} from './fonts';

loadFonts();

/** One continuous shot on the client's product photo (real labels): slow push-in with the PALMCARE titles, then the
 * end card grows out of it: orange burst + warm bloom, the titles hand over to the slogan, a frosted espresso
 * contact panel rises over the marble, ORDER NOW pulses on the beat. HERO = seconds of hero before the end card. */
export const HERO_S = 3.0;
export const HeroEnd: React.FC = () => {
  const f = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = f / fps;
  const E = HERO_S;                                                    // end card starts
  const p = interpolate(f, [0, durationInFrames - 1], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const z = 1.0 + 0.08 * p;                                           // one long, smooth push
  const fin = (s: number, d = 0.4) => interpolate(t, [s, s + d], [0, 1], {...clamp, easing: easeOut});
  const fout = (s: number, d = 0.3) => 1 - interpolate(t, [s, s + d], [0, 1], clamp);
  const ec = fin(E, 0.6);
  const slog2 = spring({frame: f - Math.round((E + 0.9) * fps), fps, config: {damping: 12, stiffness: 120}});
  const btn = spring({frame: f - Math.round((E + 3.0) * fps), fps, config: {damping: 11, stiffness: 140}});
  const pulse = 1 + 0.035 * Math.max(0, Math.sin((2 * Math.PI * t) / (60 / 113))) * fin(E + 3.6);
  return (
    <AbsoluteFill style={{background: '#e9b77c', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `scale(${z}) translateY(${-40 * p}px)`, transformOrigin: '50% 60%'}}>
        <Img src={staticFile('hero_fixed.png')} style={{width: 1080, height: 1920}} />
      </AbsoluteFill>
      <LightSweep start={6} dur={36} strength={0.26} />
      <Glint x={356} y={1158 - 30 * p} at={30} size={110} />
      <Glint x={356} y={1158 - 30 * p} at={Math.round((E + 2.2) * fps)} size={90} />
      <GoldDust n={45} seed="he" opacity={0.55} />
      {/* end-card grade: warm top veil for the slogan, darker base under the panel */}
      <AbsoluteFill style={{opacity: ec, background: 'linear-gradient(180deg, rgba(44,20,6,0.62) 0%, rgba(44,20,6,0.25) 26%, rgba(0,0,0,0) 40%, rgba(0,0,0,0) 66%, rgba(30,13,4,0.55) 82%, rgba(24,10,3,0.8) 100%)'}} />

      {/* hero titles (hand over to the slogan) */}
      <div style={{position: 'absolute', top: 210, width: '100%', textAlign: 'center', opacity: fin(0.15) * fout(E - 0.2),
        transform: `translateY(${(1 - fin(0.15)) * 16}px)`, fontFamily: 'MontSemi', fontSize: 74, letterSpacing: 18, color: '#fff',
        textShadow: '0 4px 24px rgba(90,40,0,0.45)'}}>PALMCARE</div>
      <div style={{position: 'absolute', top: 312, width: '100%', textAlign: 'center', opacity: fin(0.4) * fout(E - 0.2),
        fontFamily: 'MontSemi', fontSize: 38, letterSpacing: 5, color: '#ffe2a8', textShadow: '0 3px 18px rgba(90,40,0,0.5)'}}>
        VITAMIN C FACE MOISTURISER</div>

      <OrangeBurst at={Math.round((E - 0.1) * fps)} cx={540} cy={1060} n={16} seed="he" fadeAt={Math.round(1.0 * fps)} />

      {/* slogan */}
      <div style={{position: 'absolute', top: 128, width: '100%', textAlign: 'center', fontFamily: 'JostMed', fontSize: 30, letterSpacing: 16,
        color: '#ffd27a', opacity: fin(E + 0.3)}}>PALMCARE</div>
      <div style={{position: 'absolute', top: 176, left: '50%', width: 220 * fin(E + 0.4, 0.5), height: 2, transform: 'translateX(-50%)',
        background: 'linear-gradient(90deg, rgba(255,205,96,0), #ffcd60, rgba(255,205,96,0))'}} />
      <div style={{position: 'absolute', top: 214, width: '100%', textAlign: 'center', fontFamily: 'Corm', fontSize: 104, color: '#fff7ea',
        opacity: fin(E + 0.45), transform: `translateY(${(1 - fin(E + 0.45)) * 18}px)`, textShadow: '0 4px 26px rgba(40,15,0,0.55)'}}>
        Pamper your skin</div>
      <div style={{position: 'absolute', top: 322, width: '100%', textAlign: 'center', fontFamily: 'CormItalic', fontSize: 136,
        opacity: Math.min(1, slog2 * 2), transform: `scale(${0.85 + 0.15 * slog2})`,
        background: 'linear-gradient(180deg, #fff3cc 10%, #ffcd60 55%, #e8902e 100%)', WebkitBackgroundClip: 'text', color: 'transparent',
        filter: 'drop-shadow(0 6px 20px rgba(40,15,0,0.55))'}}>with PalmCare.</div>

      {/* frosted contact panel */}
      <div style={{position: 'absolute', left: 80, width: 920, top: 1430, height: 320, borderRadius: 34, overflow: 'hidden',
        opacity: fin(E + 1.7), transform: `translateY(${(1 - fin(E + 1.7, 0.5)) * 60}px)`,
        background: 'linear-gradient(180deg, rgba(58,28,10,0.82), rgba(26,12,4,0.9))', border: '1.5px solid rgba(255,205,96,0.8)',
        boxShadow: '0 20px 60px rgba(0,0,0,0.45)', backdropFilter: 'blur(14px)',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
        {['0903 055 5424', '0809 361 2901'].map((n, i) => (
          <div key={n} style={{fontFamily: 'JostMed', fontSize: 60, letterSpacing: 2, color: '#fff4e2', opacity: fin(E + 2.0 + 0.25 * i),
            display: 'flex', alignItems: 'center', gap: 18, lineHeight: '82px'}}>
            <span style={{width: 32, height: 32, borderRadius: '50%', display: 'inline-block',
              background: 'radial-gradient(circle, #ffd58a 0 45%, #f08024 47% 100%)'}} />{n}
          </div>
        ))}
        <div style={{width: 760, height: 1, background: 'rgba(255,205,96,0.5)', margin: '12px 0', opacity: fin(E + 2.5)}} />
        <div style={{fontFamily: 'JostLight', fontSize: 33, color: '#fff4e2', opacity: fin(E + 2.55), lineHeight: '46px'}}>Shop A67, Kogi Plaza, BBA Market,</div>
        <div style={{fontFamily: 'JostLight', fontSize: 33, color: '#ffcd60', opacity: fin(E + 2.7), lineHeight: '46px'}}>Trade Fair Complex, Lagos</div>
      </div>
      <div style={{position: 'absolute', top: 1785, left: '50%', transform: `translateX(-50%) scale(${(0.6 + 0.4 * btn) * pulse})`,
        opacity: Math.min(1, btn * 2), padding: '22px 70px', borderRadius: 60, fontFamily: 'JostMed', fontSize: 34, letterSpacing: 9,
        color: '#2a1406', background: 'linear-gradient(180deg, #ffe39a, #ffc04d 55%, #e9902c)', boxShadow: '0 10px 30px rgba(0,0,0,0.35)'}}>
        ORDER NOW</div>
    </AbsoluteFill>
  );
};
