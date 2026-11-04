import {Composition} from 'remotion';
import {LabNeonFrames} from './LabNeonFrames';

export const Root: React.FC = () => (
  <Composition id="labNeonFrames" component={LabNeonFrames} durationInFrames={300} fps={30} width={1920} height={1080} />
);
