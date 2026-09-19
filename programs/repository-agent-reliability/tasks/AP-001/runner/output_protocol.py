from __future__ import annotations

import hashlib


PROTOCOLS = {
    "none": "",
    "strict-code-only-v1": (
        "RARB MACHINE OUTPUT PROTOCOL: strict-code-only-v1\n"
        "Your entire response MUST be the complete raw Python source for "
        "app/resource_view.py.\n"
        "Do not use Markdown code fences.\n"
        "Do not include prose, headings, explanations, notes, or commentary.\n"
        "Do not include a filename label.\n"
        "Return exactly one Python file and nothing else.\n"
    ),
}


def protocol_text(name: str) -> str:
    if name not in PROTOCOLS:
        raise ValueError(f"Unknown output protocol: {name}")
    return PROTOCOLS[name]


def protocol_sha256(name: str) -> str:
    return hashlib.sha256(protocol_text(name).encode("utf-8")).hexdigest()
