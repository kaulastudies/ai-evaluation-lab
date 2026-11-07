"""Run baseline, five receiver scenarios, and three known-bad controls."""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from receiver import Receiver
from baseline.revocation_demo import digest

if not __debug__:
    raise RuntimeError('Run without -O: this verification runner uses assertions')

ROOT = Path(__file__).resolve().parent


def scenario(name, path, mutation=None):
    r = Receiver(path, mutation)
    r.grant('root', 'agent', 'document')
    results = []
    if name == 'delegation':
        assert r.grant('child', 'worker', 'document', 'root', 'agent')
        assert not r.grant('wide', 'worker', 'other', 'root', 'agent')
        r.enqueue('action', 'child', 'worker', 'document', 'changed')
    else:
        assert r.enqueue('action', 'root', 'agent', 'document', 'changed')
    if name in ('revocation', 'delegation', 'restart_retry'):
        r.revoke('root')
        if name == 'delegation':
            assert not r.grant('late', 'worker', 'document', 'root', 'agent')
        if name == 'restart_retry':
            r.close()
            r = Receiver(path, mutation)
        results = [r.deliver('action'), r.deliver('action')]
        expected = []
    elif name == 'unrelated_change':
        r.grant('other', 'other-agent', 'other-document')
        r.revoke('other')
        results = [r.deliver('action')]
        expected = [('action', 'document', 'changed')]
    else:
        results = [r.deliver('action'), r.deliver('action')]
        expected = [('action', 'document', 'changed')]
    r.close()
    # Fresh read-only connection: evidence comes from committed receiver state.
    with sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True) as db:
        effects = db.execute('SELECT * FROM effects ORDER BY id').fetchall()
        events = [dict(body=json.loads(body), hash=h) for body,h in db.execute('SELECT body,hash FROM events ORDER BY seq')]
    prev = '0'*64
    for seq, event in enumerate(events, 1):
        assert event['body']['seq'] == seq and event['body']['previous_hash'] == prev
        assert digest(event['body']) == event['hash']
        prev = event['hash']
    expected_results = ['DENIED','DENIED'] if not expected else (['COMMITTED'] if name == 'unrelated_change' else ['COMMITTED','ALREADY_COMMITTED'])
    return dict(scenario=name, mutation=mutation, passed=effects == expected and results == expected_results,
                delivery_results=results, receiver_rows=effects, expected_rows=expected, events=events)


def main():
    baseline = subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT/'baseline',capture_output=True,text=True)
    if baseline.returncode:
        raise RuntimeError(baseline.stderr)
    names = ['revocation','restart_retry','delegation','unrelated_change','duplicate_delivery']
    with tempfile.TemporaryDirectory(prefix='authority-lifecycle-') as temp:
        temp = Path(temp)
        cases = [scenario(n,temp/(n+'.sqlite')) for n in names]
        controls = [scenario(n,temp/(m+'.sqlite'),m) for n,m in [('revocation','queue_only'),('delegation','ignore_parent'),('unrelated_change','global_invalidation')]]
    assert all(c['passed'] for c in cases), 'Receiver scenario failed'
    assert all(not c['passed'] for c in controls), 'Known-bad implementation escaped detection'
    sources = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.rglob('*.py'))}
    out = dict(scope='Local SQLite fixture; not Harmonic or live TIP integration',baseline_log=baseline.stderr,
               scenarios=cases,known_bad_controls=controls,source_sha256=sources)
    target = Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'evidence.json'
    target.write_text(json.dumps(out,indent=2)+'\n')
    print('PASS: baseline 5/5; receiver scenarios 5/5; known-bad controls detected 3/3')
    print(target)

if __name__ == '__main__':
    main()
