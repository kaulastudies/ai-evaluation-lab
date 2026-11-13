"""Local SQLite receiving system. Identity is supplied by a trusted test harness."""
import json
import sqlite3
from contextlib import contextmanager
from baseline.revocation_demo import digest


class Receiver:
    def __init__(self, path, mutation=None):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.mutation = mutation  # Deliberately broken controls, never a production option.
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS grants(id TEXT PRIMARY KEY, agent TEXT, resource TEXT,
          parent TEXT REFERENCES grants(id), revoked INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS queue(id TEXT PRIMARY KEY, grant_id TEXT, agent TEXT,
          resource TEXT, value TEXT);
        CREATE TABLE IF NOT EXISTS effects(id TEXT PRIMARY KEY, resource TEXT, value TEXT);
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, body TEXT, hash TEXT);
        ''')

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def record(self, kind, **data):
        last = self.db.execute('SELECT seq, hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        body = dict(seq=last[0]+1 if last else 1, previous_hash=last[1] if last else '0'*64,
                    kind=kind, **data)
        self.db.execute('INSERT INTO events VALUES(?,?,?)',
                        (body['seq'], json.dumps(body, sort_keys=True), digest(body)))

    def allowed(self, grant_id, agent, resource):
        first = True
        while grant_id:
            row = self.db.execute('SELECT agent,resource,parent,revoked FROM grants WHERE id=?', (grant_id,)).fetchone()
            if row is None or row[3] or row[1] != resource or (first and row[0] != agent):
                return False
            grant_id = None if self.mutation == 'ignore_parent' else row[2]
            first = False
        return not first

    def grant(self, gid, agent, resource, parent=None, issuer=None):
        with self.transaction():
            if parent and not self.allowed(parent, issuer, resource):
                self.record('DELEGATION_DENIED', grant_id=gid)
                return False
            self.db.execute('INSERT INTO grants(id,agent,resource,parent) VALUES(?,?,?,?)', (gid, agent, resource, parent))
            self.record('GRANT', grant_id=gid, parent=parent, resource=resource)
        return True

    def revoke(self, gid):
        # Administrative fixture operation, not a public authenticated API.
        with self.transaction():
            self.db.execute('UPDATE grants SET revoked=1 WHERE id=?', (gid,))
            self.record('REVOKE', grant_id=gid)

    def enqueue(self, aid, gid, agent, resource, value):
        with self.transaction():
            if not self.allowed(gid, agent, resource):
                self.record('QUEUE_DENIED', action_id=aid)
                return False
            self.db.execute('INSERT INTO queue VALUES(?,?,?,?,?)', (aid,gid,agent,resource,value))
            self.record('QUEUED', action_id=aid, grant_id=gid)
        return True

    def deliver(self, aid):
        with self.transaction():
            row = self.db.execute('SELECT grant_id,agent,resource,value FROM queue WHERE id=?', (aid,)).fetchone()
            if row is None:
                raise KeyError(aid)
            if self.mutation != 'queue_only' and not self.allowed(*row[:3]):
                result = 'DENIED'
            elif self.mutation == 'global_invalidation' and self.db.execute('SELECT 1 FROM grants WHERE revoked=1').fetchone():
                result = 'DENIED'
            elif self.db.execute('SELECT 1 FROM effects WHERE id=?', (aid,)).fetchone():
                result = 'ALREADY_COMMITTED'
            else:
                self.db.execute('INSERT INTO effects VALUES(?,?,?)', (aid,row[2],row[3]))
                result = 'COMMITTED'
            self.record(result, action_id=aid)
        return result

    def close(self):
        self.db.close()
