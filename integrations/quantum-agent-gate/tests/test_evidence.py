from qag import ExecutionRequest,CircuitFacts,Decision,make_lab_record,verify_record_hash

def test_hash_is_stable_and_detects_mutation():
    args=(ExecutionRequest('agent','r1','sim',128),CircuitFacts(2,2),Decision('ALLOW',('PREFLIGHT_RESERVED_ONLY',),True))
    a=make_lab_record(*args,evaluation_id='e1',timestamp='2026-10-19T00:00:00+00:00')
    b=make_lab_record(*args,evaluation_id='e1',timestamp='2026-10-19T00:00:00+00:00')
    assert a==b and verify_record_hash(a)
    a['verification']['reserved']=False
    assert not verify_record_hash(a)

def test_denied_record_uses_valid_labels():
    r=make_lab_record(ExecutionRequest('agent','r2','qpu',128),CircuitFacts(2,2),Decision('DENY',('REMOTE_DISABLED',)),evaluation_id='e2')
    assert (r['final_label'],r['final_status'])==('FAIL','REJECTED')
    assert verify_record_hash(r)
