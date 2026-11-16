#!/usr/bin/env python3
"""Assemble approved actual screenshots and offline narration; no invented UI.

Usage: python compose_video.py frames-manifest.json [--check]
Optional avatar footage is accepted only with explicit source/matching review
flags; this script never generates a face, animation, voice clone or lip sync.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import subprocess
import textwrap
from prepare_narration import duration, spoken

HERE = Path(__file__).resolve().parent
WORK = HERE / "render-work"
BOLD = "/usr/share/fonts/truetype/open-sans/OpenSans-Bold.ttf"
REGULAR = "/usr/share/fonts/truetype/open-sans/OpenSans-Regular.ttf"
FPS = 30


def run(args):
    subprocess.run(args, check=True)


def subtitle_time(value):
    millis = round(value * 1000)
    return f"{millis // 3600000:02}:{millis // 60000 % 60:02}:{millis // 1000 % 60:02},{millis % 1000:03}"


def caption_chunks(text):
    chunks, words = [], []
    for word in text.split():
        if words and (len(" ".join(words + [word])) > 112 or len(words) >= 17):
            chunks.append(" ".join(words)); words = []
        words.append(word)
        if word.endswith((".", "?", "!")):
            chunks.append(" ".join(words)); words = []
    if words:
        chunks.append(" ".join(words))
    return chunks


def caption_weight(text):
    normalized = spoken(text)
    return sum(max(1, len(re.sub(r"[^A-Za-z0-9]", "", word)) / 4.7) for word in normalized.split()) + 0.8 * len(re.findall(r"[.,;:]", normalized))


def source_path(value, base):
    path = Path(value)
    path = path if path.is_absolute() else base / path
    path = path.resolve()
    assert path.is_file(), f"Missing supplied source: {path}"
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text())
    narration = json.loads((HERE / "narration-manifest.json").read_text())
    assert manifest.get("evidence_reviewed") is True, "Root must review the actual frame sources first"
    scenes = manifest["scenes"]
    assert len(scenes) == 9 and [scene["paragraph"] for scene in scenes] == list(range(1, 10))
    avatar = None
    if manifest.get("avatar_clip"):
        assert manifest.get("avatar_source_reviewed") is True and manifest.get("avatar_matches_narration") is True, "Do not imply matching avatar speech without reviewing an actual supplied clip"
        avatar = source_path(manifest["avatar_clip"], manifest_path.parent)
        assert duration(avatar) >= narration["planned_final_seconds"], "Do not loop or stretch a short avatar clip"
    source_hashes = []
    for scene in scenes:
        assert isinstance(scene.get("mode_banner"), str) and 1 <= len(scene["mode_banner"]) <= 110
        if scene["paragraph"] in (2, 3):
            assert "saved evidence" in scene["mode_banner"].lower(), "Completed run must be labelled saved evidence"
        if scene["paragraph"] in (4, 5, 6, 7):
            assert "rehearsal" in scene["mode_banner"].lower(), "Simulated sequence must remain visibly labelled rehearsal"
        assert scene.get("frames"), "Supply actual captured frames; placeholders are never rendered"
        for frame in scene["frames"]:
            frame["resolved_path"] = source_path(frame["path"], manifest_path.parent)
            assert frame["resolved_path"].suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"), "Use actual screenshot images"
            frame["weight"] = float(frame.get("weight", 1))
            assert 0 < frame["weight"] < 10000
            source_hashes.append({"paragraph": scene["paragraph"], "file": str(frame["resolved_path"].relative_to(HERE)) if frame["resolved_path"].is_relative_to(HERE) else frame["resolved_path"].name, "sha256": hashlib.sha256(frame["resolved_path"].read_bytes()).hexdigest()})
    planned = sum(math.ceil(row["scene_seconds"] * FPS) / FPS for row in narration["scenes"])
    assert planned < 170, "No extra title/end-card time may exceed 2:50"
    if args.check:
        print(json.dumps({"ready_to_render": True, "planned_seconds": planned, "screenshots": len(source_hashes), "avatar": bool(avatar)}))
        return
    WORK.mkdir(exist_ok=True)
    videos, subtitles, offset = [], [], 0.0
    for scene, row in zip(scenes, narration["scenes"]):
        number = row["paragraph"]
        frames = scene["frames"]
        total_frames = math.ceil(row["scene_seconds"] * FPS)
        seconds = total_frames / FPS
        total_weight = sum(frame["weight"] for frame in frames)
        allocated = [max(1, round(total_frames * frame["weight"] / total_weight)) for frame in frames]
        allocated[-1] += total_frames - sum(allocated)
        assert allocated[-1] > 0
        args_ff = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        graph = []
        screen_width = 1660 if avatar else 1792
        screen_x = "20" if avatar else "(ow-iw)/2"
        for index, (frame, count) in enumerate(zip(frames, allocated)):
            args_ff += ["-loop", "1", "-framerate", str(FPS), "-i", str(frame["resolved_path"])]
            graph.append(f"[{index}:v]scale={screen_width}:760:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=1920:1080:{screen_x}:134:color=0x111D32,setsar=1,trim=duration={count / FPS:.8f},setpts=PTS-STARTPTS[v{index}]")
        labels = "".join(f"[v{i}]" for i in range(len(frames)))
        graph.append(f"{labels}concat=n={len(frames)}:v=1:a=0[main]")
        args_ff += ["-i", str(HERE / row["file"])]
        audio_index = len(frames)
        graph.append(f"[{audio_index}:a]apad=pad_dur=1,atrim=duration={seconds:.8f},asetpts=PTS-STARTPTS[audio]")
        banner = WORK / f"scene-{number:02}-banner.txt"
        banner.write_text(scene["mode_banner"])
        heading = WORK / "heading.txt"; heading.write_text("ProofPay Purchase Desk")
        editing = WORK / "editing.txt"; editing.write_text("Edited actual UI states · Synthetic narration")
        filters = [
            f"drawtext=fontfile={BOLD}:textfile={heading}:fontcolor=0xF4F7FF:fontsize=36:x=64:y=25",
            f"drawtext=fontfile={REGULAR}:textfile={editing}:fontcolor=0x9CB7DD:fontsize=22:x=1170:y=35",
            f"drawtext=fontfile={REGULAR}:textfile={banner}:fontcolor=0xA8C8FF:fontsize=27:x=64:y=81",
            "drawbox=x=64:y=920:w=1792:h=2:color=0x385478:t=fill",
        ]
        chunks = caption_chunks(row["text"])
        weights = [caption_weight(chunk) for chunk in chunks]
        local = 0.0
        for index, (chunk, weight) in enumerate(zip(chunks, weights)):
            end = local + row["seconds"] * weight / sum(weights)
            if index == len(chunks) - 1:
                end = seconds
            textfile = WORK / f"scene-{number:02}-caption-{index:02}.txt"
            lines = textwrap.wrap(chunk, width=75)
            assert len(lines) <= 2
            textfile.write_text("\n".join(lines))
            filters.append(f"drawtext=fontfile={BOLD}:textfile={textfile}:fontcolor=0xF4F7FF:fontsize=34:line_spacing=10:x=(w-text_w)/2:y=945:enable='gte(t,{local:.5f})*lt(t,{end:.5f})'")
            subtitles.append(f"{len(subtitles) + 1}\n{subtitle_time(offset + local)} --> {subtitle_time(offset + end)}\n" + "\n".join(lines) + "\n")
            local = end
        graph.append("[main]" + ",".join(filters) + "[captioned]")
        video_label = "captioned"
        if avatar:
            args_ff += ["-ss", f"{offset:.8f}", "-i", str(avatar)]
            avatar_index = audio_index + 1
            graph.append(f"[{avatar_index}:v]scale=200:600:force_original_aspect_ratio=decrease:force_divisible_by=2,trim=duration={seconds:.8f},setpts=PTS-STARTPTS[avatar]")
            graph.append(f"[captioned][avatar]overlay=x=1700:y=336:shortest=1,drawtext=fontfile={REGULAR}:text='Synthetic presenter':fontcolor=0xC3D3EC:fontsize=18:x=1700:y=308[withavatar]")
            video_label = "withavatar"
        output = WORK / f"scene-{number:02}.mp4"
        args_ff += ["-filter_complex", ";".join(graph), "-map", f"[{video_label}]", "-map", "[audio]", "-t", f"{seconds:.8f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-threads", "2", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(output)]
        print(f"Rendering paragraph {number}: {seconds:.2f}s", flush=True)
        run(args_ff)
        videos.append(output); offset += seconds
    concat = WORK / "video-parts.txt"
    concat.write_text("".join(f"file '{video}'\n" for video in videos))
    output = HERE / "proofpay-narrated-review-cut.mp4"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(output)])
    actual_duration = duration(output)
    assert actual_duration < 170, "Rendered video exceeds the 2:50 limit"
    (HERE / "captions.srt").write_text("\n".join(subtitles))
    (HERE / "video-source-manifest.json").write_text(json.dumps({"seconds": actual_duration, "source_frames": source_hashes, "avatar": str(avatar.relative_to(HERE)) if avatar and avatar.is_relative_to(HERE) else avatar.name if avatar else None, "caption_timing": "Estimated from speech lengths; listening review is required before final publication", "status": "Review cut, not published"}, indent=2) + "\n")
    print(f"Review cut ready: {output}, {actual_duration:.3f}s. Review caption timing and voice before publication.")


if __name__ == "__main__":
    main()
