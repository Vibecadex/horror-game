from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import threading
from contextlib import closing
from datetime import datetime, timezone
from http.client import HTTPConnection, HTTPException
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
STATES = ('ready', 'active', 'blocked', 'review', 'done')
MEMBERS = {'game', 'chamber', 'scanner', 'reference'}
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$')
FORBIDDEN = {'intermediate', 'saved', 'deriveddatacache', 'binaries', 'build', '.tool-cache', '.git'}


def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


class Problem(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class Workspace:
    def __init__(self, root=ROOT, local=None, bindings=None):
        self.root = Path(root).resolve()
        self.local = Path(local or self.root / 'workspace/local')
        self.local.mkdir(parents=True, exist_ok=True)
        self.catalog = read_json(self.root / 'workspace/catalog.json')
        self.seeds = read_json(self.root / 'workspace/work-items.json')['items']
        if bindings is None:
            file = self.local / 'bindings.json'
            if not file.exists():
                file.write_bytes((self.root / 'workspace/bindings.example.json').read_bytes())
            bindings = read_json(file)
        if bindings.get('schemaVersion') != 1 or set(bindings.get('members', {})) != MEMBERS:
            raise ValueError('Bindings require schemaVersion 1 and the four declared members')
        if bindings['members']['game'] != '.':
            raise ValueError('The game binding must be this integration checkout (.)')
        self.bindings = {key: (None if value is None else (self.root / value).resolve())
                         for key, value in bindings['members'].items()}
        self.validate_catalog()
        implementation = [p for p in (self.root/'tools/federated_workspace').rglob('*')
                          if p.is_file() and p.suffix in {'.py','.js','.css','.html','.svg'}]
        implementation += [self.root/'tools/workspace.py',self.root/'workspace/catalog.json',self.root/'workspace/work-items.json',
                           self.root/'workspace/agent-contracts.json',self.root/'workspace/AGENT_WORKFLOW.md',self.root/'workspace/AGENT_RULES.md']
        self.build_id = 'workspace_' + digest(encoded({p.relative_to(self.root).as_posix():digest(p.read_bytes()) for p in sorted(implementation)}))[:16]
        self.db = self.local / 'workspace.sqlite3'
        self.snapshot = None
        self.refresh_lock = threading.Lock()
        self.initialize_store()

    def connection(self):
        conn = sqlite3.connect(self.db, timeout=5, isolation_level=None)
        conn.row_factory = sqlite3.Row
        return conn

    def validate_catalog(self):
        if self.catalog.get('schemaVersion') != 1:
            raise ValueError('Unsupported catalog schema')
        modules = {x['id'] for x in self.catalog['modules']}
        artifacts = {x['id'] for x in self.catalog['artifacts']}
        work = {x['id'] for x in self.seeds}
        for key, values in [('modules', modules), ('artifacts', artifacts)]:
            if len(values) != len(self.catalog[key]) or not all(ID.fullmatch(x) for x in values):
                raise ValueError(f'Duplicate or invalid {key} identifiers')
        if len(work) != len(self.seeds) or not all(ID.fullmatch(x) for x in work):
            raise ValueError('Duplicate or invalid work identifiers')
        for module in self.catalog['modules']:
            assert module['member'] in MEMBERS and set(module['dependencies']) <= modules
        for artifact in self.catalog['artifacts']:
            assert artifact['module'] in modules and artifact['member'] in MEMBERS
            path = Path(artifact['path'])
            if path.is_absolute() or '..' in path.parts or any(x.lower() in FORBIDDEN for x in path.parts):
                raise ValueError('Artifact path must be a scoped source path')
            if path.suffix.lower() in {'.uasset', '.umap', '.pem', '.key', '.env', '.exe', '.dll'}:
                raise ValueError('Artifact type is outside source inspection scope')
        for item in self.seeds:
            assert item['module'] in modules and item['status'] in STATES
            assert set(item['dependsOn']) <= work and set(item['evidence']) <= artifacts
        graph = {x['id']: x['dependsOn'] for x in self.seeds}
        def visit(key, stack):
            if key in stack:
                raise ValueError('Work dependency cycle')
            for dependency in graph[key]:
                visit(dependency, stack | {key})
        for key in graph:
            visit(key, set())
        for gate in self.catalog['gates']:
            assert gate['source'] in artifacts
        for service in self.catalog['services']:
            url = urlsplit(service['url'])
            if url.scheme != 'http' or url.hostname != '127.0.0.1' or url.username or url.password:
                raise ValueError('Service adapters are explicit loopback HTTP only')

    def initialize_store(self):
        with closing(self.connection()) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS work (
                    id TEXT PRIMARY KEY, status TEXT NOT NULL, owner TEXT NOT NULL,
                    rationale TEXT NOT NULL, evidence TEXT NOT NULL, revision INTEGER NOT NULL,
                    updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL,
                    kind TEXT NOT NULL, entity_id TEXT NOT NULL, payload TEXT NOT NULL);
                PRAGMA user_version=1;
            ''')
            conn.execute('BEGIN IMMEDIATE')
            try:
                for item in self.seeds:
                    result = conn.execute('INSERT OR IGNORE INTO work VALUES (?,?,?,?,?,?,?)',
                        (item['id'], item['status'], item['owner'], 'Initial work plan; no acceptance implied.',
                         json.dumps(item['evidence']), 0, now()))
                    if result.rowcount:
                        self.event(conn, 'work-created', item['id'], {'title': item['title'], 'status': item['status']})
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    @staticmethod
    def event(conn, kind, entity, payload):
        conn.execute('INSERT INTO events(at,kind,entity_id,payload) VALUES (?,?,?,?)',
                     (now(), kind, entity, json.dumps(payload, ensure_ascii=False)))

    def artifact_path(self, record):
        root = self.bindings[record['member']]
        if root is None:
            raise Problem(404, 'Member is not bound on this machine')
        path = (root / record['path']).resolve()
        if not path.is_relative_to(root):
            raise Problem(403, 'Artifact escaped its member boundary')
        return path

    def git_inspect(self, path):
        env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
        def git(*args):
            p = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-C', str(path), *args],
                               capture_output=True, text=True, timeout=5, env=env)
            if p.returncode:
                raise ValueError('Git inspection unavailable')
            return p.stdout.strip()
        try:
            return {'state': 'observed', 'branch': git('rev-parse', '--abbrev-ref', 'HEAD'),
                    'head': git('rev-parse', 'HEAD'),
                    'localChangeEntries': len(git('status', '--porcelain', '--untracked-files=normal').splitlines()),
                    'remoteFreshness': 'Not fetched by the workspace'}
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return {'state': 'unavailable', 'remoteFreshness': 'Unknown'}

    def inspect_service(self, service, artifacts):
        url = urlsplit(service['url'])
        conn = HTTPConnection(url.hostname, url.port, timeout=1.5)
        try:
            conn.request('GET', service['probe'])
            response = conn.getresponse()
            raw = response.read(1024 * 1024 + 1)
            if response.status != 200 or len(raw) > 1024 * 1024:
                raise ValueError('Probe failed')
            if service.get('identityArtifact'):
                source = next(a for a in artifacts if a['id'] == service['identityArtifact'])
                match = source['state'] == 'verified' and digest(raw) == source['sha256']
            else:
                data = json.loads(raw)
                match = data.get('app') == service['identityApp'] and data.get('ok') is True
                if service['id'] == 'studio':
                    match = match and Path(data.get('workspace', '')).resolve() == self.root
            return dict(service, state='verified' if match else 'identity-mismatch', observedAt=now())
        except (OSError, ValueError, HTTPException):
            return dict(service, state='unavailable', observedAt=now())
        finally:
            conn.close()

    def refresh(self):
        with self.refresh_lock:
            members = []
            for member, path in self.bindings.items():
                exists = path is not None and path.is_dir()
                members.append({'id': member, 'path': str(path) if path else None,
                                'state': 'observed' if exists else 'missing' if path else 'unbound',
                                'observedAt': now(), 'git': self.git_inspect(path) if exists and member != 'reference' else None})
            artifacts = []
            for spec in self.catalog['artifacts']:
                record = dict(spec, state='missing', observedAt=now())
                try:
                    path = self.artifact_path(spec)
                    if path.is_file():
                        size = path.stat().st_size
                        if size > 32 * 1024 * 1024:
                            raise Problem(413, 'Artifact exceeds inspection size limit')
                        sha = digest(path.read_bytes())
                        state = ('verified' if sha == spec['expectedSha256'] else 'changed') if spec.get('expectedSha256') else 'observed'
                        record.update(state=state, sha256=sha, bytes=size)
                        if spec['kind'] != 'identity':
                            record['href'] = '/artifact/' + spec['id']
                except (OSError, Problem) as error:
                    record.update(state='unbound' if self.bindings[spec['member']] is None else 'unavailable', detail=str(error))
                artifacts.append(record)
            snapshot = {'schemaVersion': 1, 'implementationId':self.build_id, 'observedAt': now(), 'members': members, 'artifacts': artifacts,
                        'services': [self.inspect_service(s, artifacts) for s in self.catalog['services']],
                        'catalogSha256': digest((self.root / 'workspace/catalog.json').read_bytes()),
                        'scope': 'Local source/service inspection. Remote freshness, current LFS ownership and runtime acceptance are not inferred.'}
            snapshot['id'] = 'snapshot_' + digest(encoded(snapshot))[:16]
            folder = self.local / 'snapshots'
            folder.mkdir(exist_ok=True)
            (folder / (snapshot['id'] + '.json')).write_bytes(encoded(snapshot))
            self.snapshot = snapshot
            return snapshot

    def work_items(self, conn=None):
        if conn is None:
            with closing(self.connection()) as connection:
                return self.work_items(connection)
        rows = {x['id']: dict(x) for x in conn.execute('SELECT * FROM work')}
        result = []
        for seed in self.seeds:
            item = dict(seed, **rows[seed['id']])
            item['evidence'] = json.loads(item['evidence'])
            item['blockedBy'] = [d for d in seed['dependsOn'] if rows[d]['status'] != 'done']
            result.append(item)
        return result

    def events(self):
        with closing(self.connection()) as conn:
            return [dict(row, payload=json.loads(row['payload'])) for row in conn.execute('SELECT * FROM events ORDER BY sequence DESC')]

    def data(self):
        from .agents import AgentCoordinator
        if self.snapshot is None:
            self.refresh()
        return {'catalog': self.catalog, 'snapshot': self.snapshot, 'work': self.work_items(),
                'events': self.events(), 'agents': AgentCoordinator(self).overview(),
                'authority': 'Local workflow records only; connected sources and review gates remain unchanged.'}

    def update_work(self, key, change):
        if set(change) != {'expectedRevision', 'expectedSnapshot', 'status', 'owner', 'rationale', 'evidence'}:
            raise Problem(400, 'Supply only the declared work update fields')
        if change['expectedSnapshot'] != (self.snapshot or self.refresh())['id']:
            raise Problem(409, 'Source inspection changed. Refresh and review the current evidence before saving.')
        if change['status'] not in STATES or type(change['expectedRevision']) is not int:
            raise Problem(400, 'Invalid status or expected revision')
        for field, maximum in [('owner', 80), ('rationale', 3000)]:
            if not isinstance(change[field], str) or not 1 <= len(change[field].strip()) <= maximum:
                raise Problem(400, f'{field} is required and must fit its length limit')
        evidence = change['evidence']
        if not isinstance(evidence, list) or not all(isinstance(x, str) for x in evidence) or len(set(evidence)) != len(evidence):
            raise Problem(400, 'Evidence must be a unique list of artifact IDs')
        available = {a['id'] for a in (self.snapshot or self.refresh())['artifacts'] if a['state'] in {'observed', 'verified'}}
        if not set(evidence) <= available:
            raise Problem(400, 'Evidence includes a missing, changed or unknown artifact')
        for key_id in evidence:
            record = next(a for a in self.snapshot['artifacts'] if a['id'] == key_id)
            try:
                unchanged = digest(self.artifact_path(record).read_bytes()) == record['sha256']
            except OSError:
                unchanged = False
            if not unchanged:
                raise Problem(409, 'Supporting evidence changed after inspection. Refresh before saving.')
        with closing(self.connection()) as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                item = next((x for x in self.work_items(conn) if x['id'] == key), None)
                if item is None:
                    raise Problem(404, 'Unknown work item')
                if item['revision'] != change['expectedRevision']:
                    raise Problem(409, 'This work item changed. Reload it before saving; your draft was not applied.')
                if change['status'] in {'active', 'review', 'done'} and item['blockedBy']:
                    raise Problem(409, 'Resolve dependencies first: ' + ', '.join(item['blockedBy']))
                downstream = [w['id'] for w in self.work_items(conn) if key in w['dependsOn'] and w['status'] in {'active', 'review', 'done'}]
                if item['status'] == 'done' and change['status'] != 'done' and downstream:
                    raise Problem(409, 'Reopen dependent work first: ' + ', '.join(downstream))
                if change['status'] == 'done' and not evidence:
                    raise Problem(400, 'Completion requires a source evidence record; it does not imply visual acceptance')
                before = {k: item[k] for k in ('status', 'owner', 'rationale', 'evidence', 'revision')}
                conn.execute('UPDATE work SET status=?,owner=?,rationale=?,evidence=?,revision=revision+1,updated_at=? WHERE id=?',
                    (change['status'], change['owner'].strip(), change['rationale'].strip(), json.dumps(evidence), now(), key))
                self.event(conn, 'work-updated', key, {'before': before, 'after': change, 'scope': 'Workflow only; acceptance gates unchanged'})
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return next(x for x in self.work_items() if x['id'] == key)

    def add_observation(self, note):
        expected = {'module', 'author', 'title', 'observation', 'limitations', 'nextEvidence', 'expectedSnapshot'}
        if set(note) != expected or note['module'] not in {x['id'] for x in self.catalog['modules']}:
            raise Problem(400, 'Observation must use the declared fields and a known module')
        if note['expectedSnapshot'] != (self.snapshot or self.refresh())['id']:
            raise Problem(409, 'Source inspection changed. Refresh before recording the observation.')
        for key in expected - {'module', 'expectedSnapshot'}:
            if not isinstance(note[key], str) or not 1 <= len(note[key].strip()) <= (120 if key in {'author', 'title'} else 5000):
                raise Problem(400, f'Provide {key} within its length limit')
        with closing(self.connection()) as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                self.event(conn, 'observation', note['module'], dict(note, snapshotId=(self.snapshot or self.refresh())['id'], acceptance='Not changed'))
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def artifact_bytes(self, key):
        record = next((a for a in (self.snapshot or self.refresh())['artifacts'] if a['id'] == key), None)
        if record is None or record['kind'] == 'identity':
            raise Problem(404, 'Artifact is not published by this workspace')
        if record['state'] not in {'verified', 'observed'}:
            raise Problem(409, 'Source is unavailable or changed; inspect the federation record')
        try:
            raw = self.artifact_path(record).read_bytes()
        except OSError as error:
            raise Problem(409, 'Source disappeared after the inspection; refresh the snapshot') from error
        if digest(raw) != record['sha256']:
            raise Problem(409, 'Source changed after the inspection; refresh before review')
        return record, raw

    def experiment_check(self, output=None):
        protocol_path = self.root / 'workspace/experiments/contact-alternatives-v1/protocol.json'
        protocol = read_json(protocol_path)
        snapshot = self.refresh()
        inputs = [a for a in snapshot['artifacts'] if a['id'] in protocol['baselineArtifacts']]
        if len(inputs) != len(protocol['baselineArtifacts']) or any(a['state'] != 'verified' for a in inputs):
            raise Problem(409, 'Preregistered baseline does not match all pinned inputs')
        receipt = {'schemaVersion': 1, 'experimentId': protocol['experimentId'], 'checkedAt': now(),
                   'protocolSha256': digest(protocol_path.read_bytes()),
                   'inputs': [{k: a[k] for k in ('id', 'path', 'sha256', 'bytes')} for a in inputs],
                   'scriptSha256': digest(Path(__file__).read_bytes()),
                   'result': 'Baseline verified; diagnostic candidate authoring may begin',
                   'candidateAuthored': False, 'anatomicalApproval': False, 'productionChanged': False}
        folder = Path(output or self.root / 'evidence/federated-workspace-v1/experiments')
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / ('contact-baseline_' + digest(encoded(receipt))[:16] + '.json')
        path.write_bytes(encoded(receipt))
        (folder / 'current.json').write_bytes(encoded(dict(receipt, receiptFile=path.name, receiptSha256=digest(path.read_bytes()))))
        return path, receipt
