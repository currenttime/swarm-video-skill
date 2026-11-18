"""Create a license-free synthetic workspace recording for regression tests."""
import argparse,io,subprocess,sys,tempfile
from pathlib import Path
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run import executable,encode

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    p.add_argument('--ffmpeg');p.add_argument('--width',type=int,default=1280);p.add_argument('--height',type=int,default=720)
    p.add_argument('--timeline-y',type=float,default=.55);p.add_argument('--seconds',type=float,default=15)
    args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    w,h=args.width,args.height;im=Image.new('RGB',(w,h),'#20212a');d=ImageDraw.Draw(im)
    d.rectangle((0,0,w,40),fill='#35333e');d.text((20,15),'SYNTHETIC WORKSPACE / LICENSE-FREE TEST INPUT',fill='#eeeeee')
    d.rectangle((w*.05,h*.1,w*.25,h*(args.timeline_y-.04)),fill='#2c2d38');d.text((w*.07,h*.12),'MEDIA',fill='#aaaaaa')
    d.rectangle((w*.30,h*.10,w*.73,h*(args.timeline_y-.04)),fill='#6c7884');d.text((w*.4,h*.22),'SOURCE PREVIEW',fill='#eeeeee')
    d.rectangle((w*.78,h*.10,w*.98,h*(args.timeline_y-.04)),fill='#2c2d38');d.text((w*.8,h*.12),'PARAMETERS',fill='#aaaaaa')
    y=round(args.timeline_y*h);d.rectangle((0,y,w,h),fill='#3d404b');d.text((14,y+10),'TIMELINE',fill='#dddddd')
    # Native timeline has an existing clip; generated timeline will cover it.
    d.rectangle((w*.15,y+(h-y)*.4,w*.8,y+(h-y)*.6),fill='#52848a')
    with tempfile.TemporaryDirectory() as tmp:
        png=Path(tmp)/'fixture.png';im.save(png)
        ff=executable(args.ffmpeg,'ffmpeg')
        encode(ff,['-loop','1','-i',png,'-t',args.seconds,'-vf',"drawbox=x=mod(t*45\\,iw-100):y=80:w=70:h=12:color=yellow:t=fill",'-an','-r','20','-c:v','libx264','-crf','16','-pix_fmt','yuv420p'],args.output)
    print(args.output)

if __name__=='__main__':main()
