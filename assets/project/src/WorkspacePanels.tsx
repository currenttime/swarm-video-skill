import React from 'react';
import {Img, staticFile} from 'remotion';
import {areas, panelTransform} from './geometry';
import D from './workbench-data.json';

const C={bg:'#101619',panel:'#151D21',edge:'#303C42',muted:'#809198',text:'#D5DFE1',amber:'#EDBC69',cyan:'#79C8C4'};
const mono='Consolas, "Microsoft YaHei", monospace';
const sans='"Segoe UI", "Microsoft YaHei", sans-serif';
const clamp=(v:number,a=0,b=1)=>Math.max(a,Math.min(b,v));
const text=(x:number,y:number,value:React.ReactNode,color=C.text,size=12,isMono=false)=> <text x={x} y={y} fill={color} fontSize={size} fontFamily={isMono?mono:sans}>{value}</text>;
function latest<T extends {at:number}>(items:T[], frame:number):T|undefined {
  let start=0, end=items.length;
  while(start<end){const mid=(start+end)>>>1;if(items[mid].at<=frame)start=mid+1;else end=mid;}
  return items[start-1];
}
type PanelAction={at:number;slot:number;worker:number};
const actions: Record<string, PanelAction[]> = D.panelActions;
const panelSelection=(area:string,frame:number)=>latest(actions[area] ?? [],frame);
const clips=new Map(D.clips.map(clip=>[clip.id,clip]));
function current(frame:number){return latest(D.commits,frame) ?? D.commits[0];}
export const mediaPage=(frame:number)=>Math.floor((panelSelection('media',frame)?.at ?? 0)/(D.fps*2.8))%4;
const thumbnail=(id:number)=>staticFile('thumbs/'+String(id).padStart(2,'0')+'.png');

const LeftPanel:React.FC<{frame:number}>=({frame})=>{
  const active=current(frame),index=D.commits.indexOf(active),page=mediaPage(frame);
  const selectedMedia=panelSelection('media',frame)?.slot ?? -1;
  const selectedTool=panelSelection('controls',frame);
  const toolActive=selectedTool && frame-selectedTool.at<D.fps*.42 ? selectedTool.slot : -1;
  const piece=clips.get(active.clips[0])!;
  const lines=['{',`  "shot": "${piece.label}",`,`  "lane": "${D.tracks[piece.track].code}",`,`  "in": ${((piece.x-176)/1714*D.timelineSeconds).toFixed(3)},`,`  "span": ${(piece.w/1714*D.timelineSeconds).toFixed(3)},`,'  "link": ["caption", "voice"],',`  "state": "${frame>active.at+D.fps*.25?'committed':'updating'}"`,'}'];
  return <g>
    <rect x={0} y={44} width={680} height={574} fill={C.bg}/>
    <path d="M16 96H664 M16 378H664" stroke={C.edge}/>
    {text(24,71,'ASSET GRAPH',C.amber,14,true)}{text(24,88,'MEDIA / NODES',C.muted,11)}
    <rect x={580} y={59} width={74} height={24} rx={5} fill="#223433"/>{text(592,75,'● SYNC',C.cyan,10,true)}
    {text(24,118,'MEDIA BIN',C.muted,10,true)}{text(500,118,`INDEX ${String(index+1).padStart(3,'0')} / ${D.commits.length}`,C.amber,10,true)}
    {Array.from({length:6},(_,i)=>{
      const xx=24+i%3*214,yy=132+Math.floor(i/3)*120,id=page*6+i,selected=i===selectedMedia;
      const p=((frame/(D.fps*2.83)+i*.23)%1);
      return <g key={i}>
        <rect x={xx} y={yy} width={202} height={109} rx={5} fill={selected?'#223130':C.panel} stroke={selected?C.amber:C.edge} strokeWidth={selected?1.3:.8}/>
        <image href={thumbnail(id)} x={xx+7} y={yy+7} width={188} height={72} preserveAspectRatio="xMidYMid slice"/>
        {text(xx+8,yy+94,`CLIP_${String(id+1).padStart(3,'0')}.mov`,selected?C.amber:C.text,10,true)}
        <rect x={xx+7} y={yy+102} width={188} height={2} fill="#314148"/><rect x={xx+7} y={yy+102} width={188*p} height={2} fill={selected?C.amber:C.cyan}/>
      </g>;
    })}
    <rect x={20} y={390} width={290} height={208} rx={6} fill={C.panel} stroke={C.edge}/>
    {text(34,412,'ARCH  /  A + B',C.text,11,true)}{text(34,429,'LAYER ROUTING',C.muted,10)}
    <path d="M66 476L166 446L266 476L166 506Z" fill="#79C8C4" fillOpacity={.09} stroke={C.cyan} strokeWidth={1}/>
    <path d="M66 528L166 498L266 528L166 558Z" fill="#EDBC69" fillOpacity={.09} stroke={C.amber} strokeWidth={1}/>
    {[86,126,166,206,246].map((x,i)=><path key={i} d={`M${x} ${476-Math.abs(x-166)*.3}V${528-Math.abs(x-166)*.3}`} stroke={C.muted} strokeOpacity={.3} strokeDasharray="3 4"/>)}
    {text(115,478,'A / TITLES & FX',C.cyan,11)}{text(115,530,'B / VIDEO & AUDIO',C.amber,11)}
    <circle cx={166} cy={451+(frame%(D.fps*1.66))/(D.fps*1.66)*96} r={3} fill={C.amber}/>
    {text(34,581,'COMPOSE  →  TIMELINE',C.muted,10,true)}
    <rect x={324} y={390} width={336} height={208} rx={6} fill="#121A1E" stroke={C.edge}/>
    {text(338,412,'SCENE PATCH',C.amber,11,true)}{text(573,412,'LIVE',C.cyan,10,true)}
    {[[60,447,130,40],[151,486,129,43],[380,435,210,36],[391,502,216,35]].map(([x,y,w,h],slot)=>slot===toolActive
      ? <rect key={slot} x={x} y={y} width={w} height={h} rx={5} fill={C.amber} fillOpacity={.12} stroke={C.amber} strokeOpacity={.85}/>
      : null)}
    {lines.map((l,i)=><g key={i}>
      {i===Math.floor(frame/17)%8?<rect x={332} y={424+i*20} width={318} height={19} fill="#EDBC69" fillOpacity={.065}/>:null}
      {text(337,438+i*20,String(i+1).padStart(2,'0'),C.muted,9,true)}
      {text(364,438+i*20,l,i===2||i===6?C.cyan:i===1?C.amber:C.text,10,true)}
    </g>)}
  </g>;
};

