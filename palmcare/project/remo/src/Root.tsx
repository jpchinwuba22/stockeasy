import React from 'react';
import {Composition} from 'remotion';
import {Ad, totalFrames} from './Ad';
import {HeroEnd} from './HeroEnd';
import {V7, TOTAL_F} from './V7';
import {V7b, TOTAL_F as TF7b} from './V7b';
import {LeakTest} from './LeakTest';
import {Routine, TOTAL_F as TFR} from './Routine';
import {GroupShot} from './GroupShot';
import {Commercial, TOTAL as TCM} from './Commercial';

export const Root: React.FC = () => (
  <>
    <Composition id="Ad" component={Ad} durationInFrames={totalFrames()} fps={24} width={1080} height={1920} />
    <Composition id="HeroEnd" component={HeroEnd} durationInFrames={234} fps={24} width={1080} height={1920} />
    <Composition id="V7" component={V7} durationInFrames={TOTAL_F} fps={24} width={1080} height={1920} />
    <Composition id="V7b" component={V7b} durationInFrames={TF7b} fps={24} width={1080} height={1920} />
    <Composition id="LeakTest" component={LeakTest} durationInFrames={24} fps={24} width={1080} height={1920} />
    <Composition id="Routine" component={Routine} durationInFrames={TFR} fps={24} width={1080} height={1920} />
    <Composition id="GroupShot" component={GroupShot} durationInFrames={1} fps={24} width={1080} height={1350} defaultProps={{title: false}} />
    <Composition id="GroupShotTitle" component={GroupShot} durationInFrames={1} fps={24} width={1080} height={1350} defaultProps={{title: true}} />
    <Composition id="Commercial" component={Commercial} durationInFrames={TCM} fps={30} width={1080} height={1920} />
  </>
);
