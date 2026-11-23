"""Model providers. All use stdlib HTTP — no extra installs needed.

Pick with env / .env:
  MODEL_PROVIDER=echo | openai | ollama
  MODEL_API_KEY=...        (openai-compatible providers)
  MODEL_BASE_URL=https://api.openai.com/v1
  MODEL_NAME=gpt-4o-mini   (or any model the endpoint serves)
  OLLAMA_HOST=http://localhost:11434
  OLLAMA_MODEL=llama3.2
"""
import json
import os
import urllib.request
import urllib.error


class EchoModel:
    name = "echo-demo"

    def reply(self, system: str, history: list[dict], tools: list[dict]) -> str:
        last = history[-1]["content"] if history else ""
        return f"Echo: {last}"


class OpenAICompatibleModel:
    """Works with OpenAI, OpenRouter, Meta Model API, and any
    /v1/chat/completions endpoint."""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.name = model

    def reply(self, system: str, history: list[dict], tools: list[dict]) -> str:
        messages = [{"role": "system", "content": system}] + history
        body = json.dumps({"model": self.name, "messages": messages}).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode())
            return data["choices"][0]["message"]["content"]
        except urllib.error.URLError as e:
            return f"[model error: {e}]"


class OllamaModel:
    """Local model via Ollama (https://ollama.com). Free, runs on your PC."""

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.2"):
        self.host = host.rstrip("/")
        self.name = model

    def reply(self, system: str, history: list[dict], tools: list[dict]) -> str:
        messages = [{"role": "system", "content": system}] + history
        body = json.dumps({"model": self.name, "messages": messages, "stream": False}).encode()
        req = urllib.request.Request(
            f"{self.host}/api/chat", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.loads(r.read().decode())
            return data["message"]["content"]
        except urllib.error.URLError as e:
            return f"[ollama not reachable at {self.host}: {e}. Install Ollama and run: ollama pull {self.name}]"


def load_dotenv(path: str = ".env") -> None:
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    except FileNotFoundError:
        pass


def _ollama_alive(host: str) -> bool:
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=1) as r:
            return r.status == 200
    except Exception:
        return False


def pick_model():
    """Default is NO KEY: auto = Ollama if running locally, else LocalBrain.
    An API key is used only if the owner explicitly sets MODEL_PROVIDER=openai."""
    from .local_brain import LocalBrain

    load_dotenv()
    provider = os.environ.get("MODEL_PROVIDER", "auto").lower()
    if provider == "openai" and os.environ.get("MODEL_API_KEY"):
        return OpenAICompatibleModel(
            api_key=os.environ["MODEL_API_KEY"],
            base_url=os.environ.get("MODEL_BASE_URL", "https://api.openai.com/v1"),
            model=os.environ.get("MODEL_NAME", "gpt-4o-mini"),
        )
    if provider == "echo":
        return EchoModel()
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    if provider == "ollama" or _ollama_alive(host):
        return OllamaModel(host=host, model=os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b"))
    return LocalBrain()
