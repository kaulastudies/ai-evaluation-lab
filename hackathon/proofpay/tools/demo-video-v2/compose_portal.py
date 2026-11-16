#!/usr/bin/env python3
"""Compose reviewed actual screen states with locally generated neural audio.

No model invocation, download, invented UI or avatar is part of composition.
Optional crops/highlight outlines reference coordinates in the supplied image.
"""
from pathlib import Path
import argparse,hashlib,json,math,subprocess,textwrap

HERE=Path(__file__).resolve().parent
WORK=HERE/'video-render'
FPS=30
BOLD='/usr/share/fonts/truetype/open-sans/OpenSans-Bold.ttf'
REG='/usr/share/fonts/truetype/open-sans/OpenSans-Regular.ttf'


def run(args,**kwargs): return subprocess.run(args,check=True,**kwargs)


def probe(path):
    return json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)],capture_output=True,text=True).stdout)


def file_path(value,base):
    p=Path(value);p=(p if p.is_absolute() else base/p).resolve()
    if not p.is_file(): raise ValueError(f'Missing reviewed input: {p.name}')
    return p


def rectangle(value,width,height):
    assert set(value)=={'x','y','width','height'}
    assert all(type(n) is int for n in value.values())
    x,y,w,h=(value[k] for k in ('x','y','width','height'))
    assert x>=0 and y>=0 and w>0 and h>0 and x+w<=width and y+h<=height
    return x,y,w,h


def label(name,text):
    path=WORK/f'{name}.txt';path.write_text(text);return path


def text_filter(name,text,size,x,y,color='17243C',font=BOLD,enable=None):
    value=f'drawtext=fontfile={font}:textfile={label(name,text)}:fontsize={size}:fontcolor=0x{color}:x={x}:y={y}'
    if enable: value+=f":enable='{enable}'"
    return value


