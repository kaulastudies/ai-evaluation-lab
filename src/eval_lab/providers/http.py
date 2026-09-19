from __future__ import annotations
import json, os, time, urllib.error, urllib.request
from eval_lab.providers.base import ProviderResult
from eval_lab.tasks import EvaluationTask

class ProviderConfigurationError(RuntimeError): pass

class OpenAICompatibleProvider:
    def __init__(self, name: str, base_url: str, api_key_env: str, model_env: str):
        self.name, self.base_url = name, base_url.rstrip("/")
        self.api_key_env, self.model_env = api_key_env, model_env

    def run(self, task: EvaluationTask, *, response_override: str | None = None) -> ProviderResult:
        if response_override is not None:
            raise ValueError("response_override is only supported by the mock provider")
        api_key, model = os.getenv(self.api_key_env, "").strip(), os.getenv(self.model_env, "").strip()
        if not api_key or not model:
            raise ProviderConfigurationError(f"Set {self.api_key_env} and {self.model_env} before using {self.name}.")
        payload = {"model": model, "messages": [{"role": "user", "content": task.prompt}], "temperature": 0}
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "rama-ai-evaluation-lab/0.1"},
            method="POST",
        )
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                body = json.loads(res.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"{self.name} HTTP {exc.code}: {detail}") from exc
        usage = body.get("usage") or {}
        return ProviderResult(self.name, model, body["choices"][0]["message"]["content"],
                              int((time.perf_counter()-started)*1000),
                              usage.get("prompt_tokens"), usage.get("completion_tokens"), None)

class OllamaProvider:
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    def run(self, task: EvaluationTask, *, response_override: str | None = None) -> ProviderResult:
        if response_override is not None:
            raise ValueError("response_override is only supported by the mock provider")

        model = os.getenv("OLLAMA_MODEL", "").strip()
        if not model:
            raise ProviderConfigurationError("Set OLLAMA_MODEL before using Ollama.")

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": task.prompt}],
            "stream": False,
            "options": {"temperature": 0},
        }
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "rama-ai-evaluation-lab/0.1",
            },
            method="POST",
        )

        started = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=180) as res:
                body = json.loads(res.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"ollama HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"ollama connection failed at {self.base_url}: {exc}"
            ) from exc

        message = body.get("message") or {}
        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("ollama response did not contain message.content")

        return ProviderResult(
            provider=self.name,
            model=model,
            response=content,
            latency_ms=int((time.perf_counter() - started) * 1000),
            input_tokens=body.get("prompt_eval_count"),
            output_tokens=body.get("eval_count"),
            estimated_cost_usd=0.0,
        )

class GeminiProvider:
    name = "gemini"

    def run(self, task: EvaluationTask, *, response_override: str | None = None) -> ProviderResult:
        if response_override is not None:
            raise ValueError("response_override is only supported by the mock provider")
        api_key, model = os.getenv("GEMINI_API_KEY", "").strip(), os.getenv("GEMINI_MODEL", "").strip()
        if not api_key or not model:
            raise ProviderConfigurationError("Set GEMINI_API_KEY and GEMINI_MODEL before using Gemini.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {"contents": [{"role": "user", "parts": [{"text": task.prompt}]}], "generationConfig": {"temperature": 0}}
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "rama-ai-evaluation-lab/0.1"},
                                     method="POST")
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                body = json.loads(res.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"Gemini HTTP {exc.code}: {detail}") from exc
        usage = body.get("usageMetadata") or {}
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        return ProviderResult(self.name, model, text, int((time.perf_counter()-started)*1000),
                              usage.get("promptTokenCount"), usage.get("candidatesTokenCount"), None)

def provider_from_name(name: str):
    key = name.lower()
    if key == "gemini": return GeminiProvider()
    if key == "ollama": return OllamaProvider()
    configs = {
        "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", "GROQ_MODEL"),
        "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "OPENROUTER_MODEL"),
        "cerebras": ("https://api.cerebras.ai/v1", "CEREBRAS_API_KEY", "CEREBRAS_MODEL"),
        "fireworks": ("https://api.fireworks.ai/inference/v1", "FIREWORKS_API_KEY", "FIREWORKS_MODEL"),
        "nebius": ("https://api.tokenfactory.nebius.com/v1", "NEBIUS_API_KEY", "NEBIUS_MODEL"),
    }
    if key not in configs: raise ProviderConfigurationError(f"Unknown live provider: {name}")
    base, api_env, model_env = configs[key]
    return OpenAICompatibleProvider(key, base, api_env, model_env)
