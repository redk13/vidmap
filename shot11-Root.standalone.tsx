import {Composition} from 'remotion';
import {LabWebExcerpt} from './LabWebExcerpt';

export const Root: React.FC = () => (
  <Composition id="labWebExcerpt" component={LabWebExcerpt} durationInFrames={300} fps={30} width={1920} height={1080} />
);
