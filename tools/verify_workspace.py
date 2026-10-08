"""Save a bounded workspace verification receipt; does not launch Unreal or write members."""
import json
import argparse
import re
import subprocess
import sys
import unittest
from pathlib import Path

from federated_workspace.core import ROOT, Workspace, digest, encoded, now


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='evidence/federated-workspace-v1')
    args=parser.parse_args()
    folder=(ROOT/args.output).resolve()
    if not folder.is_relative_to(ROOT/'evidence'):
        raise SystemExit('Verification output must stay under this checkout evidence directory')
    folder.mkdir(parents=True,exist_ok=True)
    qa=folder/'qa'
    qa.mkdir(exist_ok=True)
    tests=subprocess.run([sys.executable,'-m','unittest','discover','-s','tools/federated_workspace/tests','-v'],cwd=ROOT,capture_output=True,text=True)
    (qa/'backend-tests.txt').write_text(tests.stdout+tests.stderr,encoding='utf-8')
    if tests.returncode:
        raise SystemExit(tests.stdout+tests.stderr)
    syntax=subprocess.run(['node','--check','tools/federated_workspace/web/app.js'],cwd=ROOT,capture_output=True,text=True)
    if syntax.returncode:
        raise SystemExit(syntax.stderr)
    workspace=Workspace()
    snapshot=workspace.refresh()
    pinned=[a for a in snapshot['artifacts'] if a.get('expectedSha256')]
    if not all(a['state']=='verified' for a in pinned):
        raise SystemExit('A pinned source identity failed. No verification pass recorded.')
    browser_path=qa/'browser-checks.json'
    browser=json.loads(browser_path.read_text(encoding='utf-8')) if browser_path.exists() else None
    if browser and browser.get('implementationId') and browser['implementationId'] != workspace.build_id:
        raise SystemExit('Browser receipt belongs to another implementation; rerun the relevant UI checks')
    if browser and any(not check.get('passed',False) for check in browser.get('checks',[])):
        raise SystemExit('Browser receipt contains a failing check; no verification pass recorded')
    files=[p for p in (ROOT/'tools/federated_workspace').rglob('*') if p.is_file() and p.suffix in {'.py','.js','.css','.html','.svg'}]
    files += [ROOT/'tools/workspace.py',Path(__file__),ROOT/'WORKSPACE.cmd',ROOT/'workspace/catalog.json',ROOT/'workspace/work-items.json',
              ROOT/'workspace/agent-contracts.json',ROOT/'workspace/AGENT_RULES.md',ROOT/'workspace/AGENT_WORKFLOW.md',ROOT/'workspace/schemas/agent-result.schema.json']
    sources=[{k:a[k] for k in ('id','member','path','state','sha256') if k in a} for a in snapshot['artifacts'] if a['module']!='workspace' and a['id']!='contact-baseline-receipt']
    receipt={'schemaVersion':1,'verifiedAt':now(),'implementationId':workspace.build_id,
             'backend':{'passed':True,'tests':int(re.search(r'Ran (\d+) tests?',tests.stderr).group(1)),'logSha256':digest((qa/'backend-tests.txt').read_bytes())},
             'javascriptSyntax':'passed','pinnedSourceIdentities':len(pinned),'sources':sources,
             'members':snapshot['members'],'services':snapshot['services'],
             'implementationHashes':{p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(files)},
             'browserReceiptSha256':digest(browser_path.read_bytes()) if browser else None,
             'browserMatchesImplementation':bool(browser and browser.get('implementationId')==workspace.build_id),
             'browserChecks':browser,
             'scope':'Local workspace/agent contracts and tested controls only. Agent-reported check outcomes are not independently rerun by handoff ingestion. No model-performance benchmark, hosted deployment, anatomy approval, current native gameplay pass or user acceptance claimed.',
             'productionAssetWrites':False,'dependencyInstallation':False}
    raw=encoded(receipt)
    versions=folder/'receipts';versions.mkdir(exist_ok=True)
    immutable=versions/('verification_'+digest(raw)[:16]+'.json')
    immutable.write_bytes(raw)
    (folder/'verification.json').write_bytes(raw)
    print(json.dumps({'receipt':str(immutable),'implementationId':workspace.build_id,'backendTests':receipt['backend']['tests'],
                      'pinnedIdentities':len(pinned),'browserReceipt':bool(browser)},indent=2))


if __name__=='__main__':main()
