import React from 'react';
import {lightLeak} from '@remotion/effects/light-leak';
import {AbsoluteFill, interpolate, Solid, useCurrentFrame, useVideoConfig} from 'remotion';

export const Leak: React.FC<{seed?: number; hueShift?: number}> = ({seed = 0, hueShift = 0}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, height, width} = useVideoConfig();
  return (
    <Solid width={width} height={height} effects={[lightLeak({seed, hueShift,
      progress: interpolate(frame, [0, durationInFrames - 1], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})})]} />
  );
};
export const LeakTest: React.FC = () => <AbsoluteFill style={{background: '#333'}}><Leak seed={3} /></AbsoluteFill>;
