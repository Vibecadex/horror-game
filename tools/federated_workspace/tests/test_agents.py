import concurrent.futures
import json
import shutil
import tempfile
import threading
import unittest
from contextlib import closing
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch

from tools.federated_workspace.agents import AgentCoordinator
from tools.federated_workspace.core import ROOT, Workspace, Problem, digest, encoded, read_json
from tools.federated_workspace.server import Server, handler_for


class AgentWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='horror-agent-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in ('AGENTS.md','workspace/AGENT_WORKFLOW.md','workspace/AGENT_RULES.md','workspace/README.md',
                     'workspace/decisions/ADR-001-local-federation.md','workspace/agent-contracts.json',
                     'workspace/catalog.json','workspace/work-items.json','tools/workspace.py'):
            target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
        # Isolated fixture keeps the real workspace contracts with no game asset copies.
        self.bindings={'schemaVersion':1,'members':{'game':'.','chamber':None,'scanner':None,'reference':None}}
        self.w=Workspace(root=self.root,bindings=self.bindings)
        self.agent=AgentCoordinator(self.w)
        self.patches=[patch.object(self.w,'git_inspect',return_value={'state':'observed','head':'fixture-head','branch':'fixture'}),
                      patch.object(self.w,'inspect_service',side_effect=lambda s,a:dict(s,state='unavailable'))]
        for p in self.patches:p.start();self.addCleanup(p.stop)
        self.w.refresh()

    def packet(self):
        return self.agent.packet('WS-001')

    def begin(self):
        p=self.packet();return p,self.agent.start(p['id'],'Fixture agent')

    def result(self,packet,disposition='review'):
        p=self.root/'evidence/workspace-agent-v1/check.txt';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture check evidence',encoding='utf-8')
        result=self.agent.result_template(packet)
        result.update(disposition=disposition,summary='Scoped fixture output',outputs=[{'id':'proof','path':p.relative_to(self.root).as_posix(),'sha256':digest(p.read_bytes())}],
                      checks=[{'name':'Fixture check','status':'passed','command':'fixture-only','result':'Synthetic pass','evidence':['proof']}])
        result['gates']['validation']='passed'
        return result

    def test_packet_budget_full_instructions_and_source_identity(self):
        p=self.packet()
        self.assertLessEqual(len(self.agent.markdown(p)),24000)
        self.assertEqual(p['contextCharacters'],len(self.agent.markdown(p)))
        for source in p['sources']:
            self.assertEqual(source['sha256'],digest((self.root/source['path']).read_bytes()))
            if source['requiredInstruction']:
                self.assertEqual(source['content'],(self.root/source['path']).read_bytes().decode('utf-8-sig'))
        self.assertTrue(any(s['inclusion'].startswith('excerpt') or s['inclusion']=='reference only' for s in p['sources']))
        self.assertEqual(p,self.agent.load_packet(p['id']))
        self.assertEqual(len(self.agent.runs()),0)
        self.assertNotIn('writeToken',json.dumps(p))

    def test_mandatory_overflow_fails_instead_of_truncation(self):
        (self.root/'AGENTS.md').write_text('x'*70000)
        with self.assertRaises(Problem) as err:self.packet()
        self.assertEqual(err.exception.status,413)
        self.assertEqual(list(self.agent.folder.glob('*.json')),[])

    def test_tampered_packet_and_unknown_identifiers_rejected(self):
        p=self.packet();path=self.agent.folder/(p['id']+'.json');raw=json.loads(path.read_text());raw['task']['title']='Changed';path.write_bytes(encoded(raw))
        for name in (p['id'],'../../AGENTS.md','packet_wrong'):
            with self.assertRaises(Problem):self.agent.load_packet(name)
        with self.assertRaises(Problem):self.agent.packet('MISSING')

    def test_start_rejects_source_and_work_plan_drift(self):
        p=self.packet();(self.root/'workspace/README.md').write_text('changed')
        with self.assertRaises(Problem):self.agent.start(p['id'],'Test')
        p=self.packet();path=self.root/'workspace/work-items.json';path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaises(Problem):self.agent.start(p['id'],'Test')
        self.assertEqual(len(self.agent.runs()),0)

    def test_duplicate_start_is_atomic_across_two_agents(self):
        p=self.packet()
        def attempt(owner):
            try:return self.agent.start(p['id'],owner)['state']
            except Problem:return 'rejected'
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            result=list(pool.map(attempt,['Agent A','Agent B']))
        self.assertEqual(sorted(result),['active','rejected'])
        self.assertEqual(len(self.agent.runs()),1)

    def test_overlap_and_dependency_blocked(self):
        p,r=self.begin()
        q=self.agent.queue()
        self.assertFalse(next(t for t in q['tasks'] if t['id']=='WS-004')['eligible'])
        self.assertTrue(any('Reserved by' in s for s in next(t for t in q['tasks'] if t['id']=='WS-004')['reasons']))
        with self.assertRaises(Problem):self.agent.start(p['id'],'Other')
        c=self.agent.contract(next(t for t in self.w.work_items() if t['id']=='GAME-004'))
        self.assertIn('hold',c)

    def test_resume_and_release_persist_without_erasing_newer_work(self):
        p,r=self.begin();run_id=r['runId']
        self.assertEqual(AgentCoordinator(self.w).check(run_id)['sourceCheck'],'passed')
        with closing(self.w.connection()) as conn:
            conn.execute("UPDATE work SET owner='Human intervention',revision=revision+1 WHERE id='WS-001'")
        with self.assertRaises(Problem):self.agent.check(run_id)
        self.agent.release(run_id,'Respect newer work')
        task=next(t for t in self.w.work_items() if t['id']=='WS-001')
        self.assertEqual(task['owner'],'Human intervention')
        self.assertEqual(AgentCoordinator(self.w).run(run_id)['state'],'released')

    def test_immutable_drift_blocks_resume_and_handoff(self):
        p,r=self.begin();result=self.result(p);(self.root/'AGENTS.md').write_text('changed')
        with self.assertRaises(Problem):self.agent.check(r['runId'])
        with self.assertRaises(Problem):self.agent.finish(r['runId'],result)
        self.assertEqual(self.agent.run(r['runId'])['state'],'active')

    def test_editable_context_changes_must_be_declared(self):
        p,r=self.begin();path=self.root/'workspace/README.md';path.write_text('intentional scoped change')
        self.assertIn('workspace/README.md',self.agent.check(r['runId'])['editableContextChanges'])
        result=self.result(p)
        with self.assertRaises(Problem):self.agent.finish(r['runId'],result)
        result['outputs'].append({'id':'guide','path':'workspace/README.md','sha256':digest(path.read_bytes())})
        self.assertEqual(self.agent.finish(r['runId'],result)['state'],'review')

    def test_handoff_verifies_hashes_and_separate_gates_is_idempotent(self):
        p,r=self.begin();result=self.result(p);catalog=(self.root/'workspace/catalog.json').read_bytes()
        invalid=json.loads(json.dumps(result));invalid['gates']['anatomy']='approved'
        with self.assertRaises(Problem):self.agent.finish(r['runId'],invalid)
        invalid=json.loads(json.dumps(result));invalid['outputs'][0]['sha256']='0'*64
        with self.assertRaises(Problem):self.agent.finish(r['runId'],invalid)
        done=self.agent.finish(r['runId'],result)
        events=len(self.w.events())
        self.assertEqual(done['state'],'review')
        self.assertTrue(self.agent.finish(r['runId'],result)['idempotent'])
        self.assertEqual(len(self.w.events()),events)
        self.assertEqual((self.root/'workspace/catalog.json').read_bytes(),catalog)
        self.assertEqual(next(t for t in self.w.work_items() if t['id']=='WS-001')['status'],'review')

    def test_output_boundaries_and_unsupported_proven_claims(self):
        p,r=self.begin();result=self.result(p)
        for path in ('../outside.txt','workspace/local/private.json','TeddyBlueprint/Content/x.uasset','tools/federated_workspace/../../private.txt','C:/private.txt'):
            value=json.loads(json.dumps(result));value['outputs'][0]['path']=path
            with self.assertRaises(Problem,msg=path):self.agent.finish(r['runId'],value)
        value=json.loads(json.dumps(result));value['checks'][0]['evidence']=[]
        with self.assertRaises(Problem):self.agent.finish(r['runId'],value)
        value=json.loads(json.dumps(result));value['checks'][0]['status']='not-run'
        with self.assertRaises(Problem):self.agent.finish(r['runId'],value)

    def test_blocked_result_is_honest_without_output_or_approval(self):
        p,r=self.begin();result=self.agent.result_template(p)
        value=self.agent.finish(r['runId'],result)
        self.assertEqual(value['state'],'blocked')
        self.assertEqual(value['receipt']['result']['outputs'],[])
        self.assertEqual(value['receipt']['result']['gates']['validation'],'not-run')

    def test_distinct_overlapping_tasks_cannot_start_together(self):
        with closing(self.w.connection()) as conn:
            conn.execute("UPDATE work SET status='done' WHERE id='WS-001'")
        first=self.agent.packet('WS-004');second=self.agent.packet('WS-003')
        self.agent.start(first['id'],'First workspace writer')
        with self.assertRaises(Problem) as err:self.agent.start(second['id'],'Second workspace writer')
        self.assertIn('Overlapping reservation',str(err.exception))
        self.assertEqual(len(self.agent.runs()),1)

    def test_git_drift_and_explicit_holds_are_enforced(self):
        p=self.packet()
        with patch.object(self.w,'git_inspect',return_value={'head':'new-head','branch':'fixture'}):
            with self.assertRaises(Problem):self.agent.start(p['id'],'Stale Git writer')
        spec=read_json(self.root/'workspace/agent-contracts.json')
        spec['taskOverrides']['WS-001']={'hold':'Fixture requires review'}
        (self.root/'workspace/agent-contracts.json').write_bytes(encoded(spec))
        self.agent=AgentCoordinator(self.w);p=self.packet()
        with self.assertRaises(Problem) as err:self.agent.start(p['id'],'Held writer')
        self.assertEqual(str(err.exception),'Fixture requires review')

    def test_agent_http_contract_and_content_are_scoped(self):
        server=Server(('127.0.0.1',0),handler_for(self.w,'fixture-token'))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();port=server.server_port
        def call(method,path,body=None,authenticated=True):
            conn=HTTPConnection('127.0.0.1',port,timeout=10)
            headers={'Content-Type':'application/json','Origin':f'http://127.0.0.1:{port}','X-Workspace-Token':'fixture-token'} if authenticated else {}
            conn.request(method,path,body=json.dumps(body) if body is not None else None,headers=headers)
            response=conn.getresponse();status=response.status;raw=response.read();conn.close();return status,raw
        try:
            self.assertEqual(call('POST','/api/agent/packet',{'taskId':'WS-001','budgetCharacters':24000},False)[0],403)
            self.assertEqual(call('POST','/api/agent/packet',{'taskId':'WS-001','budgetCharacters':24000,'command':'execute'})[0],400)
            status,raw=call('POST','/api/agent/packet',{'taskId':'WS-001','budgetCharacters':24000});p=json.loads(raw)
            self.assertEqual(status,201)
            status,raw=call('GET','/api/agent/prompt/'+p['id']);self.assertEqual(status,200)
            self.assertEqual(raw.decode(),self.agent.markdown(p))
            self.assertEqual(call('GET','/api/agent/packets/../../AGENTS.md')[0],400)
            status,raw=call('POST','/api/agent/start',{'packetId':p['id'],'owner':'API fixture'});run=json.loads(raw)
            self.assertEqual(status,201)
            self.assertEqual(call('POST','/api/agent/finish',{'runId':run['runId'],'result':self.agent.result_template(p)})[0],200)
            self.assertEqual(call('POST','/api/execute',{'command':'no'})[0],404)
        finally:
            server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
