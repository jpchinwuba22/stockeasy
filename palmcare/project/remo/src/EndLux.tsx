import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {GoldDust} from './fx';
import {loadFonts} from './fonts';

loadFonts();

/** Video 7 end card, "The Gold Arch": an art-deco gold arch draws itself on deep espresso, a warm light pool opens
 * inside it, the full PalmCare collection rises onto a two-tier marble-and-gold plinth (face-care packs on the upper
 * tier, body care flanking the Vitamin C box on the lower tier), slow gold rays turn behind, then the letter-spaced
 * brand, the slogan in gold foil with a shine, gold hairline dividers, phone numbers and address with drawn icons, and
 * an ORDER NOW pill with a recurring sheen, pulsing on the beat. */
const EASE = Easing.bezier(0.16, 1, 0.3, 1);
const c = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const AR: Record<string, number> = {'box_straight.png': 1100 / 855, 'cacao.png': 702 / 1908, 'citrus_cut.png': 488 / 1390,
  'dermalight_cut.png': 509 / 1316, 'dermaluxe_box_final.png': 710 / 1248, 'glowshield_box_flat.png': 583 / 1295, 'milky.png': 762 / 1924,
  'molecular_cut.png': 471 / 1384, 'n10_real_final.png': 710 / 1248, 'tropical_cut.png': 495 / 1362, 'vitac_real_final.png': 710 / 1248};

const Item: React.FC<{img: string; x: number; base: number; h?: number; w?: number; delay: number; rounded?: boolean}> = ({img, x, base, h, w, delay, rounded}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: f - delay, fps, config: {damping: 15, stiffness: 120, mass: 0.9}});
  const H = h ?? w! / AR[img];
  const W = H * AR[img];
  return (
    <div style={{position: 'absolute', left: x - W / 2, top: base - H, width: W, height: H, opacity: Math.min(1, s * 1.6),
      translate: `0px ${(1 - s) * 90}px`}}>
      <div style={{position: 'absolute', left: -W * 0.15, top: H - 14, width: W * 1.3, height: 28, borderRadius: '50%',
        background: 'radial-gradient(ellipse, rgba(0,0,0,0.55), rgba(0,0,0,0) 70%)'}} />
      <Img src={staticFile('p/' + img)} style={{position: 'absolute', inset: 0, width: W, height: H, borderRadius: rounded ? 6 : 0,
        filter: 'drop-shadow(0 10px 14px rgba(0,0,0,0.45)) drop-shadow(0 0 10px rgba(255,200,120,0.18))'}} />
    </div>
  );
};

const GoldLine: React.FC<{top: number; w: number; at: number}> = ({top, w, at}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [at, at + 14], [0, 1], {...c, easing: EASE});
  return (
    <div style={{position: 'absolute', top, left: 540 - (w / 2) * p, width: w * p, height: 1.5,
      background: 'linear-gradient(90deg, rgba(255,205,96,0), #f6d68e 30%, #fff1c8 50%, #f6d68e 70%, rgba(255,205,96,0))'}}>
      <div style={{position: 'absolute', left: '50%', top: -5, width: 10, height: 10, translate: '-5px 0px', rotate: '45deg', background: '#f6d68e', opacity: p}} />
    </div>
  );
};

