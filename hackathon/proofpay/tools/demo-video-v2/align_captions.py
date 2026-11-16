"""Map exact caption phrases to the model's returned phoneme timeline.

This uses the identical local phonemizer, checks full-paragraph equality, then
matches each text prefix to the timed phoneme sequence. It is model timing,
not independent forced alignment or word-length timing.
"""
from offline_guard import lock_network
NETWORK_GUARD=lock_network()
from pathlib import Path
import difflib,json,re
import onnxruntime as ort
ort.disable_telemetry_events()
from kokoro_onnx.tokenizer import Tokenizer

HERE=Path(__file__).resolve().parent


def spoken(text):
    return text.replace('ProofPay','Proof Pay').replace('PayPal','Pay Pal').replace('GPT','G P T')


def chunks(words):
    # Keep the model name, dollar amounts and lab name together on screen.
    protected = [phrase.split() for phrase in (
        'GPT four point one mini', 'one hundred eighty', 'one hundred sixty',
        'one hundred twenty', 'two hundred ten', 'three hundred dollars',
        'PayPal sandbox', 'Evaluation lab',
    )]
    units=[];index=0
    while index<len(words):
        length=1
        for phrase in protected:
            candidate=[word.rstrip('.,;:!?') for word in words[index:index+len(phrase)]]
            if candidate==phrase:
                length=len(phrase);break
        units.append((index,index+length));index+=length
    output=[];start=0
    for begin,end in units:
        if begin>start and (len(' '.join(words[start:end]))>74 or end-start>10):
            output.append((start,begin));start=begin
        if words[end-1].endswith(('.', '?','!')):
            output.append((start,end));start=end
    if start<len(words):output.append((start,len(words)))
    return output


def main():
    manifest=json.loads((HERE/'narration-v2-manifest.json').read_text())
    tokenizer=Tokenizer()
    result=[]
    for scene in manifest['scenes']:
        timings=scene['timings'];actual=''.join(t['phoneme'] for t in timings)
        full=tokenizer.phonemize(scene['spoken_text'])
        assert full==actual,f"Paragraph {scene['paragraph']} phonemizer output differs from actual synthesis"
        words=scene['text'].split();phrases=[];start=0.0
        for begin,end in chunks(words):
            text=' '.join(words[begin:end]);prefix=tokenizer.phonemize(spoken(' '.join(words[:end])))
            matches=[b for b in difflib.SequenceMatcher(None,prefix,actual,autojunk=False).get_matching_blocks() if b.size]
            assert matches
            coverage=sum(b.size for b in matches)/len(prefix)
            last=matches[-1];tail=len(prefix)-(last.a+last.size);target=last.b+last.size
            assert coverage>=0.94 and tail<=3 and abs(target-len(prefix))<=8, f"Ambiguous caption boundary: {scene['paragraph']} {text} {coverage} {tail}"
            finish=scene['seconds'] if end==len(words) else timings[target-1]['end']
            assert start<finish<=scene['seconds']
            phrases.append({'text':text,'start':start,'end':finish,'phoneme_prefix_match':round(coverage,5),'unmatched_terminal_phoneme_chars':tail})
            start=finish
        assert ' '.join(p['text'] for p in phrases)==scene['text']
        result.append({'paragraph':scene['paragraph'],'seconds':scene['seconds'],'phrases':phrases})
    data={'method':'Exact full-paragraph phonemizer equality; caption prefix matches mapped to returned model phoneme durations. No rough word-length timing.','independent_forced_alignment':False,'network_guard':NETWORK_GUARD,'scenes':result}
    (HERE/'caption-alignment.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'paragraphs':len(result),'caption_phrases':sum(len(s['phrases']) for s in result),'minimum_prefix_match':min(p['phoneme_prefix_match'] for s in result for p in s['phrases']),'all_exact_words':True}),flush=True)


if __name__=='__main__': main()
