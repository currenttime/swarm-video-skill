import {bundle} from '@remotion/bundler';
import {getCompositions, renderStill, renderFrames} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';
// fileURLToPath handles non-ASCII paths and Windows drive letters correctly.
const {fileURLToPath}=await import('node:url');
const cwd=path.dirname(fileURLToPath(import.meta.url));
const out=path.resolve(cwd,'../checks');fs.mkdirSync(out,{recursive:true});
const browserExecutable=process.env.REMOTION_BROWSER_EXECUTABLE||undefined;
const serveUrl=await bundle({entryPoint:path.join(cwd,'src/index.ts'),publicDir:path.join(cwd,'public')});
const comps=await getCompositions(serveUrl,{browserExecutable});
const composition=comps.find(c=>c.id==='Screen-Swarm-Overlay');
if(!composition)throw new Error('Overlay composition missing');
fs.writeFileSync(path.join(out,'compositions.json'),JSON.stringify(comps,null,2));
const stills=[0,Math.floor(composition.durationInFrames*.25),Math.floor(composition.durationInFrames*.5),Math.floor(composition.durationInFrames*.9)];
for(const frame of stills){
  await renderStill({serveUrl,composition,browserExecutable,frame,output:path.join(out,`overlay-${frame}.png`),imageFormat:'png'});
}
if(process.argv.includes('--stills'))process.exit(0);
const outputDir=path.resolve(cwd,'../overlay');fs.mkdirSync(outputDir,{recursive:true});
let last=-1;
const result=await renderFrames({serveUrl,composition,browserExecutable,outputDir,imageFormat:'png',
  concurrency:Number(process.env.SWARM_VIDEO_CONCURRENCY||4),
  onFrameUpdate:n=>{const step=Math.floor(n/60);if(step!==last){last=step;console.log(`FRAMES ${n}/${composition.durationInFrames}`);}}});
fs.writeFileSync(path.join(out,'render.json'),JSON.stringify(result,null,2));
console.log('OVERLAY COMPLETE');
