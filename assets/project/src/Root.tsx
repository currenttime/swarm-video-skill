import React from 'react';
import {AbsoluteFill, Composition} from 'remotion';
import {Film, Overlay} from './Workbench';
import D from './workbench-data.json';

export const RemotionRoot=()=> <>
  <Composition id="Screen-Swarm" component={Film} width={D.width} height={D.height} fps={D.fps} durationInFrames={D.durationInFrames}/>
  <Composition id="Screen-Swarm-Overlay" component={Overlay} width={D.width} height={D.height} fps={D.fps} durationInFrames={D.durationInFrames}/>
</>;
