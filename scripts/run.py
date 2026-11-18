"""Turn one edited video into a workspace demo with animated cursors and tracks."""
from __future__ import annotations
import argparse, random, hashlib, io, json, math, os, shutil, subprocess, sys
from datetime import datetime
from fractions import Fraction
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from panels import PANEL_NAMES, linked_clicks, overlaps, panel_motion, workspace_layout
from workspaces import PRESETS, load_workspace, pixel_box, player_filter, select_workspace

ROOT=Path(__file__).resolve().parents[1]
RUNTIME_PROFILE = Path.home() / '.config' / 'swarm-video-skill' / 'runtime.json'

def run(args, **kwargs):
    r=subprocess.run([str(x) for x in args],capture_output=True,**kwargs)
    if r.returncode:
        raise RuntimeError(r.stderr.decode('utf-8','replace')[-8000:])
    return r.stdout

def executable(explicit, name):
    candidate=explicit or os.environ.get(name.upper()) or shutil.which(name) or runtime_options().get(name)
    if not candidate or not Path(candidate).is_file():
        raise RuntimeError(f'{name} not found. Install FFmpeg with ffprobe; add to PATH or pass --{name} FULL_PATH.')
    return str(Path(candidate).resolve())


def runtime_options():
    if RUNTIME_PROFILE.is_file():
        return json.loads(RUNTIME_PROFILE.read_text(encoding='utf-8-sig'))
    return {}

def probe(fp,path,count=False):
    return json.loads(run([fp,'-v','error',*(['-count_frames'] if count else []),'-show_streams','-show_format','-of','json',path]))

def encode(ff,args,dest):
    """Python owns file writing; supports hosts that deny encoder-created files."""
    tmp=dest.with_name(dest.name+'.part')
    log=dest.with_name(dest.name+'.encode.log')
    with tmp.open('wb') as output, log.open('wb') as error:
        r=subprocess.run([ff,'-hide_banner','-v','warning','-nostdin',*map(str,args),
                          '-movflags','+frag_keyframe+empty_moov','-f','mp4','pipe:1'],stdout=output,stderr=error)
    if r.returncode:
        raise RuntimeError(log.read_text(encoding='utf-8',errors='replace')[-8000:])
    tmp.replace(dest)

def extract(ff,path,t):
    b=run([ff,'-v','error','-ss',str(t),'-i',path,'-an','-frames:v','1','-f','image2pipe','-vcodec','png','pipe:1'])
    return Image.open(io.BytesIO(b)).convert('RGB')

