import {Composition} from 'remotion';
import {LabPaperMorph} from './LabPaperMorph';

export const Root: React.FC = () => (
  <Composition id="labPaperMorph" component={LabPaperMorph} durationInFrames={240} fps={30} width={1920} height={1080} />
);
