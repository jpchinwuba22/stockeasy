import React from 'react';
import {AbsoluteFill, Img, staticFile, useVideoConfig} from 'remotion';
import {loadFonts} from './fonts';

loadFonts();

/** PalmCare collection group shot (still): warm studio sweep with a soft key light, a two-tier travertine plinth with
 * gold edges, face-care packs on the upper tier, the six body-care bottles on the lower tier around the Vitamin C box
 * and jar. Soft contact shadows, floor reflections, gentle rim light. Real product photos at native proportions. */
const AR: Record<string, number> = {'box_straight.png': 1100 / 855, 'cacao.png': 702 / 1908, 'citrus_cut.png': 488 / 1390,
  'dermalight_cut.png': 509 / 1316, 'dermaluxe_box_final.png': 710 / 1248, 'glowshield_box_flat.png': 583 / 1295, 'milky.png': 762 / 1924,
  'molecular_cut.png': 471 / 1384, 'n10_real_final.png': 710 / 1248, 'tropical_cut.png': 495 / 1362, 'vitac_real_final.png': 710 / 1248,
  'jar_cut.png': 671 / 646};

const Item: React.FC<{img: string; x: number; base: number; h?: number; w?: number; flat?: boolean; reflect?: number}> = ({img, x, base, h, w, flat, reflect = 0.14}) => {
  const H = h ?? w! / AR[img];
  const W = H * AR[img];
  const r = flat ? 4 : 0;
  return (
    <>
      <div style={{position: 'absolute', left: x - W * 0.6, top: base - 10, width: W * 1.2, height: 20, borderRadius: '50%',
        background: 'radial-gradient(ellipse, rgba(50,32,16,0.55), rgba(50,32,16,0) 70%)'}} />
      <div style={{position: 'absolute', left: x - W / 2, top: base + 1, width: W, height: H * 0.25, overflow: 'hidden', opacity: reflect,
        WebkitMaskImage: 'linear-gradient(180deg, rgba(0,0,0,1), rgba(0,0,0,0))'}}>
        <Img src={staticFile('p/' + img)} style={{width: W, height: H, display: 'block', transform: 'scaleY(-1)', marginTop: -H * 0.75, borderRadius: r}} />
      </div>
      <div style={{position: 'absolute', left: x - W / 2, top: base - H, width: W, height: H,
        filter: 'drop-shadow(10px 14px 18px rgba(60,40,20,0.22))'}}>
        <Img src={staticFile('p/' + img)} style={{width: W, height: H, display: 'block', borderRadius: r}} />
        <div style={{position: 'absolute', inset: 0, borderRadius: r, mixBlendMode: 'soft-light',
          background: 'linear-gradient(100deg, rgba(255,255,255,0.28) 0%, rgba(255,255,255,0) 35%, rgba(0,0,0,0) 70%, rgba(0,0,0,0.16) 100%)',
          ...(flat ? {} : {WebkitMaskImage: `url(${staticFile('p/' + img)})`, WebkitMaskSize: '100% 100%'})} as React.CSSProperties} />
      </div>
    </>
  );
};

export const GroupShot: React.FC<{title?: boolean}> = ({title = false}) => {
  const {width: Wd, height: Hd} = useVideoConfig();
  const cx = Wd / 2;
  const UP = Hd * (title ? 0.6 : 0.55), LOW = Hd * (title ? 0.84 : 0.79);
  const ph = Hd / 1350;                              // design at 1080x1350, scales to any canvas height
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#d9cfc2'}}>
      <AbsoluteFill style={{background: 'linear-gradient(180deg, #d3c7b8 0%, #e2d9cd 50%, #ece5db 72%, #e3dace 100%)'}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 60% 40% at 50% 52%, rgba(255,251,244,0.95), rgba(255,250,242,0.4) 50%, rgba(255,250,242,0) 78%)'}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 95% 85% at 50% 50%, rgba(0,0,0,0) 55%, rgba(70,52,34,0.25) 100%)'}} />
      {/* two-tier plinth */}
      <div style={{position: 'absolute', left: cx - 380 * ph, width: 760 * ph, top: UP, height: LOW - UP - 18 * ph,
        background: 'linear-gradient(90deg, #cbb89f, #f3e9db 35%, #eadccb 65%, #bfa98d)'}} />
      <div style={{position: 'absolute', left: cx - 380 * ph, width: 760 * ph, top: UP - 1, height: 3 * ph, background: 'linear-gradient(90deg, #b9822f, #fff1c8, #b9822f)'}} />
      <div style={{position: 'absolute', left: cx - 530 * ph, width: 1060 * ph, top: LOW - 18 * ph, height: 70 * ph,
        background: 'linear-gradient(90deg, #c2ad92, #f6ecdf 35%, #ede0cf 65%, #b49d80)', boxShadow: `0 ${30 * ph}px ${60 * ph}px rgba(60,40,20,0.3)`}} />
      <div style={{position: 'absolute', left: cx - 530 * ph, width: 1060 * ph, top: LOW - 19 * ph, height: 3 * ph, background: 'linear-gradient(90deg, #b9822f, #fff1c8, #b9822f)'}} />
      {/* upper tier: face-care packs with the Vitamin C jar in the centre */}
      <Item img="n10_real_final.png" x={cx - 290 * ph} base={UP} h={270 * ph} flat />
      <Item img="vitac_real_final.png" x={cx - 145 * ph} base={UP} h={270 * ph} flat />
      <Item img="jar_cut.png" x={cx} base={UP + 2 * ph} w={130 * ph} />
      <Item img="dermaluxe_box_final.png" x={cx + 145 * ph} base={UP} h={270 * ph} flat />
      <Item img="glowshield_box_flat.png" x={cx + 285 * ph} base={UP} h={270 * ph} flat />
      {/* lower tier: body care either side of the Vitamin C box */}
      <Item img="milky.png" x={cx - 450 * ph} base={LOW - 18 * ph} h={330 * ph} />
      <Item img="cacao.png" x={cx - 320 * ph} base={LOW - 18 * ph} h={330 * ph} />
      <Item img="citrus_cut.png" x={cx - 196 * ph} base={LOW - 18 * ph} h={322 * ph} />
      <Item img="box_straight.png" x={cx} base={LOW - 18 * ph} w={230 * ph} flat />
      <Item img="molecular_cut.png" x={cx + 196 * ph} base={LOW - 18 * ph} h={322 * ph} />
      <Item img="tropical_cut.png" x={cx + 318 * ph} base={LOW - 18 * ph} h={330 * ph} />
      <Item img="dermalight_cut.png" x={cx + 446 * ph} base={LOW - 18 * ph} h={322 * ph} />
      {title && (
        <>
          <div style={{position: 'absolute', top: 90 * ph, width: '100%', textAlign: 'center', fontFamily: 'JostMed', fontSize: 26 * ph, letterSpacing: 16 * ph, color: '#7a5a38'}}>PALMCARE</div>
          <div style={{position: 'absolute', top: 128 * ph, left: cx - 80 * ph, width: 160 * ph, height: 1.5 * ph, background: '#b9822f'}} />
          <div style={{position: 'absolute', top: 150 * ph, width: '100%', textAlign: 'center', fontFamily: 'Corm', fontSize: 92 * ph, color: '#3b2a1e'}}>The Collection</div>
          <div style={{position: 'absolute', top: 262 * ph, width: '100%', textAlign: 'center', fontFamily: 'CormItalic', fontSize: 44 * ph, color: '#9a6430'}}>Pamper your skin with PalmCare.</div>
        </>
      )}
    </AbsoluteFill>
  );
};
