"""Human entry point for the local Horror Game federation. No installs or member writes."""
import argparse
import json
from pathlib import Path

from federated_workspace.core import Workspace, Problem, encoded, read_json
from federated_workspace.agents import AgentCoordinator
from federated_workspace.server import serve


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['serve','check','export','experiment-check','agent'])
    parser.add_argument('action', nargs='?', choices=['next','packet','start','check','status','release','finish'])
    parser.add_argument('identifier', nargs='?')
    parser.add_argument('--track', choices=['game','workspace'])
    parser.add_argument('--format', choices=['summary','json','markdown'], default='summary')
    parser.add_argument('--budget-chars', type=int, default=24000)
    parser.add_argument('--owner')
    parser.add_argument('--reason')
    parser.add_argument('--result-file', type=Path)
    parser.add_argument('--port',type=int,default=8489)
    parser.add_argument('--open',action='store_true')
    args = parser.parse_args()
    workspace = Workspace()
    if args.command == 'agent':
        agent = AgentCoordinator(workspace)
        if args.action in {'packet','start','check','release','finish'} and not args.identifier:
            parser.error('This agent action requires a task, packet or run identifier')
        if args.action == 'next':
            result = agent.queue(args.track)
        elif args.action == 'status':
            result = agent.overview()
        elif args.action == 'packet':
            result = agent.packet(args.identifier,args.budget_chars)
            if args.format == 'markdown':
                print(agent.markdown(result))
                return
            if args.format == 'summary':
                result = {'packetId':result['id'], 'taskId':args.identifier,
                          'markdownPath':str(agent.folder/(result['id']+'.md')),
                          'jsonPath':str(agent.folder/(result['id']+'.json')),
                          'resultTemplatePath':str(agent.folder/(result['id']+'.result-template.json')),
                          'contextCharacters':result['contextCharacters'], 'budgetCharacters':args.budget_chars,
                          'eligibleAtPreparation':result['eligibleAtPreparation'], 'blockingReasons':result['blockingReasons']}
        elif args.action == 'start':
            result = agent.start(args.identifier,args.owner)
        elif args.action == 'check':
            result = agent.check(args.identifier)
        elif args.action == 'release':
            result = agent.release(args.identifier,args.reason)
        elif args.action == 'finish':
            if not args.result_file or not args.result_file.is_file() or args.result_file.stat().st_size > 32768:
                parser.error('--result-file must name an existing JSON file of at most 32768 bytes')
            result = agent.finish(args.identifier,read_json(args.result_file))
        else:
            parser.error('Choose an agent action: next, packet, start, check, status, release, finish')
        print(json.dumps(result,indent=2,ensure_ascii=True))
    elif args.command == 'serve':
        serve(workspace,args.port,args.open)
    elif args.command == 'check':
        snapshot = workspace.refresh()
        summary = {'snapshotId':snapshot['id'],'modules':len(workspace.catalog['modules']),
                   'members':snapshot['members'], 'artifacts':[{'id':a['id'],'state':a['state']} for a in snapshot['artifacts']],
                   'services':snapshot['services'], 'writes':'Workspace local snapshot only'}
        print(json.dumps(summary,indent=2))
        if any(a.get('expectedSha256') and a['state'] != 'verified' for a in snapshot['artifacts']):
            raise SystemExit(1)
    elif args.command == 'experiment-check':
        path, receipt = workspace.experiment_check()
        print(json.dumps({'receipt':str(path),'result':receipt},indent=2))
    else:
        data = workspace.data()
        folder = workspace.local/'exports'
        folder.mkdir(exist_ok=True)
        path = folder/(data['snapshot']['id']+'.json')
        path.write_bytes(encoded(data))
        print(str(path))


if __name__ == '__main__':
    try:
        main()
    except (Problem, ValueError, OSError) as error:
        print(json.dumps({'error':str(error),'status':getattr(error,'status',400)}))
        raise SystemExit(1)
