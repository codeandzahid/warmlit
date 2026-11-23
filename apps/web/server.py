"""Warmlit local web UI. Stdlib only — runs anywhere Python runs.

Run:  python3 apps/web/server.py
Open: http://localhost:8765
"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from packages.agent_core import Agent, ApprovalGate, MemoryStore, Scheduler, UsageCounter, check_license, default_tools, pick_model  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

# Owner-only: Warmlit is personal, everything unlocked for the owner.
license_info = {"plan": "paid", "expires": None, "days_left": 0}
scheduler = Scheduler(store=DATA / "jobs.json")
_memory = MemoryStore(DATA / "memory")
agent = Agent(
    model=pick_model(),
    memory=_memory,
    tools=default_tools(DATA / "workspace", memory=_memory, data_root=DATA),
    scheduler=scheduler,
    plan="paid",  # owner: everything unlocked, no daily limit
    usage=None,
)

MANIFEST = json.dumps({
    "name": "Warmlit", "short_name": "Warmlit", "start_url": "/", "display": "standalone",
    "background_color": "#111827", "theme_color": "#111827",
    "icons": [{"src": "/icon.png", "sizes": "512x512", "type": "image/png"}],
})
SW_JS = "self.addEventListener('fetch',e=>{e.respondWith(fetch(e.request).catch(()=>caches.match('/')))});self.addEventListener('install',e=>{e.waitUntil(caches.open('warmlit').then(c=>c.add('/')))});"


def _icon_png() -> bytes:
    import io
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (512, 512), "#111827")
    d = ImageDraw.Draw(img)
    d.ellipse([106, 106, 406, 406], fill="#f59e0b")
    d.text((226, 216), "W", fill="white")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


PAGE = """<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<link rel=manifest href=/manifest.json><title>Warmlit</title>
<style>body{font-family:system-ui;max-width:760px;margin:20px auto;padding:0 12px}
#chat{border:1px solid #ccc;border-radius:10px;padding:10px;height:55vh;overflow:auto}
.u{background:#dbeafe}.a{background:#f3f4f6}.m{border-radius:10px;padding:8px;margin:6px 0;white-space:pre-wrap}
input{width:78%;padding:10px}button{padding:10px 14px}.card{border:2px solid orange;padding:10px;margin:8px 0;border-radius:8px}</style></head>
<body><h2>Warmlit — your local agent</h2>
<p id=plan>Plan: loading…</p>
<script>fetch('/health').then(r=>r.json()).then(j=>{document.getElementById('plan').textContent='Plan: '+j.plan+(j.plan==='paid'?' ('+j.days_left+' days left)':' — local system tasks need Paid')+' · Model: '+j.model;});</script>
<p>Try: <code>/remember I like tea</code> · <code>/search tea</code> · <code>/tools</code> · <code>/web https://example.com</code> · <code>/write note.txt hello</code> · <code>/job every:60s /remember tick</code></p>
<div id=chat></div>
<p><input id=msg placeholder="Message Warmlit…"><button onclick=send()>Send</button>
<button onclick=mic()>🎤 Talk</button><button onclick=speakLast()>🔊 Speak</button><button onclick=voiceNote()>⏺ Voice note</button></p>
<p><button onclick=panel('goals')>Goals</button><button onclick=panel('feed')>Feed</button><button onclick=panel('ideas')>Ideas</button><button onclick=panel('library')>Library</button><button onclick=panel('connectors')>Connectors</button></p>
<div id=panel></div>
<script>
let lastReply='';
async function panel(name){const map={goals:'/goal',feed:'/feed',ideas:'/idea',library:'/library',connectors:'/connectors'};
 const r=await fetch('/chat',{method:'POST',body:JSON.stringify({text:map[name]})});const j=await r.json();
 document.getElementById('panel').innerHTML='<pre>'+j.reply.replace(/</g,'&lt;')+'</pre>';}
function mic(){const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){alert('No mic speech in this browser');return;}
 const r=new SR();r.onresult=e=>{document.getElementById('msg').value=e.results[0][0].transcript;send();};r.start();}
function speakLast(){if(lastReply)speechSynthesis.speak(new SpeechSynthesisUtterance(lastReply));}
let rec,chunks=[];async function voiceNote(){if(rec&&rec.state==='recording'){rec.stop();return;}
 const s=await navigator.mediaDevices.getUserMedia({audio:true});rec=new MediaRecorder(s);chunks=[];
 rec.ondataavailable=e=>chunks.push(e.data);rec.onstop=async()=>{const b=new Blob(chunks,{type:'audio/webm'});
  await fetch('/voicenote',{method:'POST',body:b});add('a','Voice note saved.');};rec.start();add('a','Recording… tap Voice note again to stop.');}
if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js');
</script>
<script>
const chat=document.getElementById('chat');
function add(cls,txt){const d=document.createElement('div');d.className='m '+cls;d.textContent=txt;chat.appendChild(d);chat.scrollTop=chat.scrollHeight;}
async function send(){const i=document.getElementById('msg');const t=i.value.trim();if(!t)return;i.value='';add('u',t);
 const r=await fetch('/chat',{method:'POST',body:JSON.stringify({text:t})});const j=await r.json();lastReply=j.reply;add('a',j.reply);}
document.getElementById('msg').addEventListener('keydown',e=>{if(e.key==='Enter')send();});
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body: bytes, ctype="application/json"):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._send(PAGE.encode(), "text/html; charset=utf-8")
        elif self.path == "/manifest.json":
            self._send(MANIFEST.encode())
        elif self.path == "/sw.js":
            self._send(SW_JS.encode(), "application/javascript")
        elif self.path == "/icon.png":
            self._send(_icon_png(), "image/png")
        elif self.path == "/health":
            self._send(json.dumps({"ok": True, "model": agent.model.name, "jobs": len(scheduler.jobs), "plan": agent.plan, "days_left": license_info["days_left"]}).encode())
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path == "/voicenote":
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            out = DATA / "workspace" / "voice-notes"
            out.mkdir(parents=True, exist_ok=True)
            import time as _t
            (out / f"note-{int(_t.time())}.webm").write_bytes(raw)
            self._send(b'{"ok":true}')
            return
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if self.path == "/chat":
            reply = agent.chat(body.get("text", ""))
            self._send(json.dumps({"reply": reply}).encode())
        else:
            self.send_response(404); self.end_headers()


if __name__ == "__main__":
    DATA.mkdir(parents=True, exist_ok=True)
    scheduler.start(agent, DATA / "jobs.log")
    print(f"Warmlit running: http://localhost:8765  (model: {agent.model.name}, plan: {agent.plan})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
