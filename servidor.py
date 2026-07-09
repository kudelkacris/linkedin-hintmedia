#!/usr/bin/env python3
import json
import http.server
import socketserver
import httpx
import os
import threading
import subprocess
import unicodedata
import re as _re
from datetime import datetime as _dt

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
CONV_DIR  = os.path.join(BASE_DIR, 'conversaciones')
INTELLIGENCE_CONTEXT = os.path.join(BASE_DIR, 'hint_intelligence', 'outputs', 'context_injection.json')
INTELLIGENCE_ALERTS  = os.path.join(BASE_DIR, 'hint_intelligence', 'outputs', 'alerts.json')

client = httpx.Client(timeout=httpx.Timeout(connect=15.0, read=120.0, write=10.0, pool=5.0))

# ── File watcher: sync .md stages → historial.json ──────────────────────────

def _norm(name):
    """Normalize name: remove accents, lowercase, collapse spaces."""
    nfkd = unicodedata.normalize('NFKD', str(name))
    stripped = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return ' '.join(stripped.lower().split())

def _detect_stage(content):
    """
    Returns (stage: int|None, is_closed: bool).
    Stage order: 1=Apertura 2=MSG2 3=Dossier 4=SEG1 5=SEG2 6=Reunión
    """
    estado = ''
    m = _re.search(r'\*\*Estado:\*\*\s*(.+)', content, _re.IGNORECASE)
    if m:
        estado = m.group(1).lower()

    if 'cerrada' in estado or 'no interesad' in estado or 'descartad' in estado:
        return (None, True)
    if 'reunión' in estado or 'reunion' in estado or 'call agendada' in estado:
        return (6, False)
    if 'seg2' in estado or 'seguimiento 2' in estado:
        return (5, False)
    if 'seg1' in estado or 'seguimiento 1' in estado:
        return (4, False)
    if 'dossier enviado' in estado or 'msg3' in estado:
        return (3, False)
    if 'msg2' in estado or 'en conv' in estado:
        return (2, False)
    if 'msg1' in estado or 'apertura' in estado:
        return (1, False)

    # Fallback: section headers (most advanced wins)
    cl = content.lower()
    if '## seg2' in cl:
        return (5, False)
    if '## seg1' in cl:
        return (4, False)
    if 'dossier enviado' in cl or '## msg3' in cl:
        return (3, False)
    if '## msg2' in cl:
        return (2, False)
    if '## msg1' in cl:
        return (1, False)

    return (None, False)

