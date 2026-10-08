"""Restricted local UI/API. Member source access is read-only and catalogued."""
from __future__ import annotations

import json
import secrets
import socket
import threading
import webbrowser
from http.client import HTTPConnection, HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from .core import Problem, Workspace, encoded
from .agents import AgentCoordinator


class Server(ThreadingHTTPServer):
    allow_reuse_address = False
    allow_reuse_port = False
    daemon_threads = True

    def server_bind(self):
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def handler_for(workspace, token):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'HorrorWorkspace/1'
        sys_version = ''

        def send_headers(self, status, mime, length):
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(length))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
            self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
            self.end_headers()

        def send(self, status, data, mime='application/json; charset=utf-8', head=False):
            raw = data if isinstance(data, bytes) else encoded(data)
            self.send_headers(status, mime, len(raw))
            if not head:
                self.wfile.write(raw)

        def host_ok(self):
            port = self.server.server_port
            return self.headers.get('Host') in {f'127.0.0.1:{port}', f'localhost:{port}'}

        def do_HEAD(self):
            self.handle_read(True)

        def do_GET(self):
            self.handle_read(False)

        def handle_read(self, head):
            try:
                if not self.host_ok():
                    raise Problem(403, 'Local host required')
                path = urlsplit(self.path).path
                if path == '/api/health':
                    return self.send(200, {'app':'horror-workspace', 'version':1, 'root':str(workspace.root), 'buildId':workspace.build_id}, head=head)
                if path == '/api/workspace':
                    return self.send(200, dict(workspace.data(), writeToken=token), head=head)
                if path == '/api/export':
                    return self.send(200, dict(workspace.data(), exportScope='Local workflow and source inspection; no acceptance promotion'), head=head)
                if path == '/api/agent/queue':
                    return self.send(200, AgentCoordinator(workspace).queue(), head=head)
                if path.startswith('/api/agent/packets/'):
                    return self.send(200, AgentCoordinator(workspace).load_packet(path[len('/api/agent/packets/'):]), head=head)
                if path.startswith('/api/agent/prompt/'):
                    agent = AgentCoordinator(workspace)
                    packet = agent.load_packet(path[len('/api/agent/prompt/'):])
                    return self.send(200, agent.markdown(packet).encode('utf-8'), 'text/plain; charset=utf-8', head)
                if path.startswith('/api/agent/template/'):
                    agent = AgentCoordinator(workspace)
                    return self.send(200, agent.result_template(agent.load_packet(path[len('/api/agent/template/'):])), head=head)
                if path in {'/', '/index.html', '/styles.css', '/app.js', '/favicon.svg'}:
                    name = 'index.html' if path in {'/', '/index.html'} else path[1:]
                    mime = {'index.html':'text/html', 'styles.css':'text/css', 'app.js':'text/javascript','favicon.svg':'image/svg+xml'}[name]
                    return self.send(200, (workspace.root/'tools/federated_workspace/web'/name).read_bytes(), mime+'; charset=utf-8', head)
                if path.startswith('/artifact/'):
                    key = path[len('/artifact/'):]
                    record, raw = workspace.artifact_bytes(key)
                    suffix = record['path'].rsplit('.',1)[-1].lower()
                    mime = {'png':'image/png', 'jpg':'image/jpeg', 'jpeg':'image/jpeg', 'json':'application/json; charset=utf-8'}.get(suffix, 'text/plain; charset=utf-8')
                    return self.send(200, raw, mime, head)
                raise Problem(404, 'Route not published')
            except Problem as error:
                self.send(error.status, {'error': str(error)}, head=head)

        def do_POST(self):
            try:
                port = self.server.server_port
                if not self.host_ok() or self.headers.get('Origin') not in {f'http://127.0.0.1:{port}', f'http://localhost:{port}'}:
                    raise Problem(403, 'Same-origin local writes only')
                if not secrets.compare_digest(self.headers.get('X-Workspace-Token',''), token):
                    raise Problem(403, 'Workspace write token required')
                if self.headers.get('Content-Type') != 'application/json':
                    raise Problem(415, 'Use application/json')
                try:
                    size = int(self.headers.get('Content-Length', '0'))
                except ValueError:
                    raise Problem(400, 'Invalid content length')
                if not 0 < size <= 32768:
                    raise Problem(413, 'Request size outside limit')
                try:
                    body = json.loads(self.rfile.read(size))
                except (ValueError, UnicodeDecodeError):
                    raise Problem(400, 'Malformed JSON')
                if not isinstance(body, dict):
                    raise Problem(400, 'Request must be an object')
                path = urlsplit(self.path).path
                if path == '/api/refresh':
                    if body:
                        raise Problem(400, 'Refresh accepts no parameters')
                    workspace.refresh()
                    return self.send(200, workspace.data())
                if path == '/api/observations':
                    workspace.add_observation(body)
                    return self.send(201, workspace.data())
                if path == '/api/agent/packet':
                    if set(body) != {'taskId', 'budgetCharacters'} or not isinstance(body['taskId'], str):
                        raise Problem(400, 'Packet preparation requires taskId and budgetCharacters only')
                    return self.send(201, AgentCoordinator(workspace).packet(body['taskId'], body['budgetCharacters']))
                if path == '/api/agent/start':
                    if set(body) != {'packetId', 'owner'}:
                        raise Problem(400, 'Reservation requires packetId and owner only')
                    return self.send(201, AgentCoordinator(workspace).start(body['packetId'], body['owner']))
                if path == '/api/agent/release':
                    if set(body) != {'runId', 'reason'}:
                        raise Problem(400, 'Release requires runId and reason only')
                    return self.send(200, AgentCoordinator(workspace).release(body['runId'], body['reason']))
                if path == '/api/agent/finish':
                    if set(body) != {'runId', 'result'}:
                        raise Problem(400, 'Handoff requires runId and result only')
                    return self.send(200, AgentCoordinator(workspace).finish(body['runId'], body['result']))
                if path.startswith('/api/work/'):
                    return self.send(200, workspace.update_work(path[len('/api/work/'):], body))
                raise Problem(404, 'Write route not published')
            except Problem as error:
                self.send(error.status, {'error':str(error)})

        def log_message(self, fmt, *args):
            if len(args) > 1 and str(args[1]) not in {'200','201'}:
                super().log_message(fmt, *args)

    return Handler


def serve(workspace, port=8489, open_browser=False):
    if not 1024 <= port <= 65535:
        raise ValueError('Use an unprivileged local port')
    workspace.refresh()
    url = f'http://127.0.0.1:{port}/'
    try:
        server = Server(('127.0.0.1',port), handler_for(workspace, secrets.token_urlsafe(32)))
    except OSError as error:
        conn = HTTPConnection('127.0.0.1',port,timeout=3)
        try:
            conn.request('GET','/api/health')
            response = conn.getresponse()
            data = json.loads(response.read(8192))
            same = response.status == 200 and data == {'app':'horror-workspace','version':1,'root':str(workspace.root),'buildId':workspace.build_id}
        except (OSError, ValueError, HTTPException):
            same = False
        finally:
            conn.close()
        if not same:
            raise SystemExit(f'Port {port} is occupied by another service or workspace revision. Stop that preview before reopening, or select --port. No process changed.') from error
        print(json.dumps({'url':url,'reusedWorkspace':True}),flush=True)
        if open_browser:
            webbrowser.open(url)
        return
    print(json.dumps({'url':url,'localState':str(workspace.db),'memberWrites':False}),flush=True)
    if open_browser:
        threading.Timer(.3,lambda:webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
