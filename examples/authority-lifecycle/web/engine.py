"""Interactive scenarios over the unchanged receiver, usable in CPython/Pyodide."""
import json
from pathlib import Path
import sqlite3
import tempfile

from receiver import Receiver
from baseline.revocation_demo import digest

CASES = {
    'revocation': ('Revoke queued authority', 'queue_only'),
    'delegation': ('Revoke the parent grant', 'ignore_parent'),
    'continuation': ('Preserve unrelated authorized work', 'global_invalidation'),
    'duplicate': ('Deliver the same action twice', None),
    'ack_loss': ('Lose the reply after commit', None),
    'committed': ('Revoke after the write commits', None),
    'rollback': ('Fail between write and event record', None),
    'contention': ('Deliver while revocation holds the lock', None),
}


class Demo:
    def __init__(self, case='revocation', broken=False):
        if case not in CASES:
            raise ValueError('Unknown scenario')
        if broken and CASES[case][1] is None:
            raise ValueError('No broken control defined for this scenario')
        self.case, self.broken = case, broken
        self.temp = tempfile.TemporaryDirectory(prefix='authority-demo-')
        self.path = Path(self.temp.name) / 'receiver.sqlite'
        self.receiver = Receiver(self.path, CASES[case][1] if broken else None)
        self.history, self.deliveries = [], []
        self.index = 0
        self.steps = [('grant', 'Authorize agent A for document A')]
        if case == 'delegation':
            self.steps += [('child', 'Delegate the same scope to worker B')]
        if case == 'continuation':
            self.steps += [('other', 'Authorize an unrelated document B')]
        self.steps += [('queue', 'Queue action A under its existing grant')]
        if case in ('revocation', 'delegation', 'continuation'):
            self.steps += [('revoke', 'Revoke unrelated grant B' if case == 'continuation'
                            else 'Revoke the parent grant' if case == 'delegation'
                            else 'Revoke grant A')]
        if case == 'rollback':
            self.steps += [('rollback', 'Inject a failure after SQL insert, before recording')]
        if case == 'contention':
            self.steps += [('contention', 'Attempt delivery while revocation owns the write lock')]
        self.steps += [('ack_loss' if case == 'ack_loss' else 'deliver',
                       'Commit the write, then discard the reply' if case == 'ack_loss'
                       else 'Attempt delivery at the receiving system')]
        if case == 'committed':
            self.steps += [('revoke', 'Revoke grant A after the effect committed')]
        if case not in ('continuation', 'rollback', 'contention'):
            self.steps += [('retry', 'Retry the same queued action through a new connection')]

    def close(self):
        self.receiver.close()
        self.temp.cleanup()

    def _deliver(self, fresh=False):
        r = Receiver(self.path, self.receiver.mutation) if fresh else self.receiver
        try:
            result = r.deliver('action-A')
            self.deliveries.append(result)
            return result
        finally:
            if fresh:
                r.close()

    def advance(self):
        if self.index >= len(self.steps):
            return self.state()
        operation, label = self.steps[self.index]
        r = self.receiver
        if operation == 'grant':
            result = r.grant('grant-A', 'agent-A', 'document-A')
        elif operation == 'other':
            result = r.grant('grant-B', 'agent-C', 'document-B')
        elif operation == 'child':
            result = r.grant('child-A', 'worker-B', 'document-A', 'grant-A', 'agent-A')
        elif operation == 'queue':
            child = self.case == 'delegation'
            result = r.enqueue('action-A', 'child-A' if child else 'grant-A',
                               'worker-B' if child else 'agent-A', 'document-A', 'approved-change')
        elif operation == 'revoke':
            r.revoke('grant-B' if self.case == 'continuation' else 'grant-A')
            result = 'REVOCATION_COMMITTED'
        elif operation in ('deliver', 'retry'):
            result = self._deliver(fresh=operation == 'retry')
        elif operation == 'ack_loss':
            self._deliver()
            result = 'REPLY_DISCARDED_AFTER_COMMIT'
        elif operation == 'rollback':
            original = r.record
            def injected(kind, **data):
                if kind == 'COMMITTED':
                    raise RuntimeError('injected recording failure')
                return original(kind, **data)
            r.record = injected
            try:
                r.deliver('action-A')
                raise AssertionError('Injected recording failure was not raised')
            except RuntimeError as error:
                if str(error) != 'injected recording failure':
                    raise
                result = 'TRANSACTION_ROLLED_BACK'
            finally:
                r.record = original
        elif operation == 'contention':
            worker = Receiver(self.path)
            worker.db.execute('PRAGMA busy_timeout=0')
            try:
                with r.transaction():
                    r.db.execute("UPDATE grants SET revoked=1 WHERE id='grant-A'")
                    r.record('REVOKE', grant_id='grant-A')
                    try:
                        worker.deliver('action-A')
                        raise AssertionError('Delivery unexpectedly acquired the write lock')
                    except sqlite3.OperationalError as error:
                        if error.sqlite_errorcode != sqlite3.SQLITE_BUSY:
                            raise
                        result = 'SQLITE_BUSY_THEN_REVOCATION_COMMITTED'
            finally:
                worker.close()
        self.index += 1
        state = self._read_state()
        self.history.append(dict(step=self.index, operation=operation, label=label,
                                 result=result, effects=state['effects'],
                                 grants=state['grants'], events=state['events']))
        return self.state()

    def _read_state(self):
        # The observer is separate from Receiver's connection and queries committed rows.
        with sqlite3.connect(self.path.resolve().as_uri() + '?mode=ro', uri=True) as db:
            effects = db.execute('SELECT id,resource,value FROM effects ORDER BY id').fetchall()
            grants = db.execute('SELECT id,agent,resource,parent,revoked FROM grants ORDER BY id').fetchall()
            queue = db.execute('SELECT id,grant_id,agent,resource,value FROM queue ORDER BY id').fetchall()
            events = [dict(body=json.loads(body), hash=h) for body, h in
                      db.execute('SELECT body,hash FROM events ORDER BY seq')]
            integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
        previous, valid = '0' * 64, True
        for seq, event in enumerate(events, 1):
            body = event['body']
            valid &= (body['seq'] == seq and body['previous_hash'] == previous and digest(body) == event['hash'])
            previous = event['hash']
        return dict(effects=effects, grants=grants, queue=queue, events=events,
                    integrity=integrity, event_chain_valid=valid)

    def state(self):
        state = self._read_state()
        done = self.index == len(self.steps)
        denied = self.case in ('revocation', 'delegation', 'contention')
        expected_rows = [] if denied else [('action-A', 'document-A', 'approved-change')]
        expected_results = (['DENIED'] if self.case == 'contention' else ['DENIED', 'DENIED']) if denied else (
            ['COMMITTED'] if self.case in ('continuation', 'rollback') else
            ['COMMITTED', 'DENIED'] if self.case == 'committed' else ['COMMITTED', 'ALREADY_COMMITTED'])
        contract_met = (state['effects'] == expected_rows and self.deliveries == expected_results
                        and state['integrity'] == 'ok' and state['event_chain_valid']) if done else None
        return dict(case=self.case, title=CASES[self.case][0], broken=self.broken,
                    mutation=self.receiver.mutation, step=self.index, total_steps=len(self.steps),
                    next_step=self.steps[self.index][1] if not done else None,
                    done=done, contract_met=contract_met, expected_rows=expected_rows,
                    expected_deliveries=expected_results, delivery_results=list(self.deliveries),
                    history=list(self.history), **state)


active = None


def command_json(command):
    global active
    command = json.loads(command)
    if command['action'] == 'reset':
        if active is not None:
            active.close()
        active = Demo(command['case'], command.get('broken', False))
    elif active is None:
        raise ValueError('Start a scenario first')
    elif command['action'] == 'next':
        active.advance()
    elif command['action'] == 'run':
        while not active.state()['done']:
            active.advance()
    else:
        raise ValueError('Unknown command')
    return json.dumps(active.state())
  
