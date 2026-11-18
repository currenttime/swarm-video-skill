import D from './workbench-data.json';
type Bounds = [number, number, number, number];
type Rect = {x: number; y: number; width: number; height: number};
const layout: Record<string, Rect | undefined> = D.layout;
const reference: Record<string, Bounds> = {
  timeline: [0,618,1920,1016],
  media: [0,98,680,378],
  controls: [0,378,680,618],
  inspector: [1360,98,1920,618],
  transport: [680,500,1360,618],
};
export const areas = Object.keys(reference).filter(area=>Boolean(layout[area]));

export function boundsFor(area: string): Bounds {
  const {x,y,width,height}=layout[area] ?? D.layout.timeline;
  return [x*1920,y*1016,(x+width)*1920,(y+height)*1016];
}

export function panelTransform(area: string): string {
  const [x,y,right,bottom]=boundsFor(area);
  const [left,top,referenceRight,referenceBottom]=reference[area];
  return `translate(${x} ${y}) scale(${(right-x)/(referenceRight-left)} ${(bottom-y)/(referenceBottom-top)}) translate(${-left} ${-top})`;
}
export const timelineTransform=panelTransform('timeline');

export function mapPoint([x,y]:number[], area: string):[number,number]{
  const [left,top,right,bottom]=reference[area];
  const [destX,destY,destRight,destBottom]=boundsFor(area);
  return [destX+(x-left)/(right-left)*(destRight-destX),destY+(y-top)/(bottom-top)*(destBottom-destY)];
}
