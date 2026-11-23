"""Voice, no keys.

- Web UI voice: the browser's own speech (mic + speaker) — see apps/web.
- Local TTS here: espeak-ng/espeak if installed; else a clear message.
- Voice notes: recorded in the web UI (MediaRecorder) and saved as files.
"""
import shutil
import subprocess


def say(text: str, out_wav: str | None = None) -> str:
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        return ("No local voice engine installed. Use the mic/speaker buttons "
                "in the Warmlit web UI (browser voice, no key), or install "
                "espeak-ng / Piper on this computer.")
    cmd = [exe, text]
    if out_wav:
        cmd = [exe, "-w", out_wav, text]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return f"voice error: {(r.stderr or r.stdout)[-300:]}"
    return f"spoke: {text[:60]}" + (f" -> {out_wav}" if out_wav else "")
