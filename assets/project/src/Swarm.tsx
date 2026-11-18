import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import motion from './workbench-data.json';
import {mapPoint, timelineBounds} from './geometry';

type Point = [number, number];
type Feedback = {type: string; x: number; y: number; w: number; h: number; dx: number; dy: number; lane: string};
type Segment = {from: number; to: number; p0: number[]; p1: number[]; kind: string; bend: number; feedback?: Feedback};
type Worker = {id: string; name: string; color: string; role: string; size: number; phase: number; segments: Segment[]};
type State = {worker: Worker; p: Point; velocity: number; segment: Segment; u: number; opacity: number; label?: {x: number; y: number; w: number; h: number}};
const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
const smooth = (p: number) => p*p*(3-2*p);

export function stateAt(w: Worker, frame: number): State {
  let lo=0, hi=w.segments.length-1;
  while(lo<hi){const m=Math.floor((lo+hi)/2);if(w.segments[m].to<=frame)lo=m+1;else hi=m;}
  const s=w.segments[lo];
  const u=clamp((frame-s.from)/(s.to-s.from),0,1);
  const e=s.kind==='drag'||s.kind==='trim' ? smooth(u) : u<.5 ? 4*u*u*u : 1-Math.pow(-2*u+2,3)/2;
  const dx=s.p1[0]-s.p0[0],dy=s.p1[1]-s.p0[1];
  const bend=Math.sin(Math.PI*u)*s.bend;
  const p: Point=mapPoint([s.p0[0]+dx*e-dy*bend,s.p0[1]+dy*e+dx*bend]);
  return {worker:w,p,segment:s,u,velocity:Math.hypot(dx,dy)/(s.to-s.from)*(s.kind==='hold'?0:Math.sin(Math.PI*u)),opacity:clamp((frame+4)/8,.15,1)};
}

function labelLayout(states: State[]) {
  const occupied: {x:number;y:number;w:number;h:number}[]=[];
  for(const state of states){
    const {worker:w,p:[x,y]}=state;
    const width=w.name.length*6.25+17, height=19;
    const candidates=[[x+12,y+18],[x-width-4,y+17],[x+14,y-24],[x-width-6,y-23],[x+19,y+34],[x-width-9,y-38]];
    let best={x:0,y:0,w:width,h:height}, score=Infinity;
    for(let k=0;k<candidates.length;k++){
      const cx=clamp(candidates[k][0],timelineBounds[0]+5,timelineBounds[2]-width-5),cy=clamp(candidates[k][1],timelineBounds[1]+5,timelineBounds[3]-height-5);
      const r={x:cx,y:cy,w:width,h:height};let q=k*8;
      // Keep the content and portrait in the preview unobstructed.

      for(const a of occupied){const ow=Math.max(0,Math.min(cx+width,a.x+a.w)-Math.max(cx,a.x));const oh=Math.max(0,Math.min(cy+height,a.y+a.h)-Math.max(cy,a.y));q+=ow*oh*8;}
      if(q<score){score=q;best=r;}
    }
    state.label=best;occupied.push(best);
  }
  return states;
}

const Pointer: React.FC<{state: State; frame: number}>=({state,frame})=>{
  const {worker:w,p:[x,y],segment:s,u,label}=state;
  const press=(s.kind==='click'&&u<.2)||(s.kind==='drag'||s.kind==='trim');
  const scale=w.size*(press?.94:1);
  const tint=w.color;
  return <g opacity={state.opacity}>
    {s.kind==='click'&&u<.38?<circle cx={x+1} cy={y+1} r={3+u*23} fill="none" stroke={tint} strokeWidth={1.2} opacity={.5*(1-u/.38)}/>:null}
    {state.velocity>11&&s.kind==='move'?[2,4].map((d)=>{
      const prev=stateAt(w,frame-d);
      return <path key={d} d="M0 0 L1 20 L6 15 L10.5 24 L14.5 22 L10 13 L18.5 11 Z" fill={tint} opacity={d===2?.10:.045} transform={`translate(${prev.p[0]} ${prev.p[1]}) scale(${scale})`}/>;
    }):null}
    {s.kind==='trim'?<g transform={`translate(${x-10} ${y-9})`} stroke="#FFFFFF" strokeLinejoin="round"><path d="M0 10 L5 5 L5 8 L15 8 L15 5 L20 10 L15 15 L15 12 L5 12 L5 15 Z" fill={tint} strokeWidth={1.3}/></g>:
      <path d="M0 0 L1 20 L6 15 L10.5 24 L14.5 22 L10 13 L18.5 11 Z" fill={tint} stroke="#FFFFFF" strokeWidth={1.25} strokeLinejoin="round" transform={`translate(${x} ${y}) scale(${scale})`}/>
    }
    {label?<g>
      <rect x={label.x-.7} y={label.y-.7} width={label.w+1.4} height={label.h+1.4} rx={7.2} fill={tint} opacity={.18}/>
      <rect x={label.x} y={label.y} width={label.w} height={label.h} rx={6.4} fill={tint} stroke="#FFFFFF" strokeOpacity={.64} strokeWidth={.7}/>
      <text x={label.x+label.w/2} y={label.y+13.15} fill="#18232A" fontSize={11.2} fontWeight={750} fontFamily="Arial, 'Microsoft YaHei', sans-serif" textAnchor="middle" letterSpacing={.03}>{w.name}</text>
    </g>:null}
  </g>;
};

