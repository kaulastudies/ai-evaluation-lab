"""Synthesize the reviewed story with local Apache-2.0 Kokoro weights."""
from offline_guard import lock_network
NETWORK_GUARD = lock_network()
from pathlib import Path
import dataclasses,hashlib,json,time,subprocess
import onnxruntime as ort
# Official ONNX Runtime API: disable platform telemetry before any session.
ort.disable_telemetry_events()
import soundfile as sf
from kokoro_onnx import Kokoro

HERE=Path(__file__).resolve().parent
source=(HERE/'narration-v2-exact.txt').read_text()
text=source.strip()
paragraphs=[p.strip() for p in text.split('\n\n') if p.strip()]
assert len(paragraphs)==8 and len(text.split())==312
(HERE/'narration-v2').mkdir(exist_ok=True)
options=ort.SessionOptions();options.intra_op_num_threads=4;options.inter_op_num_threads=1
session=ort.InferenceSession(str(HERE/'models/kokoro-v1.0.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
model=Kokoro.from_session(session,str(HERE/'models/voices-v1.0.bin'))
rows=[]
for n,paragraph in enumerate(paragraphs,1):
 spoken=paragraph.replace('ProofPay','Proof Pay').replace('PayPal','Pay Pal').replace('GPT','G P T')
 start=time.monotonic()
 samples,rate,timings=model.create_timed(spoken,voice='af_heart',speed=0.94,lang='en-us',sentence_pause=0.3,clause_pause=0.12)
 output=HERE/f'narration-v2/scene-{n:02}.wav';sf.write(output,samples,rate,subtype='PCM_16')
 row={'paragraph':n,'text':paragraph,'spoken_text':spoken,'file':str(output.relative_to(HERE)),'seconds':len(samples)/rate,'sample_rate':rate,'synthesis_seconds':round(time.monotonic()-start,3),'timings':[dataclasses.asdict(t) for t in timings]}
 rows.append(row);print(json.dumps({k:v for k,v in row.items() if k not in ('text','spoken_text','timings')}),flush=True)
manifest={'model':'Kokoro-82M v1.0 ONNX','voice':'af_heart','speed':0.94,'sample_rate':24000,'words':312,'paragraphs':8,'source':'narration-v2-exact.txt','source_sha256':hashlib.sha256(source.encode()).hexdigest(),'funding':'Local CPU inference; no API, provider credits or paid service','network_guard':NETWORK_GUARD,'timing_method':'Model-predicted phoneme durations returned by kokoro-onnx; no claim of independent forced alignment','speech_seconds':sum(r['seconds'] for r in rows),'scenes':rows}
(HERE/'narration-v2-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
parts=HERE/'narration-v2/parts.txt';parts.write_text(''.join(f"file '{HERE/r['file']}'\n" for r in rows))
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(parts),'-af','loudnorm=I=-17:TP=-2:LRA=7','-c:a','libmp3lame','-b:a','160k',str(HERE/'proofpay-v2-narration-preview.mp3')],check=True)
print(json.dumps({'speech_seconds':manifest['speech_seconds'],'words':312,'voice':'af_heart','speed':0.94}),flush=True)