def dump(path,data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def digest(path):
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def detect_layout(images):
    """Find stable horizontal workspace boundaries, without identifying a brand."""
    arr=np.stack([np.asarray(im.resize((960,540)),dtype=float) for im in images])
    gray=arr.mean(axis=3)
    per_frame=np.quantile(np.abs(gray[:,1:,:]-gray[:,:-1,:]),.55,axis=2)
    edge=np.median(per_frame,axis=0)
    candidates=[]
    for y in range(190,450):
        # Prefer a divider that spans the workspace and stays visible in samples.
        stability=float(np.min(per_frame[:,y])/(np.max(per_frame[:,y])+1e-6))
        score=float(edge[y])*stability
        if score<2:continue
        candidates.append({'y':(y+1)/540,'score':round(score,3),'stability':round(stability,3)})
    candidates.sort(key=lambda x:x['score'],reverse=True)
    distinct=[]
    for c in candidates:
        if all(abs(c['y']-q['y'])>.035 for q in distinct):distinct.append(c)
        if len(distinct)==8:break
    # A bright thumbnail edge can have much higher contrast than the workspace
    # divider. Prefer the uppermost stable divider above such internal tracks.
    qualified=[c for c in distinct if c['score']>=5 and c['stability']>=.65]
    best=min(qualified,key=lambda c:c['y']) if qualified else {'y':.62,'score':0,'stability':0}
    # A preview often ends just above a stronger full-width timeline divider.
    nearby=[c for c in qualified if 0<c['y']-best['y']<.08 and c['score']>best['score']*1.5]
    if nearby:best=max(nearby,key=lambda c:c['score'])
    # No product preset: the visual agent reviews candidate/source images and
    # supplies a rectangle for ambiguous or partially docked timelines.
    y=best['y'];confidence=min(1,best['score']/12)
    supported=best['score']>=5 and best['stability']>=.65
    return {'timeline':{'x':0.,'y':y,'width':1.,'height':1-y}}, {
        'method':'stable-horizontal-divider-heuristic','confidence':round(confidence,3),
        'supported':bool(supported),'candidates':distinct,
        'limitation':'Image heuristic, not semantic software recognition. Review layout.jpg. Ambiguous/partial timelines require a rectangle selected from the source frames.'}


def validate_layout(l):
    if 'timeline' not in l or set(l)-{'timeline','thumbnail','player','preview',*PANEL_NAMES}:
        raise ValueError('Layout needs a timeline rectangle and accepts player, preview, thumbnail and workspace panels')
    for name,r in l.items():
        if set(r)!={'x','y','width','height'}:raise ValueError('Rectangles need x,y,width,height')
        if not all(isinstance(v,(int,float)) and math.isfinite(v) and 0<=v<=1 for v in r.values()):raise ValueError('Use finite normalized coordinates 0..1')
        if r['width']<=0 or r['height']<=0 or r['x']+r['width']>1.000001 or r['y']+r['height']>1.000001:raise ValueError('Rectangle extends outside image')
    if l['timeline']['height']<.16 or l['timeline']['width']<.4:raise ValueError('Timeline is too small for readable multi-track animation')
    video_rect = l.get('player') or l.get('preview')
    if video_rect and (video_rect['width'] < .15 or video_rect['height'] < .12):
        raise ValueError('The player rectangle is too small.')
    zones = ['timeline', *(name for name in PANEL_NAMES if name in l)]
    if video_rect:
        zones.append('player' if 'player' in l else 'preview')
    for index, name in enumerate(zones):
        for other in zones[index+1:]:
            if overlaps(l[name], l[other]):
                raise ValueError(f'{name} and {other} rectangles must not overlap.')


def layout_sheet(image,l,out):
    im=image.copy();d=ImageDraw.Draw(im);w,h=im.size
    for name, r in l.items():
        if name == 'thumbnail':
            continue
        color = '#00ffb3' if name in ('player', 'preview') else '#ff79bb'
        x, y = r['x']*w, r['y']*h
        d.rectangle((x,y,x+r['width']*w,y+r['height']*h),outline=color,width=max(2,w//500))
        d.text((x+8,y+8),name.upper(),fill=color)
    im.save(out)

def make_plan(n,fps,width,height,speed,seconds,layout,seed,static_workspace=None):
    d=json.loads((ROOT/'assets/choreography.json').read_text(encoding='utf-8'))
    layout=workspace_layout(layout)
    validate_layout(layout)
    first_click = min(c['at'] for c in d['commits'])
    last_click = max(c['at'] for c in d['commits'])
    factor=min(n/d.pop('referenceFrames'),(n-3)/(last_click-first_click))
    d.update(width=width,height=height,fps=fps,durationInFrames=n,speed=speed,
        timeScale=factor,timelineSeconds=seconds,layout=layout,
        staticWorkspace='player' in layout if static_workspace is None else static_workspace)
    offset = max(0, 1-first_click*factor)
    for c in d['commits']:c['at']=min(n-2,max(1,round(c['at']*factor+offset)))
    for c in d['clips']:c['at']=min(n-2,max(1,round(c['at']*factor+offset)))
    d['workspaceCues'] = linked_clicks(d['commits'], n, fps) if {'media','controls'} <= layout.keys() else []
    d['panelActions'] = {name: [] for name in PANEL_NAMES}
    side_workers = dict(zip(range(19, 28), ('media','media','controls','controls','inspector','inspector','inspector','transport','transport')))
    for number, worker in enumerate(d['crew']):
        # Names are generic labels; all scheduling derives from one authored style.
        if seed!='models':worker['name']=f"Editor {int(worker['id'].split('-')[-1])+1:02}"
        region = side_workers.get(number, 'timeline')
        worker['area'] = region if region in layout else 'timeline'
        if worker['area'] != 'timeline':
            cue_frames = [cue[region] for cue in d['workspaceCues']] if number in (19,21) else ()
            worker['segments'], actions = panel_motion(region, number, n, fps, cue_frames)
            d['panelActions'][region].extend(actions)
            continue
        rng=random.Random(907+int(worker['id'].split('-')[-1]))
        point_map={}
        def relocate(p):
            if p[1]>=618:return p
            key=tuple(p)
            if key not in point_map:
                track=rng.choice(d['tracks']);point_map[key]=[rng.uniform(195,1840),track['y']+track['h']/2]
            return point_map[key]
        for s in worker['segments']:
            s['from']=s['from']*factor+offset if s['from'] else 0
            s['to']=s['to']*factor+offset
            s['p0']=relocate(s['p0']);s['p1']=relocate(s['p1'])
    d['playhead']=[176+1714*i/max(1,n-1) for i in range(n)]
    for actions in d['panelActions'].values():
        actions.sort(key=lambda action: action['at'])
    return d

def sync_checks(d):
    workers={w['id']:w for w in d['crew']};clips={c['id']:c for c in d['clips']};bad=[]
    for c in d['commits']:
        worker=workers[f"worker-{c['worker']:02}"]
        clicks=[s for s in worker['segments'] if s['kind']=='click' and abs(s['from']-c['at'])<=.51]
        if not clicks or not any(math.dist(s['p0'],c['target'])<.01 for s in clicks):bad.append(c['id'])
        for id in c['clips']:
            if clips[id]['at']!=c['at']:bad.append(id)
    commits={c['id']:c['at'] for c in d['commits']}
    panel_actions=d.get('panelActions', {})
    actual_actions = {}
    for name, events in panel_actions.items():
        actual_actions[name] = set()
        for event in events:
            worker=workers[f"worker-{event['worker']:02}"]
            if worker.get('area')==name and any(
                s['kind']=='click' and s['from']==event['at'] for s in worker['segments']
            ):
                actual_actions[name].add(event['at'])
    cues=d.get('workspaceCues', [])
    cue_pass=all(
        cue['media'] in actual_actions['media'] and cue['controls'] in actual_actions['controls']
        and cue['media'] < cue['controls'] < commits[cue['commit']]==cue['timeline']
        for cue in cues
    )
    return {'commit_count':len(d['commits']),'clip_count':len(d['clips']),'worker_count':len(d['crew']),
            'click_reveal_sync_pass':not bad,'bad_ids':bad[:20],
            'workspace_cues':len(cues),'workspace_cue_sync_pass':cue_pass,
            'panel_click_counts':{name:len(events) for name,events in panel_actions.items()},
            'clips_before_first_click':sum(c['at']<min(x['at'] for x in d['commits']) for c in d['clips'])}

def contact_sheet(ff,output,n,fps,dest):
    frames=[0,round((n-1)*.25),round((n-1)*.5),round((n-1)*.9)]
    images=[extract(ff,output,f/fps) for f in frames];height=round(640*images[0].height/images[0].width)
    sheet=Image.new('RGB',(1280,(height+26)*2),'#171b20');draw=ImageDraw.Draw(sheet)
    for i,im in enumerate(images):
        x=i%2*640;y=i//2*(height+26);sheet.paste(im.resize((640,height)),(x,y+26));draw.text((x+8,y+5),f'{frames[i]/fps:.2f}s',fill='white')
    sheet.save(dest)


def prepare_video(ff, source, public, plan, start, end, background):
    fps = plan['fps']
    frame_count = plan['durationInFrames']
    speed = plan['speed']
    filters = (f'settb=AVTB,setpts=PTS-STARTPTS,trim=start={start}:end={end},'
               f'setpts=(PTS-STARTPTS)/{speed},fps={fps}:start_time=0,tpad=stop_mode=clone:stop=-1')
    options = ['-an','-frames:v',frame_count,'-c:v','libx264','-crf','0','-preset','fast','-threads','4','-pix_fmt','yuv420p']
    base = public / 'source-fast.mp4'
    if background is None:
        encode(ff, ['-i',source,'-map','0:v:0','-vf',filters,*options], base)
        thumb_video = base
        thumb = plan['layout'].get('thumbnail') or plan['layout'].get('preview') or plan['layout'].get('player') or {
            'x':.24,'y':.12,'width':.52,'height':max(.1,plan['layout']['timeline']['y']-.20)}
        size = plan['width'], plan['height']
        crop = tuple(round(thumb[key] * length) for key, length in zip(('x','y'), size)) + (
            round((thumb['x']+thumb['width'])*size[0]), round((thumb['y']+thumb['height'])*size[1]))
    else:
        x, y, width, height = pixel_box(plan['layout']['player'], *background.size)
        still = public / 'workspace.png'
        background.save(still)
        thumb_video = public / 'player.mp4'
        encode(ff, ['-i',source,'-map','0:v:0','-vf',f'{filters},{player_filter((x,y,width,height))}',*options], thumb_video)
        bake_workspace(ff, public, plan)
        crop = None

    strip = Image.new('RGB', (1714, 34))
    thumbnails = public / 'thumbs'
    thumbnails.mkdir()
    for index in range(28):
        left, right = round(index*1714/28), round((index+1)*1714/28)
        frame = extract(ff, thumb_video, (frame_count-1)/fps*index/28)
        if crop:
            frame = frame.crop(crop)
        frame.thumbnail((376,212),Image.Resampling.LANCZOS)
        frame.save(thumbnails / f'{index:02}.png')
        strip.paste(frame.resize((right-left,34),Image.Resampling.LANCZOS), (left,0))
    strip.save(public / 'timeline-thumbnails.png')


def bake_workspace(ff, public, plan):
    x, y, _, _ = pixel_box(plan['layout']['player'], plan['width'], plan['height'])
    encode(ff, ['-loop','1','-framerate',plan['fps'],'-i',public/'workspace.png',
        '-i',public/'player.mp4','-filter_complex_threads','2',
        '-filter_complex',f'[0:v]setsar=1[bg];[bg][1:v]overlay={x}:{y}:format=yuv420:shortest=1[v]',
        '-map','[v]','-an','-frames:v',plan['durationInFrames'],'-c:v','libx264','-crf','0',
        '-preset','fast','-threads','4','-pix_fmt','yuv420p'], public/'source-fast.mp4')


def side_cursor_coverage(plan, frames):
    """Check rendered cursor colors in each enabled side panel, not just the layer bounds."""
    width, height = plan['width'], plan['height']
    region_colors = {}
    for worker in plan['crew']:
        area = worker.get('area', 'timeline')
        if area == 'timeline':
            continue
        color = worker['color'].lstrip('#')
        region_colors.setdefault(area, set()).add(int(color, 16))
    counts = dict.fromkeys(region_colors, 0)
    for fraction in (.20, .45, .70, .90):
        index = round((len(frames)-1)*fraction)
        with Image.open(frames[index]) as sprite:
            for area, colors in region_colors.items():
                x, y, w, h = pixel_box(plan['layout'][area], width, height)
                pixels = np.asarray(sprite.crop((x,y,x+w,y+h)).convert('RGBA'), dtype=np.uint32)
                rgb = (pixels[:,:,0] << 16) | (pixels[:,:,1] << 8) | pixels[:,:,2]
                if np.count_nonzero((pixels[:,:,3] > 225) & np.isin(rgb,list(colors))) >= 12:
                    counts[area] += 1
    return counts


def verify(ff,fp,out,src,source_hash,d,base,overlay,qa_dir):
    m=probe(fp,out,True);v=next(x for x in m['streams'] if x['codec_type']=='video');n=d['durationInFrames'];fps=d['fps']
    checks={'size':(v['width'],v['height'])==(d['width'],d['height']),
            'frames':int(v['nb_read_frames'])==n,'fps':Fraction(v['r_frame_rate'])==fps,
            'duration':abs(float(v.get('duration',m['format']['duration']))-n/fps)<1/fps+.002,
            'silent':not any(s['codec_type']=='audio' for s in m['streams']),
            'source_unchanged':digest(src)==source_hash}
    w,h=d['width'],d['height'];bad=[];frames=sorted(overlay.glob('element-*.png'))
    mask=np.ones((h,w),dtype=bool)
    sample_mask=mask.copy()
    zones = ('timeline', *(name for name in PANEL_NAMES if name in d['layout']))
    for name in zones:
        box=d['layout'][name]
        x0=math.floor(box['x']*w);x1=math.ceil((box['x']+box['width'])*w)
        y0=math.floor(box['y']*h);y1=math.ceil((box['y']+box['height'])*h)
        mask[max(0,y0-2):y1+2,max(0,x0-2):x1+2]=False
        sample_mask[max(0,y0-16):y1+16,max(0,x0-16):x1+16]=False
    for i,p in enumerate(frames):
        with Image.open(p) as rendered:
            a=np.asarray(rendered.getchannel('A'))
        if a[mask].max(initial=0)>0:bad.append(i)
    checks['overlay_frame_count']=len(frames)==n
    checks['all_native_workspace_alpha_clear']=not bad
    visible_side_cursors=side_cursor_coverage(d,frames) if frames else {}
    checks['side_panel_cursors_visible']=all(value>=3 for value in visible_side_cursors.values())
    # Playback compression is lossy. Verify native workspace similarity outside
    # a small codec-block margin rather than claiming pixel-exact output.
    diffs=[];native_errors=[]
    player_errors = []
    has_static_player = d.get('staticWorkspace', 'player' in d['layout'])
    if has_static_player:
        px, py, pw, ph = pixel_box(d['layout']['player'], w, h)
        player_box = np.s_[py+4:py+ph-4,px+4:px+pw-4]
    for frame in sorted(set([0,n//3,n*2//3,n-1])):
        a=np.asarray(extract(ff,base,frame/fps),dtype=float);b=np.asarray(extract(ff,out,frame/fps),dtype=float)
        err=np.mean((a-b)[sample_mask]**2)
        diffs.append(100. if err==0 else round(10*math.log10(255**2/err),2))
        native_errors.append(float(np.mean(np.abs(a-b)[sample_mask])))
        if has_static_player:
            player = np.asarray(extract(ff, base.parent/'player.mp4', frame/fps), dtype=float)
            player_errors.append(float(np.mean(np.abs(a[player_box]-player[4:-4,4:-4]))))
    checks['sample_native_workspace_psnr']=min(diffs)>32
    checks['sample_native_workspace_mean_error']=max(native_errors)<3
    if player_errors:
        checks['player_matches_input_video'] = max(player_errors) < 2
        outside = sample_mask.copy()
        outside[max(0,py-4):py+ph+4,max(0,px-4):px+pw+4] = False
        still = np.asarray(load_workspace(base.parent/'workspace.png'), dtype=float)
        first = np.asarray(extract(ff, base, 0), dtype=float)
        checks['workspace_matches_static_template'] = bool(outside.any()) and float(np.mean(np.abs(first-still)[outside])) < 4
    sync=sync_checks(d);checks['click_reveal_sync']=sync['click_reveal_sync_pass']
    checks['workspace_cue_sync']=sync['workspace_cue_sync_pass']
    # A second complete decode with stderr captured proves no reported corruption.
    dec=subprocess.run([ff,'-v','error','-i',str(out),'-f','null','-'],capture_output=True)
    checks['full_decode']=dec.returncode==0 and not dec.stderr.strip()
    report={'all_pass':all(checks.values()),'checks':checks,'sync':sync,'output_sha256':digest(out),
            'duration_seconds':n/fps,'frames':n,'fps':fps,'dimensions':[w,h],'native_workspace_psnr_samples_db':diffs,
            'native_workspace_mean_rgb_error_samples':native_errors,
            'player_mean_rgb_error_samples':player_errors,
            'visible_side_cursor_samples_of_four':visible_side_cursors,
            'bad_native_workspace_frames':bad[:20],'review_scope':'Full decode, all overlay alpha frames, event sync and four native-workspace samples; not full human viewing.',
            'layout':d['layout'],'output':out.name}
    dump(qa_dir/'report.json',report);dump(qa_dir/'media.json',m)
    if not report['all_pass']:raise RuntimeError('QA failed; inspect checks/report.json')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('video',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--speed',type=float,help='Default: 1 for edited video, 5 for workspace recording')
    p.add_argument('--fps',type=int,default=60)
    p.add_argument('--ffmpeg');p.add_argument('--ffprobe');p.add_argument('--browser')
    p.add_argument('--template',choices=PRESETS,help='Built-in static workspace, default: cut')
    p.add_argument('--workspace-image',type=Path,help='Custom static workspace screenshot (with --layout)')
    p.add_argument('--recording',action='store_true',help='Use the older workspace-recording workflow instead')
    p.add_argument('--layout',type=Path,help='Normalized timeline, player/preview and workspace panel rectangles')
    p.add_argument('--labels',choices=['generic','models'],default='generic')
    p.add_argument('--start',type=float,default=0,help='Seconds relative to first decoded video frame')
    p.add_argument('--end',type=float,help='End seconds relative to first decoded video frame')
    p.add_argument('--analyze-only',action='store_true');p.add_argument('--prepare-only',action='store_true')
    p.add_argument('--concurrency',type=int,default=4)
    args=p.parse_args();src=args.video.expanduser().resolve()
    args.speed = args.speed if args.speed is not None else (5 if args.recording else 1)
    if args.recording and (args.template or args.workspace_image):
        p.error('--recording cannot be combined with a static workspace template')
    if args.template and args.workspace_image:
        p.error('Select either --template or --workspace-image')
    if sys.version_info<(3,11):raise RuntimeError('Python 3.11+ is required')
    if not src.is_file():raise ValueError('Input video does not exist')
    if not math.isfinite(args.speed) or not .1<=args.speed<=50 or not 12<=args.fps<=120:raise ValueError('Invalid speed/fps')
    if not math.isfinite(args.start) or args.start<0:raise ValueError('Invalid start time')
    if args.end is not None and (not math.isfinite(args.end) or args.end<=args.start):raise ValueError('Invalid end time')
    if not 1<=args.concurrency<=32:raise ValueError('Concurrency must be 1..32')
    ff=executable(args.ffmpeg,'ffmpeg');fp=executable(args.ffprobe,'ffprobe')
    npm=shutil.which('npm.cmd' if os.name=='nt' else 'npm');node=shutil.which('node')
    if not args.analyze_only and not args.prepare_only:
        if not npm or not node:raise RuntimeError('Install Node.js >=22.13 including npm')
        node_version=tuple(int(x) for x in run([node,'--version']).decode().strip().lstrip('v').split('.')[:2])
        if node_version<(22,13):raise RuntimeError('Node.js >=22.13 is required')
    m=probe(fp,src);v=next((x for x in m['streams'] if x['codec_type']=='video'),None)
    if v is None:raise ValueError('Input has no video stream')
    width,height=v['width'],v['height']
    if args.recording and (width%2 or height%2 or width<640 or height<360):
        raise ValueError('Use a full workspace recording of at least 640x360 with even dimensions')
    raw_duration=v.get('duration')
    if raw_duration is None:
        # Count/decode video timing rather than using audio/container tail duration.
        frames=json.loads(run([fp,'-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time,duration_time','-of','json',src]))['frames']
        raw_duration=float(frames[-1]['best_effort_timestamp_time'])-float(frames[0]['best_effort_timestamp_time'])+float(frames[-1].get('duration_time',1/float(Fraction(v['avg_frame_rate']))))
    source_duration=float(raw_duration);end=min(source_duration,args.end if args.end is not None else source_duration)
    seconds=end-args.start;n=math.ceil(seconds/args.speed*args.fps-1e-7)
    if n<args.fps*2:raise ValueError('Output is under 2s; use a longer input or lower speed')
    out=(args.output or src.parent/f'{src.stem}_swarm-video-skill_{datetime.now():%Y%m%d_%H%M%S}').resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('Output folder is not empty; choose a new folder to preserve previous results')
    out.mkdir(parents=True,exist_ok=True);qa=out/'checks';qa.mkdir(exist_ok=True)
    print('ANALYZING',flush=True)
    background = None
    if args.recording:
        images = [extract(ff,src,args.start+seconds*f) for f in [.05,.45,.85]]
        layout,det = detect_layout(images)
        if args.layout:
            layout=json.loads(args.layout.read_text(encoding='utf-8-sig'));det={'method':'explicit-layout','supported':True,'confidence':None}
        artwork = images[0]
        for i,image in enumerate(images):image.save(qa/f'source-{i}.jpg')
    else:
        name, artwork_path, layout = select_workspace(args.template, args.workspace_image, args.layout)
        if 'player' not in layout:
            raise ValueError('The static workspace layout needs both player and timeline rectangles.')
        background = artwork = load_workspace(artwork_path)
        width, height = background.size
        det = {'method':'static-workspace','template':name,'supported':True}
    validate_layout(layout)
    layout=workspace_layout(layout)
    validate_layout(layout);dump(qa/'layout.json',layout);dump(qa/'layout-detection.json',det)
    layout_sheet(artwork,layout,qa/'layout.jpg')
    if args.analyze_only:print('ANALYSIS READY',out,flush=True);return
    if not det['supported']:raise RuntimeError('Unrecognized layout. Inspect checks/layout.jpg; provide --layout JSON with the actual timeline rectangle. The skill can choose it from checks/source-*.jpg.')
    source_hash=digest(src);project=out/'project';shutil.copytree(ROOT/'assets/project',project)
    public=project/'public';public.mkdir(parents=True)
    d=make_plan(n,args.fps,width,height,args.speed,seconds,layout,args.labels,static_workspace=background is not None)
    dump(project/'src/workbench-data.json',d)
    sync=sync_checks(d);dump(qa/'events.json',sync)
    if not sync['click_reveal_sync_pass'] or not sync['workspace_cue_sync_pass']:raise RuntimeError('Choreography synchronization check failed')
    dump(qa/'source.json',{'sha256':source_hash,'bytes':src.stat().st_size,'video_duration':source_duration,
        'video_start_pts':v.get('start_time'),'selected_start':args.start,'selected_end':end,
        'speed':args.speed,'frames':n,'duration_seconds':n/args.fps,'source_name':src.name,'workspace':det})
    print('PREPARING PLAYER, WORKSPACE AND THUMBNAILS',flush=True)
    prepare_video(ff, src, public, d, args.start, end, background)
    base=public/'source-fast.mp4'
    (out/'OPEN-STUDIO.cmd').write_text('@echo off\r\ncd /d "%~dp0project"\r\ncall npm run dev\r\npause\r\n',encoding='ascii')
    if args.prepare_only:print('PREPARED',out,flush=True);return
    print('INSTALLING PINNED RENDERER DEPENDENCIES',flush=True)
    subprocess.run([npm,'ci','--no-audit','--no-fund'],cwd=project,check=True)
    env=os.environ.copy();env['SWARM_VIDEO_CONCURRENCY']=str(args.concurrency)
    if args.browser:
        env['REMOTION_BROWSER_EXECUTABLE']=str(Path(args.browser).resolve())
    elif not env.get('REMOTION_BROWSER_EXECUTABLE'):
        browser = runtime_options().get('browser')
        if browser and Path(browser).is_file():
            env['REMOTION_BROWSER_EXECUTABLE'] = browser
    print('RENDERING',flush=True);subprocess.run([node,'render.mjs'],cwd=project,env=env,check=True)
    overlay=out/'overlay';frames=sorted(overlay.glob('element-*.png'))
    if len(frames)!=n:raise RuntimeError('Overlay sequence is incomplete')
    digits=len(frames[0].stem.split('-')[-1]);pattern=overlay/f'element-%0{digits}d.png'
    final=out/'swarm-video.mp4';print('COMPOSITING',flush=True)
    encode(ff,['-i',base,'-framerate',args.fps,'-i',pattern,
        '-filter_complex','[0:v][1:v]overlay=0:0:format=yuv420:shortest=1[v]',
        '-map','[v]','-an','-frames:v',n,'-c:v','libx264','-crf','16','-preset','fast','-threads','4','-pix_fmt','yuv420p'],final)
    print('VERIFYING',flush=True);verify(ff,fp,final,src,source_hash,d,base,overlay,qa)
    contact_sheet(ff,final,n,args.fps,qa/'contact-sheet.jpg')
    print('DONE',final,flush=True)

if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,OSError,KeyError,subprocess.CalledProcessError,StopIteration) as e:
        print(f'ERROR: {e}',file=sys.stderr);sys.exit(1)
