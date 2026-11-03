import React from 'react';
import {AbsoluteFill, interpolate, Easing} from 'remotion';
import type {TransitionPresentation, TransitionPresentationComponentProps} from '@remotion/transitions';

/** premium cross-zoom: the outgoing shot pushes in and blurs while the incoming shot settles from a slight zoom,
 * blur-to-sharp, with a warm light leak at the seam */
type P = Record<string, never>;
const ZoomBlur: React.FC<TransitionPresentationComponentProps<P>> = ({children, presentationDirection, presentationProgress}) => {
  const p = Easing.inOut(Easing.cubic)(presentationProgress);
  if (presentationDirection === 'exiting') {
    return (
      <AbsoluteFill style={{transform: `scale(${1 + 0.1 * p})`, filter: `blur(${10 * p}px)`}}>{children}</AbsoluteFill>
    );
  }
  const leak = Math.sin(Math.PI * presentationProgress);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{opacity: interpolate(p, [0, 0.6], [0, 1], {extrapolateRight: 'clamp'}),
        transform: `scale(${1.1 - 0.1 * p})`, filter: `blur(${10 * (1 - p)}px)`}}>{children}</AbsoluteFill>
      <AbsoluteFill style={{mixBlendMode: 'screen', opacity: leak * 0.55,
        background: 'radial-gradient(ellipse 70% 50% at 30% 35%, rgba(255,190,110,0.9), rgba(255,140,60,0.25) 45%, rgba(0,0,0,0) 75%)'}} />
    </AbsoluteFill>
  );
};

export const zoomBlur = (): TransitionPresentation<P> => ({component: ZoomBlur, props: {}});
