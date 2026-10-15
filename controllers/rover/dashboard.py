"""Localhost read-only dashboard; controller owns all motion commands."""
import json,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
PAGE='''<!doctype html><meta charset="utf-8"><title>Closed-course rover</title><style>body{background:#101d29;color:#e3edf4;font:18px system-ui;max-width:1000px;margin:30px auto}pre{background:#1a3042;padding:20px}img{width:23%;margin:1%}b{color:#5fe1b0}</style><h1>Closed-course rover</h1><b>Simulation telemetry · metres / radians</b><pre id="s">Waiting for controller…</pre><div id="cams"></div><script>setInterval(async()=>{try{let r=await fetch('/status');s.textContent=JSON.stringify(await r.json(),null,2);cams.innerHTML=['front','rear','left','right'].map(n=>`<img title="${n}" src="/${n}.jpg?t=${Date.now()}">`).join('')}catch(e){}},1000)</script>'''
class Dashboard:
    def __init__(self,folder,port=8765):
        self.folder=Path(folder); self.folder.mkdir(exist_ok=True); self.data={}
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                name=self.path.split('?')[0]
                if name=='/status': body=json.dumps(owner.data,allow_nan=False).encode(); mime='application/json'
                elif name in ['/front.jpg','/rear.jpg','/left.jpg','/right.jpg']:
                    try: body=(owner.folder/name[1:]).read_bytes()
                    except OSError: self.send_error(404); return
                    mime='image/jpeg'
                elif name=='/': body=PAGE.encode(); mime='text/html'
                else: self.send_error(404); return
                self.send_response(200); self.send_header('Content-Type',mime); self.end_headers(); self.wfile.write(body)
            def log_message(self,*args): pass
        self.server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
    def update(self,data):
        self.data=data
        dest=self.folder/'status.json'; temp=dest.with_suffix('.tmp'); temp.write_text(json.dumps(data,indent=2)); temp.replace(dest)
