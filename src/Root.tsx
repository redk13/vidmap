import {Composition} from 'remotion';
import {Smoke} from './Smoke';
import {MapTest} from './MapTest';
import {ColdOpen} from './ColdOpen';
import {Act1} from './Act1';
import {Pyramids} from './Pyramids';
import {Dive} from './Dive';
import {TimeSqueeze} from './TimeSqueeze';
import {Machine} from './Machine';
import {Bill} from './Bill';
import {Finale} from './Finale';
import {Full} from './Full';
import {ColdOpenV2} from './ColdOpenV2';
import {Act1V2} from './Act1V2';
import {PyramidsV2} from './PyramidsV2';
import {TimeSqueezeV2} from './TimeSqueezeV2';
import {DiveV2} from './DiveV2';
import {MachineV2} from './MachineV2';
import {BillV2} from './BillV2';
import {FinaleV2} from './FinaleV2';
import {LabBoard} from './LabBoard';
import {LabClip} from './LabClip';
import {LabPile} from './LabPile';
import {LabGrid} from './LabGrid';
import {LabCrumple} from './LabCrumple';
import {LabTear} from './LabTear';
import {LabTear6} from './LabTear6';
import {LabTearWall} from './LabTearWall';
import {LabDataCity} from './LabDataCity';
import {LabPaperThrow} from './LabPaperThrow';
import {LabLaptopVideos} from './LabLaptopVideos';
import {LabHeadlineDrop} from './LabHeadlineDrop';
export const Root: React.FC = () => (
  <>
    <Composition id="labHeadlineDrop" component={LabHeadlineDrop} durationInFrames={300} fps={30} width={1920} height={1080} />
    <Composition id="labLaptopVideos" component={LabLaptopVideos} durationInFrames={360} fps={30} width={1920} height={1080} />
    <Composition id="labPaperThrow" component={LabPaperThrow} durationInFrames={300} fps={30} width={1920} height={1080} />
    <Composition id="labDataCity" component={LabDataCity} durationInFrames={360} fps={30} width={1920} height={1080} />
    <Composition id="labTearWall" component={LabTearWall} durationInFrames={360} fps={30} width={1920} height={1080} />
    <Composition id="labTear6" component={LabTear6} durationInFrames={360} fps={30} width={1920} height={1080} />
    <Composition id="labTear" component={LabTear} durationInFrames={360} fps={30} width={1920} height={1080} />
    <Composition id="labCrumple" component={LabCrumple} durationInFrames={240} fps={30} width={1920} height={1080} />
    <Composition id="labGrid" component={LabGrid} durationInFrames={360} fps={30} width={1920} height={1080} />
    <Composition id="labPile" component={LabPile} durationInFrames={360} fps={30} width={1920} height={1080} />
    <Composition id="labClip" component={LabClip} durationInFrames={240} fps={30} width={1920} height={1080} />
    <Composition id="labBoard" component={LabBoard} durationInFrames={480} fps={30} width={1920} height={1080} />
    <Composition id="smoke" component={Smoke} durationInFrames={150} fps={30} width={1920} height={1080} />
    <Composition id="mapTest" component={MapTest} durationInFrames={120} fps={30} width={1920} height={1080} />
    <Composition id="coldOpen" component={ColdOpen} durationInFrames={1023} fps={30} width={1920} height={1080} />
    <Composition id="act1" component={Act1} durationInFrames={1509} fps={30} width={1920} height={1080} />
    <Composition id="pyramids" component={Pyramids} durationInFrames={652} fps={30} width={1920} height={1080} />
    <Composition id="dive" component={Dive} durationInFrames={1673} fps={30} width={1920} height={1080} />
    <Composition id="timeSqueeze" component={TimeSqueeze} durationInFrames={1270} fps={30} width={1920} height={1080} />
    <Composition id="machine" component={Machine} durationInFrames={2776} fps={30} width={1920} height={1080} />
    <Composition id="bill" component={Bill} durationInFrames={1761} fps={30} width={1920} height={1080} />
    <Composition id="finale" component={Finale} durationInFrames={2021} fps={30} width={1920} height={1080} />
    <Composition id="coldOpenV2" component={ColdOpenV2} durationInFrames={1023} fps={30} width={1920} height={1080} />
    <Composition id="act1V2" component={Act1V2} durationInFrames={1509} fps={30} width={1920} height={1080} />
    <Composition id="pyramidsV2" component={PyramidsV2} durationInFrames={652} fps={30} width={1920} height={1080} />
    <Composition id="timeSqueezeV2" component={TimeSqueezeV2} durationInFrames={1270} fps={30} width={1920} height={1080} />
    <Composition id="diveV2" component={DiveV2} durationInFrames={1673} fps={30} width={1920} height={1080} />
    <Composition id="machineV2" component={MachineV2} durationInFrames={2776} fps={30} width={1920} height={1080} />
    <Composition id="billV2" component={BillV2} durationInFrames={1761} fps={30} width={1920} height={1080} />
    <Composition id="finaleV2" component={FinaleV2} durationInFrames={2021} fps={30} width={1920} height={1080} />
    <Composition id="full" component={Full} durationInFrames={12685} fps={30} width={1920} height={1080} />
  </>
);
