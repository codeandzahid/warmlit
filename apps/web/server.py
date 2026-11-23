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

pending_approvals: dict[str, threading.Event] = {}
approval_results: dict[str, bool] = {}
counter = [0]


def ask_approval(action: str) -> bool:
    counter[0] += 1
    aid = str(counter[0])
    ev = threading.Event()
    pending_approvals[aid] = ev
    print(f"[approval needed #{aid}] {action} — approve in the web UI", flush=True)
    ev.wait(timeout=300)
    return approval_results.pop(aid, False)


# Owner-only: Warmlit is personal, everything unlocked for the owner.
license_info = {"plan": "paid", "expires": None, "days_left": 0}
scheduler = Scheduler(store=DATA / "jobs.json")
agent = Agent(
    model=pick_model(),
    memory=MemoryStore(DATA / "memory"),
    tools=default_tools(DATA / "workspace"),
    approvals=ApprovalGate(approve=ask_approval),
    scheduler=scheduler,
    plan="paid",  # owner: everything unlocked, no daily limit
    usage=None,
)

PAGE = """<!doctype html><html><head><meta charset=utf-8><title>Warmlit</title>
<style>body{font-family:system-ui;max-width:760px;margin:20px auto;padding:0 12px}
#chat{border:1px solid #ccc;border-radius:10px;padding:10px;height:55vh;overflow:auto}
.u{background:#dbeafe}.a{background:#f3f4f6}.m{border-radius:10px;padding:8px;margin:6px 0;white-space:pre-wrap}
input{width:78%;padding:10px}button{padding:10px 14px}.card{border:2px solid orange;padding:10px;margin:8px 0;border-radius:8px}</style></head>
<body><h2>Warmlit — your local agent</h2>
<p id=plan>Plan: loading…</p>
<script>fetch('/health').then(r=>r.json()).then(j=>{document.getElementById('plan').textContent='Plan: '+j.plan+(j.plan==='paid'?' ('+j.days_left+' days left)':' — local system tasks need Paid')+' · Model: '+j.model;});</script>
<p>Try: <code>/remember I like tea</code> · <code>/search tea</code> · <code>/tools</code> · <code>/web https://example.com</code> · <code>/write note.txt hello</code> · <code>/job every:60s /remember tick</code></p>
<div id=approvals></div><div id=chat></div>
<p><input id=msg placeholder="Message Warmlit…"><button onclick=send()>Send</button></p>
<script>
const chat=document.getElementById('chat');
function add(cls,txt){const d=document.createElement('div');d.className='m '+cls;d.textContent=txt;chat.appendChild(d);chat.scrollTop=chat.scrollHeight;}
async function send(){const i=document.getElementById('msg');const t=i.value.trim();if(!t)return;i.value='';add('u',t);
 const r=await fetch('/chat',{method:'POST',body:JSON.stringify({text:t})});const j=await r.json();add('a',j.reply);pollApprovals();}
async function pollApprovals(){const r=await fetch('/approvals');const j=await r.json();const box=document.getElementById('approvals');box.innerHTML='';
 j.pending.forEach(id=>{const d=document.createElement('div');d.className='card';d.innerHTML='Approval needed #'+id+' ';
  const y=document.createElement('button');y.textContent='Approve';y.onclick=()=>decide(id,true);
  const n=document.createElement('button');n.textContent='Deny';n.onclick=()=>decide(id,false);
  d.appendChild(y);d.appendChild(n);box.appendChild(d);});}
async function decide(id,ok){await fetch('/approve',{method:'POST',body:JSON.stringify({id,ok})});pollApprovals();}
setInterval(pollApprovals,3000);pollApprovals();
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
        elif self.path == "/approvals":
            self._send(json.dumps({"pending": list(pending_approvals)}).encode())
        elif self.path == "/health":
            self._send(json.dumps({"ok": True, "model": agent.model.name, "jobs": len(scheduler.jobs), "plan": agent.plan, "days_left": license_info["days_left"]}).encode())
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if self.path == "/chat":
            reply = agent.chat(body.get("text", ""))
            self._send(json.dumps({"reply": reply}).encode())
        elif self.path == "/approve":
            aid = str(body.get("id"))
            approval_results[aid] = bool(body.get("ok"))
            ev = pending_approvals.pop(aid, None)
            if ev:
                ev.set()
            self._send(b'{"ok":true}')
        else:
            self.send_response(404); self.end_headers()


if __name__ == "__main__":
    DATA.mkdir(parents=True, exist_ok=True)
    scheduler.start(agent, DATA / "jobs.log")
    print(f"Warmlit running: http://localhost:8765  (model: {agent.model.name}, plan: {agent.plan})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