def _sync_md(filepath):
    """Read one .md and update historial.json if stage changed."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract name from first # heading
        nm = _re.search(r'^#\s+(.+)$', content, _re.MULTILINE)
        if not nm:
            return
        name = nm.group(1).strip()

        stage, is_closed = _detect_stage(content)
        if stage is None and not is_closed:
            return

        with _hist_lock:
            try:
                with open(HIST_FILE, 'r', encoding='utf-8-sig') as f:
                    historial = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return

            norm_target = _norm(name)
            changed = False
            for entry in historial:
                entry_name = entry.get('name') or entry.get('nombre') or ''
                if _norm(entry_name) == norm_target:
                    cur = int(entry.get('stage', 1))
                    sh  = entry.get('stageHistory', [])
                    today = _dt.now().strftime('%d/%m/%y')

                    if is_closed:
                        if not any('Cerrada' in str(s.get('note', '')) for s in sh):
                            sh.append({'stage': cur, 'date': today, 'note': 'Cerrada'})
                            entry['stageHistory'] = sh
                            changed = True
                    elif stage > cur:
                        entry['stage'] = str(stage)
                        sh.append({'stage': stage, 'date': today})
                        entry['stageHistory'] = sh
                        changed = True
                    break

            if changed:
                with open(HIST_FILE, 'w', encoding='utf-8') as f:
                    json.dump(historial, f, ensure_ascii=False, indent=2)
                label = 'cerrada' if is_closed else f'stage {stage}'
                print(f'[watcher] {name} -> {label}')
    except Exception as e:
        print(f'[watcher] error en {filepath}: {e}')

def _start_watcher():
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class _Handler(FileSystemEventHandler):
            def _handle(self, path):
                if path.endswith('.md'):
                    _sync_md(path)
            def on_modified(self, event):
                if not event.is_directory:
                    self._handle(event.src_path)
            def on_created(self, event):
                if not event.is_directory:
                    self._handle(event.src_path)

        if not os.path.exists(CONV_DIR):
            os.makedirs(CONV_DIR, exist_ok=True)
        obs = Observer()
        obs.schedule(_Handler(), CONV_DIR, recursive=True)
        obs.daemon = True
        obs.start()
        print(f'[watcher] monitoreando conversaciones/')
    except ImportError:
        print('[watcher] watchdog no instalado — pip install watchdog')

# ── End watcher ──────────────────────────────────────────────────────────────

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
                with open(HIST_FILE, 'r', encoding='utf-8-sig') as f:
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
                        with open(HIST_FILE, 'r', encoding='utf-8-sig') as f:
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

                # Extract cargo and country from profileRaw
                cargo = ''
                pais = ''
                lines_clean = [l.strip() for l in profile_raw.split('\n') if l.strip()]

                # Cargo: LinkedIn headline always appears right after the "· 1er / · 2º" connection line
                for i, line in enumerate(lines_clean):
                    if re.search(r'·\s*(1er|2º|3º|1st|2nd|3rd)', line) and i + 1 < len(lines_clean):
                        candidate = lines_clean[i + 1]
                        # Skip if it looks like a location or generic text
                        if not re.search(r'(Argentina|Colombia|Chile|México|Panamá|Costa Rica|Perú|Uruguay|España|Brasil|Venezuela|Ecuador|Bolivia|Paraguay|Guatemala)', candidate, re.I):
                            cargo = candidate[:150]
                        break

                # Country: scan all lines
                pais_pattern = r'(Argentina|Colombia|Chile|México|Mexico|Panamá|Panama|Costa Rica|Perú|Peru|Uruguay|España|Espana|Brasil|Brazil|Venezuela|Ecuador|Bolivia|Paraguay|Guatemala|Honduras|El Salvador|Nicaragua|Rep\. Dominicana|Puerto Rico)'
                for line in lines_clean:
                    if not pais:
                        m = re.search(pais_pattern, line, re.I)
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

                analysis = d.get('analysis', {})

                # Only create if doesn't exist yet
                if not os.path.exists(filepath):
                    lines_md = [
                        f'# {name}',
                        '',
                        f'**Fecha:** {today}',
                        f'**Cargo:** {cargo}' if cargo else '**Cargo:**',
                        f'**Empresa:** {empresa}' if empresa else '**Empresa:**',
                        f'**Pais:** {pais}' if pais else '**Pais:**',
                        f'**Sector:** {analysis.get("sector", "")}' if analysis.get('sector') else '**Sector:**',
                        '**Estado:** MSG1 enviado',
                        '',
                        '---',
                        '',
                    ]
                    # Analysis section
                    a_fields = [
                        ('Señal humana', analysis.get('senalHumana')),
                        ('Tensión profesional', analysis.get('tension')),
                        ('Hipótesis', analysis.get('hipotesis')),
                        ('Ángulo MSG1', analysis.get('angulo')),
                        ('Confidence', analysis.get('confLevel')),
                    ]
                    has_analysis = any(v for _, v in a_fields)
                    if has_analysis:
                        lines_md.append('## Análisis')
                        for label, val in a_fields:
                            if val:
                                lines_md.append(f'- **{label}:** {val}')
                        lines_md += ['', '---', '']
                    lines_md.append('## MSG1')
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

        elif self.path == '/api/cre':
            try:
                import sys as _sys
                _sys.path.insert(0, BASE_DIR)
                from commercial_reasoning_engine.analyzer.parser import parse as _cre_parse
                from commercial_reasoning_engine.run import run as _cre_run
                from commercial_reasoning_engine.llm.context_only_adapter import ContextOnlyAdapter as _CREAdapter

                d = json.loads(body)
                conv_text      = d.get('conversation', '')
                prospect_name  = d.get('prospect_name', '') or None
                sector         = d.get('sector', '')
                seniority      = d.get('seniority', '')
                stage          = d.get('stage', '1')

                prospect_data = {'stage': stage, 'sector': sector, 'cargo_seniority': seniority}
                conversation  = _cre_parse(conv_text, prospect_name=prospect_name)
                adapter       = _CREAdapter()
                result        = _cre_run(conversation, adapter=adapter, prospect_data=prospect_data)

                if result.blocked:
                    resp = {'blocked': True, 'block_reason': result.block_reason, 'prompt': None}
                else:
                    prompt = adapter.build_prompt(result.context)
                    resp = {'blocked': False, 'block_reason': None, 'prompt': prompt}

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

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
    _start_watcher()
    with socketserver.TCPServer(('0.0.0.0', PORT), RequestHandler) as httpd:
        print(f'Servidor corriendo en http://localhost:{PORT}')
        httpd.serve_forever()
