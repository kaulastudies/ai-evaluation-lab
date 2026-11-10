#!/usr/bin/env python3
"""Verify the actual rendered film and extract full-size review frames."""
from pathlib import Path
import array,hashlib,json,math,re,subprocess

HERE=Path(__file__).resolve().parent
VIDEO=HERE/'proofpay-v2-review-cut.mp4'
FONT='/usr/share/fonts/truetype/open-sans/OpenSans-Bold.ttf'


def run(args,**kwargs):return subprocess.run(args,check=True,**kwargs)


def timecode(text):
    h,m,s,ms=map(int,re.split('[:,]',text));return h*3600+m*60+s+ms/1000


def main():
    metadata=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(VIDEO)],capture_output=True,text=True).stdout)
    video=next(s for s in metadata['streams'] if s['codec_type']=='video');audio=next(s for s in metadata['streams'] if s['codec_type']=='audio')
    assert (video['width'],video['height'],video['r_frame_rate'])==(1920,1080,'30/1')
    assert 135<=float(metadata['format']['duration'])<=150
    assert abs(float(video['duration'])-float(audio['duration']))<0.05
    run(['ffmpeg','-hide_banner','-v','error','-i',str(VIDEO),'-f','null','-'],capture_output=True)
    samples=array.array('f');samples.frombytes(run(['ffmpeg','-hide_banner','-v','error','-i',str(VIDEO),'-vn','-ac','1','-ar','48000','-f','f32le','-'],capture_output=True).stdout)
    peak=max(abs(x) for x in samples);clipped=sum(abs(x)>=1 for x in samples);assert clipped==0
    srt=(HERE/'proofpay-v2-captions.srt').read_text();blocks=srt.strip().split('\n\n')
    text=' '.join(' '.join(b.splitlines()[2:]) for b in blocks)
    assert ' '.join(text.split())==' '.join((HERE/'narration-v2-exact.txt').read_text().split())
    last=0
    for start,end in re.findall(r'(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)',srt):
        start,end=timecode(start),timecode(end);assert last-.002<=start<end<=float(metadata['format']['duration']);last=end
    narration=json.loads((HERE/'narration-v2-manifest.json').read_text());frames=json.loads((HERE/'frames-v2.json').read_text());alignment=json.loads((HERE/'caption-alignment.json').read_text())
    review=HERE/'review-frames-v2';review.mkdir(exist_ok=True);shots_dir=HERE/'review-shots-v2';shots_dir.mkdir(exist_ok=True)
    sample_local=[6,15.5,9.5,11,8.2,5.2,7,9]
    offset=0;scenes=[];shot_rows=[]
    for scene,row,point in zip(frames['scenes'],narration['scenes'],sample_local):
        seconds=math.ceil((row['seconds']+scene['tail_hold_seconds'])*30)/30
        preview=review/f"scene-{scene['paragraph']:02}.jpg"
        run(['ffmpeg','-hide_banner','-v','error','-y','-ss',f'{offset+point:.6f}','-i',str(VIDEO),'-frames:v','1','-q:v','2',str(preview)])
        scenes.append({'paragraph':scene['paragraph'],'heading':scene['heading'],'mode':scene['mode'],'start':offset,'seconds':seconds,'review_frame':str(preview.relative_to(HERE)),'sample_at':offset+point})
        for index,shot in enumerate(scene['shots']):
            start=round(shot['start_seconds']*30)/30
            end=round(scene['shots'][index+1]['start_seconds']*30)/30 if index+1<len(scene['shots']) else seconds
            sample=offset+start+min(.65,(end-start)/2)
            image=shots_dir/f"scene-{scene['paragraph']:02}-shot-{index+1:02}.jpg"
            run(['ffmpeg','-hide_banner','-v','error','-y','-ss',f'{sample:.6f}','-i',str(VIDEO),'-frames:v','1','-q:v','2',str(image)])
            shot_rows.append({'paragraph':scene['paragraph'],'shot':index+1,'mode':scene['mode'],'source':shot['path'],'crop':shot['crop'],'start':offset+start,'end':offset+end,'sample_at':sample,'review_frame':str(image.relative_to(HERE))})
        offset+=seconds
    run(['ffmpeg','-hide_banner','-v','error','-y','-framerate','1','-start_number','1','-i',str(review/'scene-%02d.jpg'),'-vf',f"scale=960:540,drawbox=x=856:y=0:w=104:h=33:color=0x2855EA:t=fill,drawtext=fontfile={FONT}:text='Scene %{{eif\\:n+1\\:d}}':fontsize=20:fontcolor=white:x=865:y=3,tile=2x4",'-frames:v','1','-q:v','2',str(HERE/'proofpay-v2-contact-sheet.jpg')])
    result={'file':VIDEO.name,'seconds':float(metadata['format']['duration']),'bytes':VIDEO.stat().st_size,'sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest(),'full_decode_passed':True,'video':{k:video[k] for k in ('codec_name','width','height','r_frame_rate','duration','nb_frames')},'audio':{k:audio[k] for k in ('codec_name','sample_rate','channels','duration')},'decoded_audio_peak_dbfs':round(20*math.log10(peak),3),'full_scale_samples':clipped,'captions':{'phrases':len(blocks),'exact_words':len(text.split()),'minimum_phoneme_prefix_match':min(p['phoneme_prefix_match'] for s in alignment['scenes'] for p in s['phrases']),'method':alignment['method'],'independent_forced_alignment':False},'rehearsal_operation_id':frames['rehearsal_operation_id'],'source_commit':frames['source_commit'],'scenes':scenes,'shots':shot_rows,'status':'Review cut; not published or submitted','limits':['Edited actual captured states; no fabricated actions or continuous-recording claim.','Scene 6 is labelled saved completed external evidence; other scenes are the isolated simulated rehearsal.','Signal/timing checks do not replace a normal-speed listening review.']}
    (HERE/'video-v2-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('seconds','bytes','full_decode_passed','decoded_audio_peak_dbfs','full_scale_samples','captions')},indent=2))


if __name__=='__main__':main()