const FeedbackLayer: React.FC<{state: State}>=({state})=>{
  const {segment:s,worker:w,u}=state;const f=s.feedback;if(!f)return null;
  const p=smooth(u), color=w.color;
  const x=f.x+f.dx*p, y=f.y+f.dy*p;
  const alpha=Math.min(1,u/.12,(1-u)/.13)*.80;
  if(f.type==='trim'){
    const edge=f.dx>0?f.x+f.w+f.dx*p:f.x+f.dx*p;
    return <g opacity={alpha}>
      <rect x={Math.min(f.x,edge)} y={f.y} width={Math.max(12,f.w+f.dx*p)} height={f.h} fill={color} fillOpacity={.055} stroke={color} strokeWidth={1.15}/>
      <line x1={edge} y1={f.y-5} x2={edge} y2={f.y+f.h+5} stroke={color} strokeWidth={2}/>
      <path d={`M${edge-4} ${f.y-5}h8 M${edge-4} ${f.y+f.h+5}h8`} stroke={color} strokeWidth={1.2}/>
    </g>;
  }
  return <g opacity={alpha}>
    <rect x={f.x} y={f.y} width={f.w} height={f.h} rx={2} fill="none" stroke={color} strokeWidth={.8} strokeOpacity={.4} strokeDasharray="3 4"/>
    <rect x={x} y={y} width={f.w} height={f.h} rx={2} fill={color} fillOpacity={.09} stroke={color} strokeWidth={1.2}/>
    <line x1={x+f.w/2} y1={f.y-6} x2={x+f.w/2} y2={f.y+f.h+7} stroke={color} strokeWidth={.7} strokeOpacity={.5}/>
    <line x1={f.x+f.w/2} y1={f.y-7} x2={x+f.w/2} y2={f.y-7} stroke={color} strokeWidth={.8} strokeDasharray="2 3"/>
    {[0,1].flatMap((a)=>[0,1].map((b)=><rect key={`${a}-${b}`} x={x+a*f.w-1.8} y={y+b*f.h-1.8} width={3.6} height={3.6} fill="#E6F2EE" stroke={color} strokeWidth={.8}/>))}
  </g>;
};

export const CursorSwarm: React.FC<{offset?: number; crew?: Worker[]}>=({offset=0,crew=motion.crew})=>{
  const frame=useCurrentFrame()+offset;
  const states=labelLayout(crew.map((w)=>stateAt(w,frame)));
  return <AbsoluteFill style={{pointerEvents:'none',overflow:'hidden'}}>
    <svg width="100%" height="100%" preserveAspectRatio="none" viewBox="0 0 1920 1016" style={{position:'absolute',inset:0,overflow:'hidden'}}>
      <defs><mask id="cursor-safe"><rect width="1920" height="1016" fill="black"/><rect x={timelineBounds[0]} y={timelineBounds[1]} width={timelineBounds[2]-timelineBounds[0]} height={timelineBounds[3]-timelineBounds[1]} fill="white"/></mask></defs><g mask="url(#cursor-safe)">{states.map((s)=><FeedbackLayer key={`f-${s.worker.id}`} state={s}/>)}
      {states.map((s)=><Pointer key={s.worker.id} state={s} frame={frame}/>)}
    </g></svg>
  </AbsoluteFill>;
};

export function getDiagnostics(frame: number){
  return labelLayout(motion.crew.map(w=>stateAt(w,frame))).map(s=>({id:s.worker.id,name:s.worker.name,role:s.worker.role,x:s.p[0],y:s.p[1],label:s.label,kind:s.segment.kind}));
}
