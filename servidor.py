#!/usr/bin/env python3
import json
import http.server
import socketserver
import httpx
import os

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
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        if self.path == '/api/generate':
            data = json.loads(body)
            prompt = data.get('prompt', '')
            try:
                response = client.post(API_URL,
                    json={'model': 'claude-haiku-4-5-20251001', 'max_tokens': 4000,
                          'messages': [{'role': 'user', 'content': prompt}]},
                    headers={'x-api-key': API_KEY, 'anthropic-version': '2023-06-01'}
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
                entries = json.loads(body)
                with open(HIST_FILE, 'w', encoding='utf-8') as f:
                    json.dump(entries, f, ensure_ascii=False, indent=2)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
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
    with socketserver.TCPServer(('0.0.0.0', PORT), RequestHandler) as httpd:
        print(f'Servidor corriendo en http://localhost:{PORT}')
        httpd.serve_forever()