export const EndLux: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const beat = 60 / 112;
  const arch = interpolate(f, [4, 26], [0, 1], {...c, easing: Easing.inOut(Easing.cubic)});
  const pool = interpolate(f, [12, 30], [0, 1], {...c, easing: EASE});
  const plinth = interpolate(f, [14, 26], [0, 1], {...c, easing: EASE});
  const brand = interpolate(f, [8, 20], [0, 1], {...c, easing: EASE});
  const s1 = interpolate(f, [26, 38], [0, 1], {...c, easing: EASE});
  const s2 = spring({frame: f - 34, fps, config: {damping: 12, stiffness: 120}});
  const shine = interpolate(f, [44, 70], [-0.3, 1.3], c);
  const info = (d: number) => interpolate(f, [d, d + 12], [0, 1], {...c, easing: EASE});
  const btn = spring({frame: f - 84, fps, config: {damping: 11, stiffness: 140}});
  const sheen = ((f - 96) % 48) / 48;
  const pulse = 1 + 0.03 * Math.max(0, Math.sin((2 * Math.PI * t) / beat)) * info(96);
  const ARCH_L = 70, ARCH_R = 1010, ARCH_TOP = 560, ARCH_BOT = 1360;
  const r = (ARCH_R - ARCH_L) / 2;
  const archPath = `M ${ARCH_L} ${ARCH_BOT} L ${ARCH_L} ${ARCH_TOP + r} A ${r} ${r} 0 0 1 ${ARCH_R} ${ARCH_TOP + r} L ${ARCH_R} ${ARCH_BOT}`;
  const archLen = 2 * (ARCH_BOT - ARCH_TOP - r) + Math.PI * r;
  const LOW = 1352, UP = 1045;
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: 'radial-gradient(ellipse 85% 60% at 50% 52%, #3a1b0a 0%, #1c0c05 55%, #0a0402 100%)'}}>
      {/* slow gold rays turning behind the arch */}
      <AbsoluteFill style={{opacity: 0.22 * pool, rotate: `${f * 0.12}deg`, scale: '1.6',
        background: 'repeating-conic-gradient(from 0deg at 50% 52%, rgba(255,205,120,0.35) 0deg 4deg, rgba(0,0,0,0) 4deg 18deg)',
        WebkitMaskImage: 'radial-gradient(circle at 50% 52%, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 45%)'}} />
      {/* light pool inside the arch */}
      <div style={{position: 'absolute', left: ARCH_L, top: ARCH_TOP, width: ARCH_R - ARCH_L, height: ARCH_BOT - ARCH_TOP, opacity: pool,
        borderRadius: `${r}px ${r}px 0 0`, overflow: 'hidden',
        background: 'radial-gradient(ellipse 70% 55% at 50% 72%, rgba(255,196,120,0.55), rgba(140,70,20,0.25) 55%, rgba(30,12,4,0.1) 100%)'}} />
      <GoldDust n={70} seed="lux" opacity={0.75} />
      {/* the arch, drawn */}
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <defs>
          <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#fff1c8" /><stop offset="0.35" stopColor="#e7b75f" /><stop offset="0.6" stopColor="#fbe3a2" /><stop offset="1" stopColor="#b9822f" />
          </linearGradient>
        </defs>
        <path d={archPath} fill="none" stroke="url(#gold)" strokeWidth={4} strokeDasharray={archLen} strokeDashoffset={archLen * (1 - arch)} />
        <path d={`M ${ARCH_L + 22} ${ARCH_BOT} L ${ARCH_L + 22} ${ARCH_TOP + r} A ${r - 22} ${r - 22} 0 0 1 ${ARCH_R - 22} ${ARCH_TOP + r} L ${ARCH_R - 22} ${ARCH_BOT}`}
          fill="none" stroke="url(#gold)" strokeWidth={1.4} opacity={0.7} strokeDasharray={archLen} strokeDashoffset={archLen * (1 - arch)} />
        <circle cx={540} cy={ARCH_TOP} r={7 * arch} fill="url(#gold)" />
      </svg>
      {/* two-tier plinth */}
      <div style={{opacity: plinth, translate: `0px ${(1 - plinth) * 30}px`}}>
        <div style={{position: 'absolute', left: 250, width: 580, top: UP, height: LOW - UP - 26,
          background: 'linear-gradient(90deg, #cdb79b, #f4e8d6 35%, #e8d6bd 65%, #b89e7f)', boxShadow: 'inset 0 2px 0 #f6d68e'}} />
        <div style={{position: 'absolute', left: 250, width: 580, top: UP - 1, height: 3, background: 'linear-gradient(90deg, #b9822f, #fff1c8, #b9822f)'}} />
        <div style={{position: 'absolute', left: 90, width: 900, top: LOW - 26, height: 90,
          background: 'linear-gradient(90deg, #bba487, #f6ecdd 35%, #ecdcc4 65%, #a88d6d)', boxShadow: '0 30px 60px rgba(0,0,0,0.5)'}} />
        <div style={{position: 'absolute', left: 90, width: 900, top: LOW - 27, height: 3, background: 'linear-gradient(90deg, #b9822f, #fff1c8, #b9822f)'}} />
        <div style={{position: 'absolute', left: 90, width: 900, top: LOW + 61, height: 2, background: 'linear-gradient(90deg, #8a5f22, #f6d68e, #8a5f22)'}} />
      </div>
      {/* the collection: face-care packs on the upper tier, body care flanking the Vitamin C box below */}
      <Item img="vitac_real_final.png" x={290} base={UP} h={290} delay={30} rounded />
      <Item img="n10_real_final.png" x={440} base={UP} h={290} delay={28} rounded />
      <Item img="dermaluxe_box_final.png" x={640} base={UP} h={290} delay={28} rounded />
      <Item img="glowshield_box_flat.png" x={790} base={UP} h={290} delay={30} rounded />
      <Item img="milky.png" x={150} base={LOW - 26} h={385} delay={26} />
      <Item img="cacao.png" x={262} base={LOW - 26} h={385} delay={24} />
      <Item img="citrus_cut.png" x={368} base={LOW - 26} h={385} delay={22} />
      <Item img="box_straight.png" x={540} base={LOW - 26} w={300} delay={18} rounded />
      <Item img="molecular_cut.png" x={712} base={LOW - 26} h={385} delay={22} />
      <Item img="tropical_cut.png" x={818} base={LOW - 26} h={385} delay={24} />
      <Item img="dermalight_cut.png" x={930} base={LOW - 26} h={385} delay={26} />
      {/* typography */}
      <div style={{position: 'absolute', top: 120, width: '100%', textAlign: 'center', fontFamily: 'JostMed', fontSize: 32, letterSpacing: 18 + 10 * (1 - brand),
        color: '#f6d68e', opacity: brand}}>PALMCARE</div>
      <GoldLine top={176} w={260} at={14} />
      <div style={{position: 'absolute', top: 214, width: '100%', textAlign: 'center', fontFamily: 'Corm', fontSize: 100, color: '#fbf1e1',
        opacity: s1, translate: `0px ${(1 - s1) * 16}px`, filter: `blur(${(1 - s1) * 6}px)`}}>Pamper your skin</div>
      <svg width={1080} height={220} style={{position: 'absolute', left: 0, top: 300, overflow: 'visible', opacity: Math.min(1, s2 * 2),
        scale: `${0.86 + 0.14 * s2}`, transformOrigin: '540px 110px'}}>
        <defs>
          <linearGradient id="slog" x1="0" y1="0" x2="1" y2="0.25">
            <stop offset="0" stopColor="#e9b65a" />
            <stop offset={Math.min(1, Math.max(0, shine - 0.08))} stopColor="#fff3cf" />
            <stop offset={Math.min(1, Math.max(0, shine))} stopColor="#ffffff" />
            <stop offset={Math.min(1, Math.max(0, shine + 0.08))} stopColor="#fff3cf" />
            <stop offset="1" stopColor="#d4953a" />
          </linearGradient>
          <filter id="slogsh" x="-10%" y="-30%" width="120%" height="160%"><feDropShadow dx="0" dy="6" stdDeviation="9" floodColor="#000" floodOpacity="0.55" /></filter>
        </defs>
        <text x={540} y={150} textAnchor="middle" fontFamily="CormItalic" fontSize={138} fill="url(#slog)" filter="url(#slogsh)">with PalmCare.</text>
      </svg>
      {/* contact block */}
      <GoldLine top={1482} w={760} at={60} />
      <div style={{position: 'absolute', top: 1505, width: '100%', display: 'flex', justifyContent: 'center', gap: 56, opacity: info(64), translate: `0px ${(1 - info(64)) * 20}px`}}>
        {['0903 055 5424', '0809 361 2901'].map((n) => (
          <div key={n} style={{display: 'flex', alignItems: 'center', gap: 14, fontFamily: 'JostMed', fontSize: 50, letterSpacing: 1, color: '#fbf1e1'}}>
            <svg width={34} height={34} viewBox="0 0 24 24"><path fill="#f6d68e" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1l-2.3 2.2z" /></svg>
            {n}
          </div>
        ))}
      </div>
      <div style={{position: 'absolute', top: 1592, width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12,
        opacity: info(72), fontFamily: 'JostLight', fontSize: 33, color: '#e9d6b6'}}>
        <svg width={26} height={26} viewBox="0 0 24 24"><path fill="#f6d68e" d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z" /></svg>
        Shop A67, Kogi Plaza, BBA Market, Trade Fair Complex, Lagos
      </div>
      <GoldLine top={1660} w={760} at={74} />
      <div style={{position: 'absolute', top: 1720, left: '50%', translate: '-50% 0px', scale: `${(0.6 + 0.4 * btn) * pulse}`, opacity: Math.min(1, btn * 2),
        padding: '24px 84px', borderRadius: 60, overflow: 'hidden', fontFamily: 'JostMed', fontSize: 36, letterSpacing: 10, color: '#2a1406',
        background: 'linear-gradient(180deg, #fff0bf, #f3c35e 50%, #d68f2c)', boxShadow: '0 12px 34px rgba(0,0,0,0.5), 0 0 30px rgba(255,190,90,0.25)'}}>
        ORDER NOW
        {f > 96 && <div style={{position: 'absolute', top: 0, bottom: 0, left: `${-30 + sheen * 160}%`, width: '25%',
          background: 'linear-gradient(100deg, rgba(255,255,255,0), rgba(255,255,255,0.8), rgba(255,255,255,0))'}} />}
      </div>
    </AbsoluteFill>
  );
};
