"""MATCHLAB AZ v0.9.52 — public HTTPS hosting adapter (Python stdlib).

Deployment uses the existing validated database and API, but blocks local maintenance,
dangerous upload/install routes, and unnecessary user-triggered upstream refreshes.
"""
import os, json, time, threading, urllib.parse
from http.server import ThreadingHTTPServer
from server import Handler as LocalHandler, send_data
import world_db

RATE_LIMIT = 180
RATE_WINDOW = 60.0
RATE_LOCK = threading.Lock()
RATE_BUCKETS = {}

def is_allowed(ip):
    now = time.monotonic()
    with RATE_LOCK:
        if len(RATE_BUCKETS) > 5000:
            for key, (ts, amount) in list(RATE_BUCKETS.items()):
                if now - ts > RATE_WINDOW: RATE_BUCKETS.pop(key, None)
        ts, amount = RATE_BUCKETS.get(ip, (now, 0))
        if now - ts > RATE_WINDOW: ts, amount = now, 0
        amount += 1
        RATE_BUCKETS[ip] = ts, amount
        return amount <= RATE_LIMIT

class PublicHandler(LocalHandler):
    server_version = 'MATCHLAB/0.9.52'

    def do_POST(self):
        # Critical: Internet visitors must not start large imports or upload arbitrary files.
        self.json_response(403, {'error': 'Onlayn versiyada fayl yükləmə və indeks yeniləmə bağlıdır.'})

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if path == '/healthz':
            reg=world_db.counts()
            ok=bool(reg and reg.get('total') == 506207)
            return self.json_response(200 if ok else 503, {'ok': ok, 'service': 'matchlab', 'version': '0.9.52', 'registryTotal':reg.get('total',0) if reg else 0, 'hosting':'render'})
        # Do not expose public repository internals through SimpleHTTPRequestHandler.
        # Encoded paths and mixed-case extensions must not bypass the check.
        decoded=urllib.parse.unquote(path).replace('\\\\','/').lower()
        segments=[part for part in decoded.split('/') if part not in ('', '.')]
        private_names={'hosting_server.py','server.py','world_football.sqlite',
                       'data_manifest.json','render.yaml','.env','.git',
                       'prepare_database.py','requirements.txt'}
        private_dirs={'.git','.github','deploy','tests','native','score_cache'}
        private_extensions=('.py','.pyc','.sqlite','.db','.gz','.part001','.part002',
                            '.part003','.part004','.part005','.part006','.part007','.part008',
                            '.part009','.part010','.part011','.part012','.part013','.part014',
                            '.part015','.part016','.pem','.key','.env')
        if (any(part in private_dirs or part.startswith('.') for part in segments)
            or any(part in private_names or part.endswith(private_extensions) for part in segments)):
            return self.json_response(404, {'error': 'Not found'})
        if path in ('/api/install-start', '/api/install-upload', '/api/install-status', '/api/wikipedia-refresh'):
            return self.json_response(403, {'error': 'İctimai serverdə bu əməliyyat aktiv deyil.'})
        if path == '/api/status':
            try:
                result = send_data(path,{})
                result.update({'version': '0.9.52', 'publicHosting': True, 'canInstall': False})
                return self.json_response(200, result)
            except Exception:
                return self.json_response(503, {'ok': False, 'error': 'Baza əlçatan deyil'})
        # Only same-origin requests are needed; no CORS for third party sites.
        xf = self.headers.get('X-Forwarded-For', '')
        # The rightmost forwarded hop is less vulnerable to forged leading XFF values.
        ip = xf.split(',')[-1].strip()[:70] if xf else self.client_address[0]
        if not is_allowed(ip):
            return self.json_response(429, {'error': 'Sorğu limiti: bir az sonra yenidən yoxla.'})
        if path.startswith('/api/') and len(self.path) > 1200:
            return self.json_response(414, {'error': 'Sorğu çox uzundur'})
        return super().do_GET()

def main():
    port = int(os.environ.get('PORT', '10000'))
    if not (1 <= port <= 65535): raise ValueError('Invalid PORT')
    bind_host=os.environ.get('MATCHLAB_BIND_HOST','0.0.0.0')
    if bind_host not in ('127.0.0.1','0.0.0.0'):
        raise ValueError('MATCHLAB_BIND_HOST must be 127.0.0.1 or 0.0.0.0')
    with ThreadingHTTPServer((bind_host, port), PublicHandler) as httpd:
        print(f'MATCHLAB AZ onlayn server: {bind_host}:{port}', flush=True)
        httpd.serve_forever(poll_interval=0.5)

if __name__ == '__main__': main()
