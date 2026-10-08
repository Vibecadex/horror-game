import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch

from tools.federated_workspace.core import ROOT, Workspace, Problem, digest
from tools.federated_workspace.server import Server, handler_for


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='horror-workspace-test-')
        self.addCleanup(self.temp.cleanup)
        self.bindings = {'schemaVersion':1,'members':{'game':'.','chamber':None,'scanner':None,'reference':None}}
        self.workspace = Workspace(local=Path(self.temp.name),bindings=self.bindings)
        with patch.object(self.workspace,'git_inspect',return_value={'state':'test-fixture'}), patch.object(self.workspace,'inspect_service',side_effect=lambda s,a:dict(s,state='unavailable')):
            self.workspace.refresh()

    def change(self, **kw):
        return dict({'expectedRevision':0,'expectedSnapshot':self.workspace.snapshot['id'],'status':'active','owner':'Interface QA','rationale':'Synthetic isolated test record.','evidence':['workspace-guide']},**kw)

    def test_catalog_and_frozen_sources(self):
        self.assertEqual(len(self.workspace.catalog['modules']),8)
        for key in ['source-bear','anatomy-map','decision-manifest','report-manifest']:
            item=next(x for x in self.workspace.snapshot['artifacts'] if x['id']==key)
            self.assertEqual(item['state'],'verified',key)

    def test_missing_member_is_explicit(self):
        source=next(x for x in self.workspace.snapshot['artifacts'] if x['id']=='chamber-qa')
        self.assertEqual(source['state'],'unbound')
        with self.assertRaises(Problem):self.workspace.artifact_bytes('chamber-qa')

    def test_persistent_restart_and_no_seed_overwrite(self):
        result=self.workspace.update_work('WS-001',self.change(owner='Saved owner'))
        restarted=Workspace(local=Path(self.temp.name),bindings=self.bindings)
        item=next(x for x in restarted.work_items() if x['id']=='WS-001')
        self.assertEqual(item['owner'],'Saved owner')
        self.assertEqual(item['revision'],1)
        self.assertEqual(len(restarted.events()),len(restarted.seeds)+1)

    def test_stale_write_is_atomic(self):
        self.workspace.update_work('WS-001',self.change())
        before=self.workspace.events()
        with self.assertRaises(Problem) as caught:self.workspace.update_work('WS-001',self.change(owner='Stale client'))
        self.assertEqual(caught.exception.status,409)
        self.assertEqual(before,self.workspace.events())

    def test_stale_source_snapshot_and_downstream_reopen_rejected(self):
        with self.assertRaises(Problem):self.workspace.update_work('WS-001',self.change(expectedSnapshot='snapshot_old'))
        self.workspace.update_work('WS-001',self.change(status='done'))
        self.workspace.update_work('GAME-001',self.change())
        with self.assertRaises(Problem):self.workspace.update_work('WS-001',self.change(status='active',expectedRevision=1))

    def test_dependencies_and_completion_evidence(self):
        with self.assertRaises(Problem):self.workspace.update_work('GAME-001',self.change())
        with self.assertRaises(Problem):self.workspace.update_work('WS-001',self.change(status='done',evidence=[]))
        self.workspace.update_work('WS-001',self.change(status='done'))
        self.assertEqual(self.workspace.update_work('GAME-001',self.change())['status'],'active')

    def test_no_gate_or_file_mutation(self):
        before=digest((ROOT/'workspace/catalog.json').read_bytes())
        with self.assertRaises(Problem):self.workspace.update_work('WS-001',dict(self.change(),anatomicalApproval=True))
        self.workspace.update_work('WS-001',self.change(status='done'))
        self.assertEqual(before,digest((ROOT/'workspace/catalog.json').read_bytes()))
        self.assertEqual(self.workspace.catalog['gates'][2]['status'],'Unresolved')

    def test_changed_evidence_rejected_at_save_and_serve(self):
        spec=next(x for x in self.workspace.snapshot['artifacts'] if x['id']=='workspace-guide')
        spec['sha256']='0'*64
        with self.assertRaises(Problem) as caught:self.workspace.update_work('WS-001',self.change())
        self.assertEqual(caught.exception.status,409)
        with self.assertRaises(Problem):self.workspace.artifact_bytes('workspace-guide')

    def test_artifact_access_is_exact(self):
        for name in ['../AGENTS.md','source-bear','anatomy-map','workspace.sqlite3','tools/workspace.py']:
            with self.assertRaises(Problem):self.workspace.artifact_bytes(name)

    def test_observation_is_attributed_and_preserved(self):
        note={'module':'workspace','author':'QA fixture','title':'Synthetic observation','observation':'<script>literal test</script>', 'limitations':'Interface only','nextEvidence':'Compare the exported record','expectedSnapshot':self.workspace.snapshot['id']}
        self.workspace.add_observation(note)
        event=self.workspace.events()[0]
        self.assertEqual(event['payload']['observation'],note['observation'])
        self.assertEqual(event['payload']['snapshotId'],self.workspace.snapshot['id'])
        self.assertEqual(event['payload']['acceptance'],'Not changed')

    def test_experiment_freezes_inputs_without_claiming_candidate(self):
        with patch.object(self.workspace,'refresh',return_value=self.workspace.snapshot):
            path,receipt=self.workspace.experiment_check(Path(self.temp.name)/'experiment')
        self.assertTrue(path.is_file())
        self.assertFalse(receipt['candidateAuthored'])
        self.assertFalse(receipt['anatomicalApproval'])
        self.assertEqual(len(receipt['inputs']),3)

    def test_boundaries_and_exclusive_http(self):
        server=Server(('127.0.0.1',0),handler_for(self.workspace,'test-token'))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        port=server.server_port
        try:
            with self.assertRaises(OSError):Server(('127.0.0.1',port),handler_for(self.workspace,'another-token'))
            def request(method,path,body=None,headers=None):
                conn=HTTPConnection('127.0.0.1',port,timeout=3)
                conn.request(method,path,body=json.dumps(body) if body is not None else None,headers=headers or {})
                response=conn.getresponse();raw=response.read();status=response.status;conn.close()
                return status,raw
            self.assertEqual(request('GET','/')[0],200)
            for path in ['/AGENTS.md','/../AGENTS.md','/%2e%2e/AGENTS.md','/artifact/../AGENTS.md','/workspace/local/workspace.sqlite3']:
                self.assertEqual(request('GET',path)[0],404,path)
            self.assertEqual(request('GET','/api/workspace',headers={'Host':'external.example'})[0],403)
            self.assertEqual(request('POST','/api/work/WS-001',self.change())[0],403)
            headers={'Origin':f'http://127.0.0.1:{port}','Content-Type':'application/json','X-Workspace-Token':'test-token'}
            self.assertEqual(request('POST','/api/work/WS-001',self.change(),headers)[0],200)
            self.assertEqual(request('POST','/api/work/WS-001',self.change(),headers)[0],409)
            self.assertEqual(request('POST','/api/execute',{'command':'anything'},headers)[0],404)
            self.assertEqual(request('POST','/api/refresh',{'path':'C:/'},headers)[0],400)
            status,raw=request('GET','/api/export')
            self.assertEqual(status,200);self.assertNotIn('writeToken',json.loads(raw))
        finally:
            server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
