"""Recompose an edited generated project, preserving the previous MP4."""
import argparse,json
from pathlib import Path
from run import bake_workspace,encode,executable,contact_sheet,verify,digest

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path)
    p.add_argument('--ffmpeg');p.add_argument('--ffprobe');args=p.parse_args()
    root=args.folder.resolve();d=json.loads((root/'project/src/workbench-data.json').read_text(encoding='utf-8'))
    ff=executable(args.ffmpeg,'ffmpeg');fp=executable(args.ffprobe,'ffprobe')
    base=root/'project/public/source-fast.mp4';overlay=root/'overlay';frames=sorted(overlay.glob('element-*.png'))
    if len(frames)!=d['durationInFrames']:raise ValueError('Run npm run render in project first; overlay frame count differs')
    digits=len(frames[0].stem.split('-')[-1]);pattern=overlay/f'element-%0{digits}d.png'
    out=root/'swarm-video-edited.mp4'
    if out.exists():raise ValueError('swarm-video-edited.mp4 already exists. Rename it to preserve the earlier edit, then retry.')
    if d.get('staticWorkspace', 'player' in d['layout']):
        bake_workspace(ff, base.parent, d)
    source_hash=digest(base)
    encode(ff,['-i',base,'-framerate',d['fps'],'-i',pattern,
        '-filter_complex','[0:v][1:v]overlay=0:0:format=yuv420:shortest=1[v]',
        '-map','[v]','-an','-frames:v',d['durationInFrames'],'-c:v','libx264','-crf','16','-preset','fast','-threads','4','-pix_fmt','yuv420p'],out)
    qa=root/'checks-edited';qa.mkdir(exist_ok=True)
    verify(ff,fp,out,base,source_hash,d,base,overlay,qa)
    contact_sheet(ff,out,d['durationInFrames'],d['fps'],qa/'contact-sheet.jpg')
    print(out)

if __name__=='__main__':main()
