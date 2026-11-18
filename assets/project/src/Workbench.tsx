import React from 'react';
import {AbsoluteFill, staticFile, useCurrentFrame} from 'remotion';
import {Video} from '@remotion/media';
import {CursorSwarm} from './Swarm';
import {MediaPreload, WorkspacePanels} from './WorkspacePanels';
import {timelineTransform} from './geometry';
import D from './workbench-data.json';
const C={bg:'#101619',panel:'#151D21',edge:'#303C42',muted:'#809198',text:'#D5DFE1',amber:'#EDBC69',cyan:'#79C8C4'};
const mono='Consolas, monospace';const sans='Arial, sans-serif';
const clamp=(v:number,a=0,b=1)=>Math.max(a,Math.min(b,v));
const text=(x:number,y:number,value:React.ReactNode,color=C.text,size=12,isMono=false)=><text x={x} y={y} fill={color} fontSize={size} fontFamily={isMono?mono:sans}>{value}</text>;
function wave(x:number,y:number,w:number,h:number,seed:number){
  const n=Math.max(3,Math.min(70,Math.floor(w/3)));let p='';
  for(let i=0;i<n;i++){const a=(.10+.30*Math.abs(Math.sin(i*1.73+seed))+.23*Math.abs(Math.sin(i*.31+seed*.41)))*h*.65;const xx=x+2+i/(n-1)*Math.max(1,w-4);p+=`M${xx.toFixed(1)} ${(y+h/2-a).toFixed(1)}V${(y+h/2+a).toFixed(1)}`;}
  return p;
}
const Timeline:React.FC<{frame:number}>=({frame})=>{
  const visible=D.clips.filter(p=>frame>p.at),head=D.playhead[Math.min(frame,D.playhead.length-1)];
  return <g>
    <defs>{D.clips.map(c=><clipPath key={c.id} id={`v3-${c.id}`}><rect x={c.x} y={c.y} width={c.w} height={c.h} rx={1.8}/></clipPath>)}</defs>
    <rect x={0} y={618} width={1920} height={398} fill="#10171B"/>
    <rect x={0} y={618} width={1920} height={31} fill="#1A2429"/>
    {text(20,638,'SEQUENCE 01',C.text,12,true)}{text(182,638,'11 TRACKS',C.cyan,10,true)}{text(289,638,`${String(visible.length).padStart(3,'0')} / 268 ELEMENTS`,C.amber,10,true)}
    {['LINK','SNAP','RIPPLE','MARKERS','KEYFRAMES'].map((s,i)=><g key={s}><rect x={588+i*113} y={625} width={101} height={17} rx={3} fill={i<2?'#31433F':'#263238'}/>{text(600+i*113,637,s,i<2?C.cyan:C.muted,9,true)}</g>)}
    {text(1600,638,`${D.speed}×   |   ${D.fps} FPS   |   SILENT`,C.muted,10,true)}
    <rect x={176} y={654} width={1714} height={15} rx={2} fill="#253139"/>
    {visible.map(c=><rect key={`mini-${c.id}`} x={c.x} y={655+c.track*.95} width={Math.max(1,c.w)} height={1} fill={c.color} fillOpacity={.65}/>)}
    <rect x={176} y={654} width={Math.max(1,head-176)} height={15} fill={C.amber} fillOpacity={.04}/>
    <line x1={head} x2={head} y1={652} y2={671} stroke={C.amber} strokeWidth={1.4}/>
    <rect x={0} y={673} width={1920} height={22} fill="#151F24"/>
    {Array.from({length:73},(_,i)=>{
      const x=176+i/72*1714;return <g key={i}><line x1={x} x2={x} y1={i%6===0?678:686} y2={695} stroke={i%6===0?'#74868C':'#39494F'} strokeWidth={.7}/>
        {i%6===0?text(x+4,684,`${String(Math.floor((i/72*D.timelineSeconds)/60)).padStart(2,'0')}:${String(Math.floor(i/72*D.timelineSeconds)%60).padStart(2,'0')}`,C.muted,9,true):null}</g>;
    })}
    {D.tracks.map(t=><g key={t.id}>
      <rect x={0} y={t.y} width={1920} height={t.h} fill={t.id%2?'#151D22':'#182126'}/><line x1={0} y1={t.y+t.h} x2={1920} y2={t.y+t.h} stroke="#29363C" strokeWidth={.5}/>
      <rect x={0} y={t.y} width={157} height={t.h} fill="#19242A"/>
      <rect x={9} y={t.y+6} width={3} height={t.h-12} rx={1.5} fill={t.color}/>
      {text(20,t.y+t.h/2+4,t.code,t.color,10,true)}{text(52,t.y+t.h/2+4,t.label.split(' / ')[0],C.text,9,true)}
      <circle cx={132} cy={t.y+t.h/2} r={3} fill="none" stroke={C.muted} strokeWidth={.7}/>
    </g>)}
    {visible.map(c=>{
      const age=frame-c.at,alpha=clamp(age/(5*D.timeScale)),selected=age<24*D.timeScale;const hasImage=c.kind==='video',hasWave=c.kind==='wave';
      return <g key={c.id} opacity={alpha}>
        <g clipPath={`url(#v3-${c.id})`}>
          <rect x={c.x} y={c.y} width={c.w} height={c.h} rx={1.8} fill={c.color} fillOpacity={hasImage?.47:hasWave?.22:.31}/>
          {hasImage?<><image href={staticFile('timeline-thumbnails.png')} x={176} y={c.y+10} width={1714} height={c.h-10} preserveAspectRatio="none"/><rect x={c.x} y={c.y} width={c.w} height={10} fill="#244D50"/></>:null}
          {hasWave?<><path d={wave(c.x,c.y,c.w,c.h,c.seed)} stroke={c.color} strokeWidth={1.05} strokeOpacity={.85}/><path d={`M${c.x} ${c.y+5}L${c.x+c.w*.2} ${c.y+7}L${c.x+c.w*.8} ${c.y+7}L${c.x+c.w} ${c.y+5}`} fill="none" stroke="#DAE3DC" strokeOpacity={.4} strokeWidth={.65}/></>:null}
          {c.kind==='motion'?<path d={`M${c.x+5} ${c.y+c.h-4}Q${c.x+c.w*.35} ${c.y+3} ${c.x+c.w*.6} ${c.y+c.h*.5}T${c.x+c.w-4} ${c.y+4}`} stroke={c.color} strokeWidth={1} fill="none"/>:null}
          {c.kind==='automation'?<><path d={`M${c.x+3} ${c.y+c.h*.7}L${c.x+c.w*.25} ${c.y+5}L${c.x+c.w*.62} ${c.y+c.h*.65}L${c.x+c.w-3} ${c.y+4}`} stroke={c.color} strokeWidth={1} fill="none"/>{[.05,.25,.62,.94].map((a,i)=><rect key={i} x={c.x+c.w*a-1.6} y={c.y+4+(i%2?0:c.h*.42)} width={3.2} height={3.2} fill={C.text} transform={`rotate(45 ${c.x+c.w*a} ${c.y+5.6+(i%2?0:c.h*.42)})`}/>)}</>:null}
          {c.kind==='transition'?<path d={`M${c.x+2} ${c.y+2}L${c.x+c.w-2} ${c.y+c.h-2}M${c.x+2} ${c.y+c.h-2}L${c.x+c.w-2} ${c.y+2}`} stroke={c.color} strokeWidth={.7}/>:null}
          {c.kind!=='wave'&&c.kind!=='automation'&&c.w>25?text(c.x+4,c.y+(hasImage?8:Math.min(13,c.h-3)),c.label,hasImage?'#D9EEEA':C.text,hasImage?8:8.5,true):null}
        </g>
        <rect x={c.x+.4} y={c.y+.4} width={c.w-.8} height={c.h-.8} rx={1.8} fill="none" stroke={selected?C.amber:c.color} strokeOpacity={selected?.95:.45} strokeWidth={selected?1.1:.65}/>
        {selected?<circle cx={c.x+Math.min(c.w-3,7)} cy={c.y+3.5} r={1.4} fill={C.amber}/>:null}
      </g>;
    })}
    {[1,2,3,4,5].map((s,i)=>{const x=176+s/6*1714;return <g key={s}><path d={`M${x-3} 689L${x} 685L${x+3} 689L${x} 693Z`} fill={C.amber} fillOpacity={.7}/><line x1={x} x2={x} y1={696} y2={989} stroke={C.amber} strokeOpacity={.08} strokeDasharray="2 5"/>{frame>(180+i*250)*D.timeScale?text(x+4,663,`M${i+1}`,C.amber,7,true):null}</g>;})}
    <line x1={head} x2={head} y1={676} y2={990} stroke="#E8D6B3" strokeWidth={1.25}/><path d={`M${head-4} 673H${head+4}V679L${head} 683L${head-4} 679Z`} fill={C.amber}/>
    <rect x={0} y={991} width={1920} height={25} fill="#11191D"/>{text(18,1007,'EDIT SESSION',C.muted,9,true)}
    {text(687,1007,`NESTED COMPOSITIONS   28    ·    LINKED TRACKS   11    ·    ${visible.length} ELEMENTS`,C.muted,9,true)}
    <rect x={1613} y={1001} width={268} height={3} rx={1.5} fill="#304047"/><rect x={1613} y={1001} width={268*visible.length/268} height={3} rx={1.5} fill={C.cyan}/>
  </g>;
};

export const Overlay:React.FC=()=>{
 const frame=useCurrentFrame();
 return <AbsoluteFill style={{pointerEvents:'none'}}>
  <MediaPreload frame={frame}/>
  <svg width="100%" height="100%" preserveAspectRatio="none" viewBox="0 0 1920 1016">
   <WorkspacePanels frame={frame}/>
   <g transform={timelineTransform}><Timeline frame={frame}/></g>
  </svg>
  <CursorSwarm crew={D.crew}/>
 </AbsoluteFill>;
};
export const Film:React.FC=()=> <AbsoluteFill style={{backgroundColor:C.bg}}>
 <Video src={staticFile('source-fast.mp4')} muted objectFit="fill" style={{width:'100%',height:'100%'}}/>
 <Overlay/>
</AbsoluteFill>;
