#!/usr/bin/env python3
"""Servidor local que emula el comportamiento de Cloudflare Pages.

  /v1/*/            -> /v1/*/index.json   (rewrite 200)
  /v1/*  (sin /)    -> /v1/*/             (redirect 308)
  404 bajo /v1/     -> /v1/404.html       (404 anidado, cuerpo JSON)
  404 elsewhere     -> /404.html          (404 global, cuerpo HTML)

Uso:  python3 scripts/serve_local.py [puerto]
"""
import sys
import os
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api')


def _already_serving(port):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/v1/', timeout=2) as r:
            return r.headers.get('Content-Type', '').startswith('application/json')
    except Exception:
        return False


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        self._resolved = None
        self._not_found = False
        super().__init__(*a, directory=ROOT, **kw)

    def _nearest_404(self, clean):
        node = os.path.join(ROOT, clean.lstrip('/'))
        while os.path.abspath(node) != os.path.abspath(ROOT):
            cand = os.path.join(node, '404.html')
            if os.path.isfile(cand):
                return cand
            node = os.path.dirname(node)
        return os.path.join(ROOT, '404.html')

    def translate_path(self, path):
        if self._resolved is not None:
            return self._resolved

        clean = unquote(path.split('?', 1)[0].split('#', 1)[0])

        if clean.startswith('/v1/'):
            fs = os.path.join(ROOT, clean.lstrip('/'))

            # Pages aplica los redirects antes de buscar el asset:
            #   /v1/* -> /v1/*/  308
            if not clean.endswith('/') and not os.path.splitext(clean)[1]:
                self.send_response(308)
                self.send_header('Location', clean + '/')
                self.end_headers()
                self._resolved = ''
                return ''

            #   /v1/*/ -> /v1/*/index.json  200
            if os.path.isdir(fs):
                idx = os.path.join(fs, 'index.json')
                if os.path.isfile(idx):
                    self._resolved = idx
                    return idx

            if not os.path.exists(fs):
                self._not_found = True
                self._resolved = self._nearest_404(clean)
                return self._resolved

        resolved = super().translate_path(path)
        self._resolved = resolved
        return resolved

    def send_head(self):
        resolved = self.translate_path(self.path)

        if self._resolved == '':
            return None

        if not self._not_found:
            return super().send_head()

        try:
            with open(resolved, 'rb') as f:
                body = f.read()
        except OSError:
            body = b'404: Not Found'

        ctype = 'application/problem+json' if resolved.endswith(os.path.join('v1', '404.html')) else 'text/html; charset=utf-8'

        self.send_response(404)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()

        import io
        return io.BytesIO(body)

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    try:
        srv = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    except OSError as e:
        if e.errno != 98:
            raise
        if _already_serving(port):
            print(f'Ya hay un server corriendo en http://localhost:{port}')
            print(f'  comparador de rediseños: http://localhost:{port}/temp/')
            print(f'  (para otra instancia pasale otro puerto: python3 scripts/serve_local.py {port + 1})')
            sys.exit(0)
        print(f'El puerto {port} está ocupado por otro proceso.')
        print(f'  levantá esta server en otro puerto: python3 scripts/serve_local.py {port + 1}')
        sys.exit(1)

    print(f'serving {ROOT} en http://localhost:{port}')
    print(f'  comparador de rediseños: http://localhost:{port}/temp/')
    srv.serve_forever()
