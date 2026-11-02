import {Composition} from 'remotion';
import {LabPaperWriting} from './LabPaperWriting';

export const Root: React.FC = () => (
  <Composition id="labPaperWriting" component={LabPaperWriting} durationInFrames={300} fps={30} width={1920} height={1080} />
);
