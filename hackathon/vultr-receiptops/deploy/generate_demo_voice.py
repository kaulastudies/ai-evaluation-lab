"""Generate an explicitly synthetic, built-in-voice narration for the demo.

Run once on the trusted VM with its existing inference environment. No voice
cloning or user audio is used. Output contains public narration only.
"""
import json
import os
from pathlib import Path
import httpx

root = Path(__file__).resolve().parents[1]
story = json.loads((root / "docs/demo-story.json").read_text())
out = Path("/opt/receiptops/receiptops/static/demo-audio")
out.mkdir(mode=0o755, exist_ok=True)
with httpx.Client(timeout=180) as client:
    for scene in story:
        target = out / (scene["frame"] + ".mp3")
        if target.exists():
            print(scene["frame"], "already generated", flush=True)
            continue
        response = client.post("https://api.vultrinference.com/v1/audio/speech",
            headers={"Authorization": "Bearer " + os.environ["VULTR_INFERENCE_API_KEY"]},
            json={"model": "qwen3-tts-12hz-1.7b", "voice": "aiden",
                  "input": scene["narration"], "language": "en",
                  "instructions": "Clear, calm professional product demonstration. Speak naturally at a measured pace. No dramatic emphasis.",
                  "response_format": "mp3"})
        response.raise_for_status()
        if not response.headers.get("content-type", "").startswith("audio/"):
            raise RuntimeError("Speech service did not return audio.")
        target.write_bytes(response.content)
        target.chmod(0o644)
        print(scene["frame"], len(response.content), "bytes", flush=True)
