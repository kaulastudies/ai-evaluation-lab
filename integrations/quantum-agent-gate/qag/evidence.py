"""Experimental adapter to AI Evaluation Lab's public evaluation-record field names."""
import hashlib
import json
from datetime import datetime,timezone
from .gate import ExecutionRequest,CircuitFacts,Decision

def canonical_bytes(obj):
    return json.dumps(obj,ensure_ascii=False,separators=(',',':'),sort_keys=True,allow_nan=False).encode('utf-8')

def make_lab_record(req:ExecutionRequest,facts:CircuitFacts,decision:Decision,*,evaluation_id:str,model='unattributed',timestamp=None):
    if timestamp is None:
        timestamp=datetime.now(timezone.utc).isoformat()
    accepted=decision.verdict=='ALLOW'
    record={
        'evaluation_id':evaluation_id,'task_id':'QAG-001','task_version':'0.1.0',
        'provider':'quantum-agent-gate','model':model,
        'response':json.dumps({'actor':req.actor,'request_id':req.request_id,'target':req.target_id,'shots':req.shots},sort_keys=True),
        'review':{'status':'NOT_REVIEWED'},
        'verification':{'verdict':decision.verdict,'reasons':list(decision.reasons),
                        'facts':{'qubits':facts.qubits,'depth':facts.depth},'reserved':decision.reserved},
        'disagreement':False,'final_label':'PASS' if accepted else 'FAIL',
        'final_status':'ACCEPTED' if accepted else 'REJECTED','created_at':timestamp}
    record['record_hash']=hashlib.sha256(canonical_bytes(record)).hexdigest()
    return record

def verify_record_hash(record):
    published=record.get('record_hash')
    payload={k:v for k,v in record.items() if k!='record_hash'}
    return isinstance(published,str) and hashlib.sha256(canonical_bytes(payload)).hexdigest()==published
