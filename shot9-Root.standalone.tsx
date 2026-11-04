import React from 'react';
import {Composition} from 'remotion';
import {LabLaptopVideos} from './LabLaptopVideos';

export const Root: React.FC = () => (
  <Composition id="labLaptopVideos" component={LabLaptopVideos} durationInFrames={360} fps={30} width={1920} height={1080} />
);