const RightPanel:React.FC<{frame:number}>=({frame})=>{
  const item=current(frame),p=clips.get(item.clips[0])!,t=frame*60/D.fps,u=(t%180)/180;
  const selected=panelSelection('inspector',frame);
  const activeSlot=selected && frame-selected.at<D.fps*.32 ? selected.slot : -1;
  const y1=370+Math.sin(t/70)*29,y2=352+Math.sin(t/87+1)*25;
  const bx=(t:number)=>Math.pow(1-t,3)*1408+3*(1-t)*(1-t)*t*1530+3*(1-t)*t*t*1708+t*t*t*1874;
  const by=(t:number)=>Math.pow(1-t,3)*413+3*(1-t)*(1-t)*t*y1+3*(1-t)*t*t*y2+t*t*t*326;
  const all=D.clips.filter(c=>frame>c.at),counts=[all.filter(c=>c.kind==='title').length/56,all.filter(c=>c.kind==='wave').length/74,all.length/268];
  return <g>
    <rect x={1360} y={44} width={560} height={574} fill={C.bg}/>
    {text(1380,71,'MOTION INSPECTOR',C.amber,14,true)}{text(1380,89,'CURVES / MIXER',C.muted,11)}
    <path d="M1378 96H1902" stroke={C.edge}/>
    <rect x={1380} y={108} width={520} height={39} rx={5} fill={C.panel} stroke={C.edge}/>
    {text(1394,133,`${D.tracks[p.track].code} / ${p.label}`,C.text,12,true)}{text(1760,133,'LINKED  ◇',C.cyan,10,true)}
    {['POSITION','SCALE','ROTATION'].map((label,i)=>{
      const q=.46+Math.sin(t/(79+i*21)+i*2.1)*(.19-i*.025),value=i===0?(p.x+Math.sin(t/80)*9).toFixed(2):i===1?(100+Math.sin(t/110)*2.8).toFixed(2)+'%':(Math.sin(t/130)*1.2).toFixed(2)+'°';
      return <g key={label}>{text(1384,177+i*41,label,C.muted,10,true)}
        <rect x={1508} y={168+i*41} width={273} height={3} rx={1.5} fill="#334249"/><rect x={1508} y={168+i*41} width={273*q} height={3} rx={1.5} fill={i===1?C.cyan:C.amber}/>
        <circle cx={1508+273*q} cy={169.5+i*41} r={4.5} fill={C.panel} stroke={i===1?C.cyan:C.amber} strokeWidth={1.4}/>{text(1798,177+i*41,value,C.text,11,true)}
      </g>;
    })}
    {text(1384,297,'KEYFRAME EDITOR',C.text,11,true)}{text(1747,297,'CUBIC / EASE',C.muted,10,true)}
    <rect x={1382} y={308} width={516} height={132} rx={4} fill="#11191D" stroke={C.edge}/>
    {[0,1,2,3,4,5,6,7].map(i=><line key={`x${i}`} x1={1407+i*67} x2={1407+i*67} y1={320} y2={427} stroke="#28353B" strokeWidth={.6}/>)}
    {[0,1,2,3].map(i=><line key={`y${i}`} x1={1394} x2={1888} y1={325+i*31} y2={325+i*31} stroke="#28353B" strokeWidth={.6}/>)}
    <path d={`M1408 413L1530 ${y1} M1708 ${y2}L1874 326`} fill="none" stroke={C.amber} strokeOpacity={.4} strokeDasharray="3 4"/>
    <path d={`M1408 413C1530 ${y1} 1708 ${y2} 1874 326`} fill="none" stroke={C.amber} strokeWidth={1.7}/>
    <path d={`M1408 406C1517 ${396-Math.sin(t/100)*20} 1685 ${405+Math.sin(t/80)*10} 1874 352`} fill="none" stroke={C.cyan} strokeOpacity={.65} strokeWidth={1.2}/>
    {[[1408,413],[1530,y1],[1708,y2],[1874,326]].map(([x,y],i)=><rect key={i} x={x-3} y={y-3} width={6} height={6} fill={C.panel} stroke={C.amber} strokeWidth={1}/>) }
    <circle cx={bx(u)} cy={by(u)} r={4} fill={C.amber}/>
    {text(1384,463,'AUDIO BUS / MULTICHANNEL',C.text,11,true)}{text(1770,463,'12 CHANNELS',C.muted,10,true)}
    {[[1531,155,89,31],[1644,196,100,35],[1478,341,95,43],[1702,365,111,44],[1724,472,57,63]].map(([x,y,w,h],slot)=>slot===activeSlot
      ? <rect key={slot} x={x} y={y} width={w} height={h} rx={4} fill={C.cyan} fillOpacity={.09} stroke={C.cyan} strokeOpacity={.75}/>
      : null)}
    {Array.from({length:12},(_,i)=>{
      const q=.13+.65*Math.abs(Math.sin(t/(10+i*.42)+i*.93))*Math.abs(Math.sin(t/71+i));
      return <g key={i}><rect x={1394+i*41.6} y={476} width={22} height={57} rx={2} fill="#233137"/>
        <rect x={1394+i*41.6} y={533-q*57} width={22} height={q*57} rx={1} fill={i>8?C.amber:C.cyan} fillOpacity={.68}/>
        <line x1={1392+i*41.6} x2={1418+i*41.6} y1={519-q*40} y2={519-q*40} stroke="#E1E9DD" strokeWidth={1}/>{text(1398+i*41.6,548,String(i+1).padStart(2,'0'),C.muted,8,true)}</g>;
    })}
    {['TYPE','SOUND','COMPOSE'].map((label,i)=><g key={label}>{text(1386+i*173,573,label,C.muted,9,true)}
      <rect x={1386+i*173} y={583} width={152} height={3} rx={1.5} fill="#2D3B40"/><rect x={1386+i*173} y={583} width={152*counts[i]} height={3} rx={1.5} fill={i===1?C.cyan:C.amber}/>
      {text(1490+i*173,573,`${Math.round(counts[i]*100)}%`,C.text,9,true)}</g>)}
  </g>;
};


