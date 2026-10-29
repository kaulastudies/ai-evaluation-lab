"""Compose an explicitly captioned walkthrough from real browser screenshots."""
from pathlib import Path
import subprocess
import textwrap

ROOT = Path(__file__).resolve().parent
scenes = [
    ("01-intro", 10, "A green test is not the whole contract", "ProofGate helps engineers review coding-agent patches.\n\nThese are actual browser executions, shown as a captioned walkthrough. No fresh model inference is shown."),
    ("02-false-green", 15, "Ordinary tests miss the defect", "This recorded Ollama candidate passes the public test.\n\nThe independent verifier rejects it: all four contract gates fail.\n\nThe browser executed the Python checks."),
    ("03-repair", 12, "The same contract checks the repair", "The recorded bounded Ollama repair passes the public test and all four gates.\n\nThe verdict comes from execution, not a stored success animation."),
    ("04-zero-mutation", 12, "One subtle change. One failed gate.", "Change numeric zero to None.\n\nOrdinary tests still pass. The independent edge-case gate, AP005-G02, fails.\n\nThe other three gates pass."),
    ("05-controls", 16, "Test the verifier before trusting it", "The reference passes.\n\nThe known-bad control and all four mutations fail.\n\nAll six pass the public test. These controls qualify the verifier for these specific faults."),
    ("06-nemotron", 16, "NVIDIA Nemotron, served by Nebius", "This is a real archived candidate generated with Nemotron 3 Super on Nebius Token Factory.\n\nIt passes two public tests and all three AP-001 gates when executed here."),
    ("07-nebius-ledger", 14, "Keep the evidence, including failures", "The full ledger preserves 52 attempts, including failures and HOLDs.\n\nEleven Nebius records include a pilot and ten fixed Phase 12 trials. This is a bounded study, not a model ranking."),
    ("08-runtime", 14, "Reproduce it. Then generate again.", "The local workbench supports full historical replay and new Nebius generation or bounded repair.\n\nNew inference requires a server-side key. The new repair route still needs a live-service run.\n\nOpen source: Apache 2.0."),
]

def run(args):
    subprocess.run(args, check=True)

out = ROOT / "renders"
out.mkdir(exist_ok=True)
font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
for i, (name, duration, heading, body) in enumerate(scenes, 1):
    title = out / f"{i}-heading.txt"
    copy = out / f"{i}-body.txt"
    title.write_text("\n".join(textwrap.wrap(heading, 24)))
    copy.write_text("\n\n".join("\n".join(textwrap.wrap(p, 30)) for p in body.split("\n\n")))
    filters = (
        "[0:v]scale=1348:926,pad=1920:1080:24:116:color=0x152c3a,"
        f"drawtext=fontfile={font}:text='ProofGate / Independent verification for coding agents':x=32:y=35:fontsize=40:fontcolor=white,"
        f"drawtext=fontfile={font}:text='With mentorship from Prof. Nithya Ravi Kumar':x=35:y=89:fontsize=19:fontcolor=0xa9e4c4,"
        f"drawtext=fontfile={font}:textfile={title}:x=1410:y=145:fontsize=32:fontcolor=0x9be1bc:line_spacing=10,"
        f"drawtext=fontfile={font}:textfile={copy}:x=1410:y=335:fontsize=27:fontcolor=white:line_spacing=10,"
        f"drawtext=fontfile={font}:text='{i:02d} / 09  -  Actual UI captures':x=1410:y=1015:fontsize=22:fontcolor=0xb7c7ce[v]"
    )
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-loop", "1", "-framerate", "15", "-i", str(ROOT / "captures" / f"{name}.jpg"), "-filter_complex", filters, "-map", "[v]", "-t", str(duration), "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "20", "-pix_fmt", "yuv420p", str(out / f"{i}.mp4")])
run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-loop", "1", "-framerate", "15", "-i", str(ROOT / "proofgate-video-credits.png"), "-t", "10", "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "20", "-pix_fmt", "yuv420p", str(out / "9.mp4")])
listing = out / "concat.txt"
listing.write_text("\n".join(f"file '{out / f'{i}.mp4'}'" for i in range(1, len(scenes) + 2)))
destination = ROOT / "proofgate-walkthrough.mp4"
run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", "-movflags", "+faststart", str(destination)])
print(f"Created {destination}: {sum(s[1] for s in scenes) + 10} seconds")
