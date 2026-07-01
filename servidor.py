#!/usr/bin/env python3
import json
import http.server
import socketserver
import httpx
import os
import threading
import subprocess

_hist_lock = threading.Lock()

# Load .env.local if present (local dev only, never committed)
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.local')
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

PORT = int(os.environ.get('PORT', 3000))
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
API_URL = 'https://api.anthropic.com/v1/messages'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HIST_FILE = os.path.join(BASE_DIR, 'historial.json')
INTELLIGENCE_CONTEXT = os.path.join(BASE_DIR, 'hint_intelligence', 'outputs', 'context_injection.json')
INTELLIGENCE_ALERTS  = os.path.join(BASE_DIR, 'hint_intelligence', 'outputs', 'alerts.json')

client = httpx.Client(timeout=httpx.Timeout(connect=15.0, read=120.0, write=10.0, pool=5.0))

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            try:
                with open(os.path.join(BASE_DIR, 'index.html'), 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except:
                self.send_response(404)
                self.end_headers()
        elif self.path == '/api/historial':
            try:
                with open(HIST_FILE, 'r', encoding='utf-8') as f:
                    data = f.read()
            except FileNotFoundError:
                data = '[]'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data.encode('utf-8'))
        elif self.path.startswith('/api/intelligence'):
            # Sirve context_injection.json y alerts.json al frontend
            # GET /api/intelligence?sector=X&seniority=Y
            # devuelve contexto histórico relevante para ese prospecto
            try:
                ctx = {}
                if os.path.exists(INTELLIGENCE_CONTEXT):
                    with open(INTELLIGENCE_CONTEXT, 'r', encoding='utf-8') as f:
                        ctx = json.load(f)
                alerts_data = {}
                if os.path.exists(INTELLIGENCE_ALERTS):
                    with open(INTELLIGENCE_ALERTS, 'r', encoding='utf-8') as f:
                        alerts_data = json.load(f)
                result = json.dumps({'context': ctx, 'alerts': alerts_data}, ensure_ascii=False)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(result.encode('utf-8'))
            except Exception as e:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'context': {}, 'alerts': {}, 'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        if self.path == '/api/generate':
            data = json.loads(body)
            prompt = data.get('prompt', '')
            system = data.get('system', '')
            try:
                payload = {
                    'model': 'claude-haiku-4-5-20251001',
                    'max_tokens': 4000,
                    'messages': [{'role': 'user', 'content': prompt}]
                }
                if system:
                    payload['system'] = [{'type': 'text', 'text': system, 'cache_control': {'type': 'ephemeral'}}]
                response = client.post(API_URL,
                    json=payload,
                    headers={'x-api-key': API_KEY, 'anthropic-version': '2023-06-01', 'anthropic-beta': 'prompt-caching-2024-07-31'}
                )
                result = response.json()
                text = result['content'][0]['text']
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'text': text}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

        elif self.path == '/api/historial':
            try:
                incoming = json.loads(body)
                with _hist_lock:
                    try:
                        with open(HIST_FILE, 'r', encoding='utf-8') as f:
                            existing = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        existing = []
                    # upsert por id — incoming puede ser array completo o entry única
                    if isinstance(incoming, dict):
                        incoming = [incoming]
                    index = {e['id']: e for e in existing}
                    for entry in incoming:
                        index[entry['id']] = entry
                    merged = sorted(index.values(), key=lambda e: e.get('id', ''), reverse=True)
                    with open(HIST_FILE, 'w', encoding='utf-8') as f:
                        json.dump(merged, f, ensure_ascii=False, indent=2)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

        elif self.path == '/api/save-md':
            try:
                import re
                from datetime import date
                d = json.loads(body)
                name = d.get('name', '').strip()
                empresa = d.get('empresa', '').strip()
                msg1 = d.get('msg1', '').strip()
                profile_raw = d.get('profileRaw', '').strip()

                # Extract cargo and country from profileRaw (best effort)
                cargo = ''
                pais = ''
                for line in profile_raw.split('\n'):
                    line = line.strip()
                    if not cargo and re.match(r'^(Director|Gerente|Manager|Head|Chief|VP|Founder|CEO|CMO|CFO|CTO|CIO|CISO|CDO|Jefe|Lead|Líder|Especialista|Analista|Coordinador|Responsable)', line, re.I):
                        cargo = line[:120]
                    if not pais and re.search(r'(Argentina|Colombia|Chile|México|Panamá|Costa Rica|Perú|Uruguay|España|Brasil|Venezuela|Ecuador|Bolivia|Paraguay|Guatemala|Honduras|El Salvador|Nicaragua|Rep\. Dominicana|Puerto Rico)', line, re.I):
                        m = re.search(r'(Argentina|Colombia|Chile|México|Panamá|Costa Rica|Perú|Uruguay|España|Brasil|Venezuela|Ecuador|Bolivia|Paraguay|Guatemala|Honduras|El Salvador|Nicaragua|Rep\. Dominicana|Puerto Rico)', line, re.I)
                        if m:
                            pais = m.group(1)

                # Build slug for filename
                slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
                if not slug:
                    slug = 'contacto-' + str(int(__import__('time').time()))

                # Determine current month folder
                month = date.today().strftime('%B').lower()  # julio, agosto, etc.
                month_map = {'january':'enero','february':'febrero','march':'marzo','april':'abril',
                             'may':'mayo','june':'junio','july':'julio','august':'agosto',
                             'september':'septiembre','october':'octubre','november':'noviembre','december':'diciembre'}
                month_es = month_map.get(month, month)
                folder = os.path.join(BASE_DIR, 'conversaciones', month_es)
                os.makedirs(folder, exist_ok=True)

                filepath = os.path.join(folder, slug + '.md')
                today = date.today().strftime('%d/%m/%y')

                # Only create if doesn't exist yet
                if not os.path.exists(filepath):
                    lines_md = [
                        f'# {name}',
                        '',
                        f'**Fecha:** {today}',
                        f'**Cargo:** {cargo}' if cargo else '**Cargo:**',
                        f'**Empresa:** {empresa}' if empresa else '**Empresa:**',
                        f'**Pais:** {pais}' if pais else '**Pais:**',
                        '**Estado:** MSG1 enviado',
                        '',
                        '---',
                        '',
                        '## MSG1',
                    ]
                    for bubble in msg1.split('\n'):
                        if bubble.strip():
                            lines_md.append(f'> {bubble}')
                        else:
                            lines_md.append('>')
                    lines_md += ['', '---', '', '## Notas', '']
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines_md))

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True, 'file': filepath}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

        elif self.path == '/api/sync':
            try:
                msgs = []
                for cmd in [
                    ['git', '-C', BASE_DIR, 'add', 'historial.json'],
                    ['git', '-C', BASE_DIR, 'commit', '-m', 'sync historial', '--allow-empty'],
                    ['git', '-C', BASE_DIR, 'push'],
                ]:
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    msgs.append(r.stdout.strip() or r.stderr.strip())
                    if r.returncode != 0 and cmd[3] != 'commit':
                        raise Exception(msgs[-1])
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True, 'msg': ' | '.join(msgs)}).encode('utf-8'))
            except Exception as e:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': False, 'msg': str(e)}).encode('utf-8'))

        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    with socketserver.TCPServer(('0.0.0.0', PORT), RequestHandler) as httpd:
        print(f'Servidor corriendo en http://localhost:{PORT}')
        httpd.serve_forever()
