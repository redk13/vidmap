import {Composition} from 'remotion';
import {LabOnlineLine} from './LabOnlineLine';

export const Root: React.FC = () => (
  <Composition id="labOnlineLine" component={LabOnlineLine} durationInFrames={300} fps={30} width={1920} height={1080} />
);
