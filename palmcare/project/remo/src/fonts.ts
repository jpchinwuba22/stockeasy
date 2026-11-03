import {continueRender, delayRender, staticFile} from 'remotion';

const FONTS: [string, string][] = [
  ['MontSemi', 'Montserrat-SemiBold.ttf'],
  ['MontBold', 'Montserrat-Bold.ttf'],
  ['Corm', 'Cormorant-SemiBold.ttf'],
  ['CormItalic', 'Cormorant-Italic.ttf'],
  ['JostMed', 'Jost-Medium.ttf'],
  ['JostLight', 'Jost-Light.ttf'],
  ['JostReg', 'Jost-Regular.ttf'],
];

let loaded = false;
export const loadFonts = () => {
  if (loaded || typeof window === 'undefined') return;
  loaded = true;
  const h = delayRender('fonts');
  Promise.all(
    FONTS.map(([name, file]) => {
      const f = new FontFace(name, `url(${staticFile(file)})`);
      return f.load().then((ff) => document.fonts.add(ff));
    }),
  ).then(() => continueRender(h));
};