def stamp(seconds):
    n=round(seconds*1000)
    return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('manifest',type=Path);parser.add_argument('--check',action='store_true');parser.add_argument('--paragraph',type=int,choices=range(1,9));args=parser.parse_args()
    manifest_path=args.manifest.resolve();manifest=json.loads(manifest_path.read_text())
    narration=json.loads((HERE/'narration-v2-manifest.json').read_text());alignment=json.loads((HERE/'caption-alignment.json').read_text())
    assert manifest.get('evidence_reviewed') is True,'Review actual screen inputs before rendering'
    scenes=manifest['scenes'];assert [s['paragraph'] for s in scenes]==list(range(1,9))
    assert narration['words']==312 and len(alignment['scenes'])==8
    assert manifest['public_url']=='https://proofpay-evaluation-lab.vercel.app'
    inputs=[];total=0
    for scene,row in zip(scenes,narration['scenes']):
        assert scene['mode']==('saved-evidence' if scene['paragraph']==6 else 'rehearsal')
        assert isinstance(scene['heading'],str) and len(scene['heading'])<=90
        hold=scene.get('tail_hold_seconds',1.2);assert type(hold) in (int,float) and 0<=hold<=3
        scene['frame_count']=math.ceil((row['seconds']+hold)*FPS);scene['seconds']=scene['frame_count']/FPS
        total+=scene['seconds'];assert scene['shots']
        if args.paragraph and scene['paragraph']!=args.paragraph:
            continue  # A scene preview never opens unrelated, uncaptured inputs.
        for shot in scene['shots']:
            source=file_path(shot['path'],manifest_path.parent);info=probe(source)
            stream=next(s for s in info['streams'] if s['codec_type']=='video')
            assert source.suffix.lower() in ('.png','.jpg','.jpeg','.webp')
            width,height=stream['width'],stream['height']
            crop=rectangle(shot['crop'],width,height) if shot.get('crop') else (0,0,width,height)
            if shot.get('highlight'): rectangle(shot['highlight'],width,height)
            assert not (shot.get('gentle_zoom') and shot.get('highlight')),'Use a static highlight or a moving crop, not both'
            shot.update(resolved=source,source_width=width,source_height=height,resolved_crop=crop)
            inputs.append({'paragraph':scene['paragraph'],'file':shot['path'],'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'crop':list(crop),'gentle_zoom':bool(shot.get('gentle_zoom')),'highlight':shot.get('highlight')})
        absolute_starts=[s.get('start_seconds') for s in scene['shots']]
        if any(v is not None for v in absolute_starts):
            assert all(type(v) in (int,float) for v in absolute_starts) and absolute_starts[0]==0
            indices=[round(v*FPS) for v in absolute_starts]+[scene['frame_count']]
            counts=[b-a for a,b in zip(indices,indices[1:])]
        else:
            weights=[float(s.get('weight',1)) for s in scene['shots']];assert all(0<w<1000 for w in weights)
            counts=[round(scene['frame_count']*w/sum(weights)) for w in weights];counts[-1]+=scene['frame_count']-sum(counts)
        assert all(c>=FPS for c in counts),'Every actual state needs at least one readable second'
        scene['shot_frame_counts']=counts
    assert 135<=total<=150,f'Expected a 2:15–2:30 reviewed film, got {total}s'
    if args.check:
        print(json.dumps({'ready':True,'seconds':total,'screenshots':len(inputs),'paragraphs':1 if args.paragraph else 8,'scope':'single-scene preview' if args.paragraph else 'complete film','caption_phrases':sum(len(s['phrases']) for s in alignment['scenes'])}));return
    WORK.mkdir(exist_ok=True);parts=[];subtitles=[];offset=0
    for scene,row,captions in zip(scenes,narration['scenes'],alignment['scenes']):
        number=scene['paragraph'];seconds=scene['seconds']
        if args.paragraph and number!=args.paragraph:
            offset+=seconds;continue
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y'];graph=[]
        for index,(shot,count) in enumerate(zip(scene['shots'],scene['shot_frame_counts'])):
            cmd+=['-loop','1','-framerate',str(FPS),'-i',str(shot['resolved'])]
            x,y,w,h=shot['resolved_crop'];ratio=min(1792/w,760/h);outw=math.floor(w*ratio/2)*2;outh=math.floor(h*ratio/2)*2
            filters=[f'crop={w}:{h}:{x}:{y}',f'scale={outw}:{outh}:flags=lanczos','setsar=1']
            if shot.get('gentle_zoom'):
                filters.append(f"zoompan=z='1+0.015*min(on/{max(1,count-1)},1)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s={outw}x{outh}:fps={FPS}")
            image_y=172+(760-outh)//2
            filters += [f'pad=1920:1080:(ow-iw)/2:{image_y}:color=0xF8FAFD',f'trim=duration={count/FPS:.8f}','setpts=PTS-STARTPTS']
            if shot.get('highlight'):
                hx,hy,hw,hh=rectangle(shot['highlight'],shot['source_width'],shot['source_height'])
                assert x<=hx and y<=hy and hx+hw<=x+w and hy+hh<=y+h
                filters.append(f'drawbox=x={(1920-outw)/2+(hx-x)*outw/w:.3f}:y={image_y+(hy-y)*outh/h:.3f}:w={hw*outw/w:.3f}:h={hh*outh/h:.3f}:color=0x2855EA@0.85:t=3')
            graph.append(f'[{index}:v]'+','.join(filters)+f'[v{index}]')
        graph.append(''.join(f'[v{i}]' for i in range(len(scene['shots'])))+f"concat=n={len(scene['shots'])}:v=1:a=0[main]")
        audio_index=len(scene['shots']);cmd+=['-i',str(HERE/row['file'])]
        graph.append(f'[{audio_index}:a]loudnorm=I=-17:TP=-2:LRA=7,aresample=48000,apad,atrim=duration={seconds:.8f},asetpts=PTS-STARTPTS[audio]')
        mode='Saved AI + PayPal result · Virtual funds' if scene['mode']=='saved-evidence' else 'Interactive rehearsal · Simulated payments'
        overlays=[text_filter('brand','ProofPay',30,64,30,'2855EA'),text_filter(f'mode-{number}',mode,18,1320,42,'536178',REG),text_filter(f'heading-{number}',scene['heading'],40,64,94),text_filter(f'foot-{number}','Edited actual screen states · Neural narration',13,64,1058,'718096',REG),text_filter(f'count-{number}',f'{number:02} / 08',15,1780,1060,'718096',REG)]
        for i,p in enumerate(captions['phrases']):
            lines=textwrap.wrap(p['text'],width=67);assert len(lines)<=2
            end=p['end'] if i<len(captions['phrases'])-1 else seconds
            overlays.append(text_filter(f'caption-{number}-{i}','\n'.join(lines),30,'(w-text_w)/2',965,enable=f'gte(t,{p["start"]:.6f})*lt(t,{end:.6f})'))
            subtitles.append(f'{len(subtitles)+1}\n{stamp(offset+p["start"])} --> {stamp(offset+end)}\n'+ '\n'.join(lines)+'\n')
        # Scene transitions occur after the result has been held; no actions are invented.
        overlays += [f'fade=t=in:st=0:d=0.12:color=0xF8FAFD',f'fade=t=out:st={seconds-.12:.8f}:d=0.12:color=0xF8FAFD']
        if number==8:
            overlays.append(text_filter('end-url',manifest['public_url'].removeprefix('https://'),21,64,140,'2855EA',REG))
        graph.append('[main]'+','.join(overlays)+'[video]')
        output=WORK/f'scene-{number:02}.mp4';cmd+=['-filter_complex',';'.join(graph),'-map','[video]','-map','[audio]','-t',f'{seconds:.8f}','-r',str(FPS),'-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-threads','2','-c:a','aac','-ar','48000','-b:a','192k','-movflags','+faststart',str(output)]
        print(f'Rendering scene {number}: {seconds:.3f}s',flush=True);run(cmd);parts.append(output);offset+=seconds
    if args.paragraph:
        print(parts[0]);return
    concat=WORK/'parts.txt';concat.write_text(''.join(f"file '{p}'\n" for p in parts))
    output=HERE/'proofpay-v2-review-cut.mp4';run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(output)])
    (HERE/'proofpay-v2-captions.srt').write_text('\n'.join(subtitles))
    report={'status':'Review cut; not published or submitted','seconds':float(probe(output)['format']['duration']),'source_frames':inputs,'caption_method':alignment['method'],'independent_forced_alignment':False,'narration_words':312,'expected_video_frames':sum(s['frame_count'] for s in scenes),'source_manifest':manifest_path.name,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
    (HERE/'video-v2-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'file':output.name,'seconds':report['seconds']}),flush=True)


if __name__=='__main__': main()
