import React from 'react';
import {Composition} from 'remotion';
import {LabPaperThrow} from './LabPaperThrow';

export const Root: React.FC = () => (
  <Composition id="labPaperThrow" component={LabPaperThrow} durationInFrames={300} fps={30} width={1920} height={1080} />
);
