#!/usr/bin/env python3
"""Read actual Flite Segment relations and verify matching synthesized PCM.

API references: festvox/flite include/flite.h and main/flite_main.c print_info.
Uses installed libflite + cmu_us_slt through ctypes; no network or API service.
"""
import ctypes as C
import argparse
from pathlib import Path
import hashlib
import json
import math
import subprocess
import sys
import wave

HERE = Path(__file__).resolve().parent


def pcm(path):
    with wave.open(str(path), "rb") as audio:
        return audio.getframerate(), audio.getnchannels(), audio.getsampwidth(), audio.readframes(audio.getnframes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paragraph", type=int, choices=range(1, 10))
    args = parser.parse_args()
    data = json.loads((HERE / "narration-manifest.json").read_text())
    if not args.paragraph:
        # ffmpeg's nine narration jobs each started a fresh Flite process. Keep
        # that same initialization boundary, including the engine's noise state.
        scenes = []
        for index in range(1, 10):
            subprocess.run([sys.executable, str(Path(__file__).resolve()), "--paragraph", str(index)], check=True)
            scenes.append(json.loads((HERE / "render-work" / f"phoneme-scene-{index:02}.json").read_text()))
        result = {"method": "Actual Flite Segment phoneme names/end times; source PCM verified identical to narration synthesis; times scaled for audio tempo processing", "voice": "cmu_us_slt", "fps": 30, "duration": sum(scene["scene_seconds"] for scene in scenes), "scenes": scenes}
        (HERE / "phoneme-timeline.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"paragraphs": len(scenes), "segments": sum(len(scene["segments"]) for scene in scenes), "all_pcm_identical": True, "duration": result["duration"], "phonemes": sorted({segment["phone"] for scene in scenes for segment in scene["segments"]})}, indent=2))
        return
    flite = C.CDLL("libflite.so.1", mode=C.RTLD_GLOBAL)
    voice_library = C.CDLL("libflite_cmu_us_slt.so.1", mode=C.RTLD_GLOBAL)
    api = {
        "flite_init": ([], C.c_int),
        "flite_synth_text": ([C.c_char_p, C.c_void_p], C.c_void_p),
        "utt_relation": ([C.c_void_p, C.c_char_p], C.c_void_p),
        "relation_head": ([C.c_void_p], C.c_void_p),
        "item_next": ([C.c_void_p], C.c_void_p),
        "item_feat_string": ([C.c_void_p, C.c_char_p], C.c_char_p),
        "item_feat_float": ([C.c_void_p, C.c_char_p], C.c_float),
        "utt_wave": ([C.c_void_p], C.c_void_p),
        "cst_wave_save_riff": ([C.c_void_p, C.c_char_p], C.c_int),
        "delete_utterance": ([C.c_void_p], None),
    }
    for name, (argument_types, result) in api.items():
        method = getattr(flite, name); method.argtypes = argument_types; method.restype = result
    voice_library.register_cmu_us_slt.argtypes = [C.c_char_p]
    voice_library.register_cmu_us_slt.restype = C.c_void_p
    flite.flite_init()
    voice = voice_library.register_cmu_us_slt(None)
    assert voice
    scenes, offset = [], 0.0
    for row in data["scenes"]:
        if row["paragraph"] != args.paragraph:
            offset += math.ceil(row["scene_seconds"] * 30) / 30
            continue
        utterance = flite.flite_synth_text(row["spoken_text"].encode(), voice)
        assert utterance
        try:
            check_path = HERE / "render-work" / f"phoneme-reference-{row['paragraph']:02}.wav"
            assert flite.cst_wave_save_riff(flite.utt_wave(utterance), str(check_path).encode()) == 0
            expected = pcm(HERE / "render-work" / f"raw-{row['paragraph']:02}.wav")
            actual = pcm(check_path)
            assert actual == expected, f"Paragraph {row['paragraph']} PCM differs; do not claim alignment to a different waveform"
            raw_seconds = len(actual[3]) / actual[0] / actual[1] / actual[2]
            ratio = row["seconds"] / raw_seconds
            item = flite.relation_head(flite.utt_relation(utterance, b"Segment"))
            segments, start = [], 0.0
            while item:
                phone = flite.item_feat_string(item, b"name").decode()
                end = float(flite.item_feat_float(item, b"end"))
                assert start <= end <= raw_seconds + 0.05
                segments.append({"phone": phone, "raw_start": start, "raw_end": end,
                                 "start": round(offset + start * ratio, 6), "end": round(offset + end * ratio, 6)})
                start = end; item = flite.item_next(item)
            assert segments
            scene_seconds = math.ceil(row["scene_seconds"] * 30) / 30
            scenes.append({"paragraph": row["paragraph"], "start": offset, "scene_seconds": scene_seconds,
                           "pcm_sha256": hashlib.sha256(actual[3]).hexdigest(), "identical_pcm": True,
                           "raw_seconds": raw_seconds, "processed_seconds": row["seconds"], "timing_scale": ratio,
                           "segments": segments})
            offset += scene_seconds
        finally:
            flite.delete_utterance(utterance)
    (HERE / "render-work" / f"phoneme-scene-{args.paragraph:02}.json").write_text(json.dumps(scenes[0], indent=2) + "\n")


if __name__ == "__main__":
    main()
