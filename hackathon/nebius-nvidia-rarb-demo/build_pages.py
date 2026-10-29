"""Build GitHub Pages from repository-owned source and hash-pinned dependencies."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from build_evidence import build, build_browser
from prepare_browser_runtime import prepare

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PUBLIC_FILES = (
    "index.html", "style.css", "app.js", "lab.js", "lab-worker.mjs",
    "browser_lab.py", "browser-runtime.json", "PYODIDE_LICENSE.txt",
    "PYTHON_LICENSE.txt", "THIRD_PARTY_NOTICES.md",
)
MEDIA_FILES = (
    "proofgate-team-card.svg", "proofgate-video-credits.svg",
    "proofgate-team-card.png", "proofgate-video-credits.png",
    "proofgate-walkthrough.mp4", "proofgate-mentorship-demo.jpg",
)


def build_pages(output: Path) -> Path:
    output = output.resolve()
    if output == ROOT or output in ROOT.parents or output == HERE:
        raise ValueError("Choose a separate build output directory")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Build output must be absent or empty; existing files are never removed")
    prepare()
    app = output / "proofgate"
    app.mkdir(parents=True, exist_ok=True)
    for name in PUBLIC_FILES:
        shutil.copy2(HERE / name, app / name)
    for name in MEDIA_FILES:
        shutil.copy2(HERE / "submission/media" / name, app / name)
    shutil.copy2(ROOT / "LICENSE", app / "LICENSE")
    shutil.copytree(HERE / "vendor/pyodide", app / "vendor/pyodide")
    for name, bundle in (("evidence.json", build()), ("browser-evidence.json", build_browser())):
        (app / name).write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n")

    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    hashes = {p.relative_to(app).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(app.rglob("*")) if p.is_file()}
    (app / "deployment.json").write_text(json.dumps({
        "repository": "https://github.com/kaulastudies/ai-evaluation-lab",
        "source_commit": revision,
        "evidence_commit": build()["evidence_commit"],
        "files_sha256": hashes,
        "mode": "static_browser_verification_no_fresh_inference",
    }, indent=2) + "\n")
    shutil.copy2(HERE / "pages-index.html", output / "index.html")
    (output / ".nojekyll").write_text("")
    print(f"Built {len(hashes)} public app files at {app}")
    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".proofgate-pages")
    build_pages(parser.parse_args().output)
