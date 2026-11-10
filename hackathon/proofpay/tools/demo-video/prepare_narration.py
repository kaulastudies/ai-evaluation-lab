#!/usr/bin/env python3
"""Offline flite narration. No API, network, avatar generation or voice cloning."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "DEMO_SCRIPT.md"
MAX_FINAL_SECONDS = 170
SCENE_PADDING = 0.45
APPROVED_TEMPO = 0.85282901


def command(args):
    subprocess.run(args, check=True)


def duration(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], check=True, capture_output=True, text=True)
    return float(result.stdout.strip())


def spoken(text):
    # Caption text remains the exact supplied script. These spellings only guide
    # the installed US English voice through brand names and initialisms.
    for original, pronunciation in [
        ("ProofPay", "Proof Pay"), ("PayPal", "Pay Pal"),
        ("OpenAI", "Open A. I."), ("GPT", "G. P. T."),
        ("Vercel", "Ver sell"), ("PostgreSQL", "Post gres queue ell"),
    ]:
        text = text.replace(original, pronunciation)
    text = re.sub(r"\bAI\b", "A. I.", text)
    text = re.sub(r"\bUS\b", "U. S.", text)
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", type=Path, default=SCRIPT, help="Approved Markdown script containing the exact narration text block")
    parser.add_argument("--paragraph", type=int, choices=range(1, 10), help="Regenerate only this narration WAV, preserving the current tempo and other WAVs")
    args = parser.parse_args()
    for name in ("narration", "text", "render-work"):
        (HERE / name).mkdir(exist_ok=True)
    script_path = args.script.resolve()
    source = script_path.read_text()
    block = re.search(r"```text\n(.*?)\n```", source, re.S).group(1)
    # Release owner's explicit update after the new 210-check run. This also
    # permits the approved correction while the source document is being synced.
    block = block.replace("one hundred ninety nine local checks", "two hundred ten local checks")
    paragraphs = [part.strip() for part in block.split("\n\n") if part.strip()]
    assert len(paragraphs) == 9, "Expected the approved nine-paragraph script"
    assert len(block.split()) == 347, "The approved narration text has changed; review before synthesis"
    prior = json.loads((HERE / "narration-manifest.json").read_text()) if args.paragraph else None
    (HERE / "narration-exact-script.txt").write_text(block + "\n")
    rows = []
    for index, paragraph in enumerate(paragraphs, 1):
        if prior and index != args.paragraph:
            row = prior["scenes"][index - 1]
            assert row["text"] == paragraph, "Another paragraph changed; do not silently reuse its old audio"
            rows.append(row)
            continue
        raw = HERE / "render-work" / f"raw-{index:02}.wav"
        textfile = HERE / "text" / f"scene-{index:02}-spoken.txt"
        textfile.write_text(spoken(paragraph))
        (HERE / "text" / f"scene-{index:02}-exact.txt").write_text(paragraph)
        command(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"flite=textfile={textfile}:voice=slt", "-c:a", "pcm_s16le", str(raw)])
        rows.append({"paragraph": index, "word_count": len(paragraph.split()), "text": paragraph, "spoken_text": spoken(paragraph), "raw_seconds": duration(raw)})
    raw_total = sum(row["raw_seconds"] for row in rows)
    # Preserve the reviewed narration cadence for this exact approved script.
    # Pitch stays unchanged; frame padding keeps the film below 170 seconds.
    tempo = prior["tempo"] if prior else APPROVED_TEMPO
    assert tempo <= 1.18, "Timing needs a script/editor decision; do not rush the voice further"
    elapsed = 0.0
    for row in rows:
        index = row["paragraph"]
        wav = HERE / "narration" / f"scene-{index:02}.wav"
        if not prior or index == args.paragraph:
            command(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(HERE / "render-work" / f"raw-{index:02}.wav"),
                     "-af", f"atempo={tempo:.8f},loudnorm=I=-18:TP=-2:LRA=7,aresample=48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)])
        seconds = duration(wav)
        row.update({"file": str(wav.relative_to(HERE)), "seconds": seconds, "start_seconds": round(elapsed, 3), "scene_seconds": round(seconds + SCENE_PADDING, 3)})
        elapsed += seconds + SCENE_PADDING
    assert elapsed <= MAX_FINAL_SECONDS
    manifest = {
        "status": "Offline fallback preparation; not a published or final video",
        "voice": "flite slt, installed generic synthetic US English voice; no clone",
        "source_script": script_path.name, "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "exact_word_count": 347, "approved_revision": "Paragraph 8: two hundred ten local checks, per release owner's updated test evidence", "paragraphs": 9, "tempo": round(tempo, 8),
        "raw_speech_seconds": round(raw_total, 3),
        "narration_seconds": round(sum(row["seconds"] for row in rows), 3),
        "planned_final_seconds": round(elapsed, 3), "scene_padding_seconds": SCENE_PADDING,
        "quality_limits": [
            "The installed concatenative voice sounds more mechanical than a commercial narrator.",
            "Phonetic spellings guide brand names/initialisms; captions retain the exact approved words.",
            "No human listening approval is implied by duration or signal checks.",
            "This narration script creates audio only; the separate presenter renderer maps actual phoneme timings to original SVG artwork.",
        ],
        "scenes": rows,
    }
    (HERE / "narration-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    concat = HERE / "render-work" / "narration-parts.txt"
    # A listening preview includes the same scene pauses as the compositor.
    for row in rows:
        index = row["paragraph"]
        command(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(HERE / row["file"]), "-af", f"apad=pad_dur={SCENE_PADDING}", "-c:a", "pcm_s16le", str(HERE / "render-work" / f"padded-{index:02}.wav")])
    concat.write_text("".join(f"file '{HERE / 'render-work' / ('padded-' + str(row['paragraph']).zfill(2) + '.wav')}'\n" for row in rows))
    command(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c:a", "pcm_s16le", str(HERE / "narration-preview.wav")])
    command(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(HERE / "narration-preview.wav"), "-c:a", "libmp3lame", "-b:a", "128k", str(HERE / "narration-preview.mp3")])
    print(json.dumps({"scenes": [{"paragraph": row["paragraph"], "file": row["file"], "seconds": row["seconds"]} for row in rows], "narration_seconds": manifest["narration_seconds"], "planned_final_seconds": manifest["planned_final_seconds"], "tempo": manifest["tempo"]}, indent=2))


if __name__ == "__main__":
    main()
