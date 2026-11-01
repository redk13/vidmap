import React from 'react';
import {Series} from 'remotion';
import {ColdOpenV2} from './ColdOpenV2';
import {Act1V2} from './Act1V2';
import {PyramidsV2} from './PyramidsV2';
import {DiveV2} from './DiveV2';
import {TimeSqueezeV2} from './TimeSqueezeV2';
import {MachineV2} from './MachineV2';
import {BillV2} from './BillV2';
import {FinaleV2} from './FinaleV2';

// FULL VIDEO — 12,685 frames = 7:03 @30fps — V2 COLLAGE/SATELLITE SKIN
// scene starts: 0 / 1023 / 2532 / 3184 / 4857 / 6127 / 8903 / 10664
export const Full: React.FC = () => (
  <Series>
    <Series.Sequence durationInFrames={1023}><ColdOpenV2/></Series.Sequence>
    <Series.Sequence durationInFrames={1509}><Act1V2/></Series.Sequence>
    <Series.Sequence durationInFrames={652}><PyramidsV2/></Series.Sequence>
    <Series.Sequence durationInFrames={1673}><DiveV2/></Series.Sequence>
    <Series.Sequence durationInFrames={1270}><TimeSqueezeV2/></Series.Sequence>
    <Series.Sequence durationInFrames={2776}><MachineV2/></Series.Sequence>
    <Series.Sequence durationInFrames={1761}><BillV2/></Series.Sequence>
    <Series.Sequence durationInFrames={2021}><FinaleV2/></Series.Sequence>
  </Series>
);
