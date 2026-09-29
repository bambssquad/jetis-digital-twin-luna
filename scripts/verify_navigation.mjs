import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import * as n from '../web/dist/navigation.js';
const root=fileURLToPath(new URL('../',import.meta.url));
const data=JSON.parse(fs.readFileSync(root+'web/dist/assets/scene.json'));
const {walls,floors}=n.collisionData(data);
const checks=data.motions.map(m=>{
 const[x,y,z,w,d,h]=m.bounds;
 const start={x:x+w/2,y:1,z:-y-d-2},closed={...start},opened={...start};
 n.moveBody(closed,0,d+4,[...walls,...n.motionBoxes(m,0)],floors);
 n.moveBody(opened,0,d+4,[...walls,...n.motionBoxes(m,1)],floors);
 const north=['pintu-t1-36-row-a','pintu-t1-78-row-a'].includes(m.id),sign=north?1:-1;
 const p={x:x+w/2,y:0,z:-(y+sign*5)},active=[...walls,...n.motionBoxes(m,1)];
 const inboundBlocked=n.moveBody(p,0,sign*7,active,floors),inside={...p};
 const outboundBlocked=n.moveBody(p,0,-sign*7,active,floors);
 return {id:m.id,closedBlocks:closed.z < -y,openCrosses:opened.z > -y,
   stairsBothWays:!inboundBlocked&&!outboundBlocked&&Math.abs(inside.y-1)<.01&&Math.abs(p.y)<.01&&Math.abs(p.z+(y+sign*5))<.1};
});
const report={passed:checks.length===6&&checks.every(c=>c.closedBlocks&&c.openCrosses&&c.stairsBothWays),checks};
fs.writeFileSync(root+'verification/navigation.json',JSON.stringify(report,null,2));
console.log(JSON.stringify({passed:report.passed,doorRoutes:checks.length}));
process.exitCode=report.passed?0:1;
