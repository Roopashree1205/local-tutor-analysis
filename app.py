"""Run: python app.py. Open http://127.0.0.1:8000."""
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from analytics import parse_csv, analyze

ROOT = Path(__file__).resolve().parent
class Handler(BaseHTTPRequestHandler):
    def send(self, status, body, kind='application/json'):
        data = body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', kind + '; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        if self.path == '/':
            return self.send(200, (ROOT/'index.html').read_text(encoding='utf-8'), 'text/html')
        if self.path == '/sample.csv':
            return self.send(200, (ROOT/'data/tutor_data.csv').read_text(), 'text/csv')
        self.send(404, json.dumps({'error':'Not found'}))
    def do_POST(self):
        if self.path != '/api/analyze':
            return self.send(404, json.dumps({'error':'Not found'}))
        if self.headers.get('Origin') not in (None, 'http://127.0.0.1:8000', 'http://localhost:8000'):
            return self.send(403, json.dumps({'error':'Origin rejected'}))
        try:
            size = int(self.headers.get('Content-Length', 0))
            if not 0 < size <= 2_000_000:
                raise ValueError('Upload must be under 2 MB.')
            payload = json.loads(self.rfile.read(size).decode('utf-8'))
            rows = parse_csv(payload['csv'])
            self.send(200, json.dumps(analyze(rows, payload.get('location', '')), allow_nan=False))
        except (ValueError, KeyError, TypeError) as e:
            self.send(400, json.dumps({'error':str(e)}))
if __name__ == '__main__':
    print('Tutor Analysis running at http://127.0.0.1:8000 — Ctrl+C to stop', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8000), Handler).serve_forever()
