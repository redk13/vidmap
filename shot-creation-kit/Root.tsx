import {Composition} from 'remotion';
import {PipelineCheck} from './PipelineCheck';

export const Root: React.FC = () => (
  <Composition id="pipelineCheck" component={PipelineCheck} durationInFrames={30} fps={30} width={1920} height={1080} />
);