const Transport:React.FC<{frame:number}>=({frame})=>{
  const active=panelSelection('transport',frame)?.slot ?? -1;
  const time=(frame/D.fps)*D.speed;
  return <g>
    <rect x={680} y={500} width={680} height={118} fill="#141D21"/>
    {text(700,524,'FOLLOW EDITS',C.text,12,true)}
    {text(1241,524,'A + B',C.cyan,11,true)}
    {['CAPTION SYNC','KEYFRAME LINK','MULTITRACK MIX'].map((label,i)=>{
      const x=707+i*201, color=i===active?C.amber:C.muted;
      return <g key={label}><circle cx={x} cy={549} r={5} fill={i===active?color:'none'} stroke={color}/>{text(x+13,553,label,color,11,true)}</g>;
    })}
    {text(700,586,Math.floor(time/60).toString().padStart(2,'0')+':'+(time%60).toFixed(2).padStart(5,'0'),C.text,12,true)}
    {text(1134,586,D.fps+' FPS  /  SILENT',C.muted,10,true)}
  </g>;
};

const originalBoxes: Record<string,[number,number,number,number]> = {
  media:[0,98,680,280],
  controls:[0,378,680,240],
  inspector:[1360,98,560,520],
  transport:[680,500,680,118],
};

export const MediaPreload:React.FC<{frame:number}>=({frame})=>areas.includes('media')?<>{Array.from({length:6},(_,i)=>
  <Img key={i} src={thumbnail(mediaPage(frame)*6+i)} style={{position:'absolute',width:1,height:1,opacity:0}}/>
)}</>:null;

export const WorkspacePanels:React.FC<{frame:number}>=({frame})=><>{areas.filter(area=>area!=='timeline').map(area=>{
  const [x,y,width,height]=originalBoxes[area];
  const id='panel-'+area;
  return <g key={area} transform={panelTransform(area)}>
    <defs><clipPath id={id}><rect x={x} y={y} width={width} height={height}/></clipPath></defs>
    <g clipPath={'url(#'+id+')'}>{area==='inspector'?<RightPanel frame={frame}/>:area==='transport'?<Transport frame={frame}/>:<LeftPanel frame={frame}/>}</g>
  </g>;
})}</>;
