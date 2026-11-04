import {Composition} from 'remotion';
import {LabAnimatedChart} from './LabAnimatedChart';

export const Root: React.FC = () => (
  <Composition id="labAnimatedChart" component={LabAnimatedChart} durationInFrames={300} fps={30} width={1920} height={1080} />
);
