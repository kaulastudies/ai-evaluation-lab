from __future__ import annotations

import hashlib
import json
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = ["verifier/**", "controls/**", "evidence/**"]


def read_lf(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def build_context() -> dict:
    visible = {
        "brief": TASK_ROOT / "agent_brief.md",
        "source": TASK_ROOT / "fixture" / "app" / "resource_view.py",
        "public_test": TASK_ROOT / "fixture" / "tests" / "public" / "test_resource_view.py",
    }

    payload = {
        "task_id": "AP-001",
        "visible_files": {},
        "explicitly_excluded": EXCLUDED,
    }

    for name, path in visible.items():
        content = read_lf(path)
        payload["visible_files"][name] = {
            "path": path.relative_to(TASK_ROOT).as_posix(),
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "content": content,
        }

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    payload["context_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def main() -> int:
    print(json.dumps(build_context(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
