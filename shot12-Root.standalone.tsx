import {Composition} from 'remotion';
import {LabNeonSequence} from './src/LabNeonSequence';

export const Root: React.FC = () => (
  <Composition id="labNeonSequence" component={LabNeonSequence} durationInFrames={300} fps={30} width={1920} height={1080} />
);
