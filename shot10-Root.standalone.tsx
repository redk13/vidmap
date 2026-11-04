import React from 'react';
import {Composition} from 'remotion';
import {LabHeadlineDrop} from './LabHeadlineDrop';

export const Root: React.FC = () => (
  <Composition id="labHeadlineDrop" component={LabHeadlineDrop} durationInFrames={300} fps={30} width={1920} height={1080} />
);
