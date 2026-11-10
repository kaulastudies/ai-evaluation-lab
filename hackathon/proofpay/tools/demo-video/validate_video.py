#!/usr/bin/env python3
"""Offline decode, timing, audio-signal and nine-scene visual review artifacts."""
from pathlib import Path
import array
import hashlib
import json
import math
import re
import subprocess

HERE = Path(__file__).resolve().parent
VIDEO = HERE / 'proofpay-narrated-review-cut.mp4'
FONT = '/usr/share/fonts/truetype/open-sans/OpenSans-Bold.ttf'


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def main():
    metadata = json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(VIDEO)],capture_output=True,text=True).stdout)
    video = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
    audio = next(s for s in metadata['streams'] if s['codec_type'] == 'audio')
    assert (video['width'], video['height']) == (1920,1080)
    assert video['r_frame_rate'] == '30/1'
    assert float(metadata['format']['duration']) < 170
    assert abs(float(video['duration']) - float(audio['duration'])) < 0.05
    run(['ffmpeg','-hide_banner','-v','error','-i',str(VIDEO),'-f','null','-'],capture_output=True)
    floats = array.array('f')
    floats.frombytes(run(['ffmpeg','-hide_banner','-v','error','-i',str(VIDEO),'-vn','-ac','1','-ar','48000','-f','f32le','-'],capture_output=True).stdout)
    peak = max(abs(sample) for sample in floats)
    clipped = sum(abs(sample) >= 1 for sample in floats)
    assert clipped == 0, 'Decoded AAC contains full-scale or clipped samples'
    rows = json.loads((HERE/'narration-manifest.json').read_text())['scenes']
    out = HERE/'review-frames'; out.mkdir(exist_ok=True)
    offset, picks = 0.0, []
    for row in rows:
        seconds = math.ceil(row['scene_seconds']*30)/30
        time = offset + seconds / 2
        target = out/f"scene-{row['paragraph']:02}.png"
        run(['ffmpeg','-hide_banner','-v','error','-y','-ss',f'{time:.6f}','-i',str(VIDEO),'-frames:v','1',str(target)])
        picks.append({'paragraph':row['paragraph'],'start':offset,'seconds':seconds,'sample_time':time,'review_frame':str(target.relative_to(HERE))})
        offset += seconds
    # Contact sheet uses actual decoded video frames, not recreated screenshots.
    run(['ffmpeg','-hide_banner','-v','error','-y','-framerate','1','-start_number','1','-i',str(out/'scene-%02d.png'),'-vf',f"scale=960:540,drawbox=x=0:y=0:w=112:h=35:color=0x111D32:t=fill,drawtext=fontfile={FONT}:text='Scene %{{eif\\:n+1\\:d}}':fontsize=22:fontcolor=white:x=10:y=4,tile=3x3",'-frames:v','1','-q:v','2',str(HERE/'proofpay-video-contact-sheet.jpg')])
    srt = (HERE/'captions.srt').read_text()
    caption_text = ' '.join(' '.join(block.splitlines()[2:]) for block in srt.strip().split('\n\n'))
    approved_text = ' '.join((HERE/'narration-exact-script.txt').read_text().split())
    assert ' '.join(caption_text.split()) == approved_text, 'Subtitle text differs from the approved narration'
    times=[]
    def seconds(value):
        h,m,s,ms=map(int,re.split('[:,]',value)); return h*3600+m*60+s+ms/1000
    for start,end in re.findall(r'(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)',srt):
        start,end=seconds(start),seconds(end)
        assert start < end <= float(metadata['format']['duration'])
        if times: assert start >= times[-1][1]-0.002
        times.append((start,end))
    result={
        'status':'Review cut, not published or submitted',
        'file':VIDEO.name,'sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest(),
        'duration_seconds':float(metadata['format']['duration']),
        'video':{key:video[key] for key in ('codec_name','width','height','r_frame_rate','duration','nb_frames')},
        'audio':{key:audio[key] for key in ('codec_name','sample_rate','channels','duration')},
        'full_decode_passed':True,'decoded_audio_peak_dbfs':round(20*math.log10(peak),3),
        'decoded_audio_full_scale_samples':clipped,'subtitle_entries':len(times),
        'subtitle_words_match_approved_narration':len(approved_text.split()),
        'caption_timing':'Estimated from speech lengths and punctuation; not forced-aligned; listening review remains required',
        'presenter_timing':'Actual Flite phoneme segments, source PCM verified byte-for-byte; processed timing uses audio duration scaling',
        'scenes':picks,
        'limits':['Signal checks do not constitute a human listening review.','Edited actual screen states, not a continuous recording.','Saved completed AI/PayPal evidence and a separate simulated rehearsal are explicitly labelled.']
    }
    (HERE/'video-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('duration_seconds','full_decode_passed','decoded_audio_peak_dbfs','decoded_audio_full_scale_samples','subtitle_entries')},indent=2))


if __name__ == '__main__':
    main()
