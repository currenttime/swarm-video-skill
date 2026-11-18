import D from './workbench-data.json';
const T=D.layout.timeline;
// Canonical animation coordinates do not prescribe an editor's screen layout.
export const timelineBounds=[T.x*1920,T.y*1016,(T.x+T.width)*1920,(T.y+T.height)*1016];
export const timelineTransform=`translate(${T.x*1920} ${T.y*1016}) scale(${T.width} ${T.height*1016/398}) translate(0 -618)`;
export function mapPoint([x,y]:number[]):[number,number]{
 return [T.x*1920+x*T.width,T.y*1016+(y-618)/398*T.height*1016];
}
