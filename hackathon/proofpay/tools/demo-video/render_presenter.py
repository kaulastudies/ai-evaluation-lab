#!/usr/bin/env python3
"""Original vector presenter with phoneme-driven visemes, rendered offline.

The artwork is newly authored for this project, not a likeness of a real person.
Mouth state uses Flite Segment timing, never audio amplitude. No face model,
photo, subscription, remote service, voice cloning or learned lip-sync is used.
"""
from pathlib import Path
import bisect
import json
import math
import subprocess
from prepare_narration import duration

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "presenter-assets"
FPS = 30
VISEMES = ("REST", "MBP", "FV", "TH", "L", "AA", "E", "O", "U", "S", "CH", "R")
PHONE_MAP = {
    "pau": "REST", "m": "MBP", "b": "MBP", "p": "MBP", "f": "FV", "v": "FV",
    "th": "TH", "dh": "TH", "l": "L", "aa": "AA", "ae": "AA", "ah": "AA", "ax": "AA", "hh": "AA",
    "eh": "E", "ey": "E", "ih": "E", "iy": "E", "y": "E", "ao": "O", "uh": "U", "uw": "U", "w": "U",
    "s": "S", "z": "S", "t": "S", "d": "S", "n": "S", "k": "S", "g": "S", "ng": "S",
    "ch": "CH", "jh": "CH", "sh": "CH", "zh": "CH", "r": "R", "er": "R",
}
DIPHTHONGS = {"aw": ("AA", "U"), "ay": ("AA", "E"), "oy": ("O", "E"), "ow": ("O", "U")}


def mouth(viseme):
    if viseme == "REST":
        return '<path d="M181 265 Q200 274 219 265" fill="none" stroke="#8d4e45" stroke-width="3.5" stroke-linecap="round"/>'
    if viseme == "MBP":
        return '<path d="M179 266 Q200 260 221 266 Q200 273 179 266Z" fill="#b16c60"/><path d="M180 266 Q200 267 220 266" fill="none" stroke="#79443d" stroke-width="2" stroke-linecap="round"/>'
    width, height = {"FV": (22, 7), "TH": (19, 9), "L": (22, 13), "AA": (24, 18), "E": (26, 11), "O": (14, 18), "U": (10, 13), "S": (21, 6), "CH": (16, 12), "R": (17, 12)}[viseme]
    shape = f'<ellipse cx="200" cy="267" rx="{width}" ry="{height}"/>'
    teeth = '<rect x="170" y="247" width="60" height="15" rx="3" fill="#fff5e6"/>' if viseme in ("FV", "TH", "L", "AA", "E", "S", "CH") else ""
    tongue = '<ellipse cx="200" cy="279" rx="15" ry="6" fill="#d8918b"/>'
    if viseme == "L": tongue = '<path d="M188 280 Q193 255 201 258 Q209 260 212 280Z" fill="#d8918b"/>'
    if viseme == "TH": tongue = '<ellipse cx="200" cy="272" rx="11" ry="5" fill="#dfa09a"/>'
    if viseme == "FV": tongue = '<path d="M175 273 Q200 263 225 273" stroke="#bc7768" stroke-width="5" fill="none"/>'
    return f'<defs><clipPath id="mouth-clip">{shape}</clipPath></defs><g fill="#4d2930" stroke="#8d4e45" stroke-width="2">{shape}</g><g clip-path="url(#mouth-clip)">{teeth}{tongue}</g>'


def avatar_svg(viseme="REST", blink=False):
    eyes = '<path d="M146 207 Q164 218 182 207 M218 207 Q236 218 254 207" fill="none" stroke="#56372f" stroke-width="3.5" stroke-linecap="round"/>' if blink else '''
      <path d="M145 208 Q164 193 183 208 Q164 221 145 208Z M217 208 Q236 193 255 208 Q236 221 217 208Z" fill="#fff8ed"/>
      <circle cx="166" cy="208" r="7" fill="#403d40"/><circle cx="234" cy="208" r="7" fill="#403d40"/>
      <circle cx="168" cy="206" r="2" fill="#fff"/><circle cx="236" cy="206" r="2" fill="#fff"/>
      <path d="M145 207 Q164 193 183 207 M217 207 Q236 193 255 207" fill="none" stroke="#56372f" stroke-width="2.5" stroke-linecap="round"/>'''
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="560" viewBox="0 0 400 560">
    <defs><linearGradient id="back" x2="0" y2="1"><stop stop-color="#1c3554"/><stop offset="1" stop-color="#13243c"/></linearGradient><linearGradient id="coat" x2="1" y2="1"><stop stop-color="#4b6f94"/><stop offset="1" stop-color="#2c496d"/></linearGradient></defs>
    <rect width="400" height="560" rx="26" fill="url(#back)"/>
    <circle cx="200" cy="232" r="155" fill="#2b4d70" opacity=".45"/>
    <text x="28" y="43" font-family="Open Sans,sans-serif" font-size="22" font-weight="700" fill="#f0f6ff">ProofPay</text>
    <text x="28" y="63" font-family="Open Sans,sans-serif" font-size="10" letter-spacing="1.5" fill="#a8c8e7">SYNTHETIC PRESENTER</text>
    <path d="M102 196 C98 119 136 85 199 84 C272 84 301 133 298 207 L285 335 Q200 371 110 332Z" fill="#24313d"/>
    <path d="M176 284 L224 284 L232 345 Q200 370 168 345Z" fill="#c99170"/>
    <path d="M176 292 Q201 317 224 293 L224 314 Q199 330 176 313Z" fill="#af775b" opacity=".55"/>
    <ellipse cx="120" cy="217" rx="13" ry="22" fill="#c99170"/><ellipse cx="280" cy="217" rx="13" ry="22" fill="#c99170"/>
    <ellipse cx="200" cy="207" rx="78" ry="98" fill="#d6a07e"/>
    <path d="M122 185 C115 121 154 97 201 98 C253 98 282 130 279 177 C251 164 223 133 213 119 C196 155 162 174 122 185Z" fill="#24313d"/>
    <path d="M127 180 Q142 173 157 161" fill="none" stroke="#43505c" stroke-width="4" stroke-linecap="round"/>
    <path d="M145 188 Q163 179 181 189 M219 189 Q237 179 255 188" fill="none" stroke="#43392f" stroke-width="5" stroke-linecap="round"/>
    {eyes}
    <path d="M199 211 L192 238 Q200 243 208 237" fill="none" stroke="#b47c60" stroke-width="2.5" stroke-linecap="round"/>
    <ellipse cx="151" cy="244" rx="15" ry="7" fill="#cd8977" opacity=".33"/><ellipse cx="249" cy="244" rx="15" ry="7" fill="#cd8977" opacity=".33"/>
    {mouth(viseme)}
    <circle cx="117" cy="234" r="4" fill="#72c4c2"/><circle cx="283" cy="234" r="4" fill="#72c4c2"/>
    <path d="M170 333 L137 345 Q72 357 58 415 L43 503 L357 503 L342 415 Q328 359 264 345 L230 333 Q201 356 170 333Z" fill="url(#coat)"/>
    <path d="M175 333 Q200 355 225 333 L241 503 L159 503Z" fill="#e5eef4"/>
    <path d="M168 335 L145 350 L167 388 L151 405 L179 489 M232 335 L255 350 L233 388 L249 405 L221 489" fill="none" stroke="#6283a5" stroke-width="3" stroke-linejoin="round"/>
    <path d="M195 350 L205 350 L213 420 L200 435 L187 420Z" fill="#399f9f"/>
    <path d="M99 423 L90 497 M301 423 L310 497" fill="none" stroke="#243e5d" stroke-width="3" stroke-linecap="round"/>
    <rect x="269" y="402" width="27" height="27" rx="8" fill="#457eed"/><path d="M276 415 L281 420 L290 410" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    <rect x="0" y="503" width="400" height="57" fill="#122239"/>
    <text x="200" y="533" text-anchor="middle" font-family="Open Sans,sans-serif" font-size="17" fill="#f0f6ff">ProofPay narrator</text>
    <text x="200" y="550" text-anchor="middle" font-family="Open Sans,sans-serif" font-size="10" fill="#9bb5d4">Original illustration · Offline speech</text>
    </svg>'''
    return "\n".join(line.rstrip() for line in svg.splitlines())


def viseme_at(segment, time):
    phone = segment["phone"]
    if phone in DIPHTHONGS:
        return DIPHTHONGS[phone][int(time >= (segment["start"] + segment["end"]) / 2)]
    return PHONE_MAP[phone]


def main():
    timeline = json.loads((HERE / "phoneme-timeline.json").read_text())
    segments = [segment for scene in timeline["scenes"] for segment in scene["segments"]]
    assert all(scene["identical_pcm"] for scene in timeline["scenes"])
    assert all(segment["phone"] in PHONE_MAP or segment["phone"] in DIPHTHONGS for segment in segments)
    ASSETS.mkdir(exist_ok=True)
    images = {}
    for viseme in VISEMES:
        for blink in (False, True):
            stem = f"{viseme.lower()}-{'blink' if blink else 'open'}"
            svg, png = ASSETS / f"{stem}.svg", ASSETS / f"{stem}.png"
            svg.write_text(avatar_svg(viseme, blink))
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(svg), "-frames:v", "1", str(png)], check=True)
            images[(viseme, blink)] = png.read_bytes()
    (HERE / "presenter-original.svg").write_text(avatar_svg())
    total_frames = math.ceil(timeline["duration"] * FPS)
    output = HERE / "presenter-phoneme-silent.mp4"
    encoder = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-i", "pipe:0", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-threads", "2", "-movflags", "+faststart", str(output)], stdin=subprocess.PIPE)
    starts = [segment["start"] for segment in segments]
    used, counts = set(), {}
    try:
        for frame in range(total_frames):
            time = (frame + .5) / FPS
            index = bisect.bisect_right(starts, time) - 1
            segment = segments[index] if index >= 0 else None
            viseme = viseme_at(segment, time) if segment and time < segment["end"] else "REST"
            blink = 0 <= (time - 2.7) % 4.9 < .13
            used.add(viseme); counts[viseme] = counts.get(viseme, 0) + 1
            encoder.stdin.write(images[(viseme, blink)])
    finally:
        encoder.stdin.close()
    assert encoder.wait() == 0
    # Preview only: first paragraph, with the matching already-produced voice.
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(output), "-i", str(HERE / "narration/scene-01.wav"), "-t", str(duration(HERE / "narration/scene-01.wav")), "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(HERE / "presenter-preview.mp4")], check=True)
    report = {"duration": total_frames / FPS, "frames": total_frames, "fps": FPS, "phoneme_segments": len(segments), "visemes_used": sorted(used), "viseme_frame_counts": counts, "input_pcm_matches_narration": True, "amplitude_driven": False, "likeness": "Original generic illustrated person, not a real person", "method": "Flite Segment timing to explicit vector mouth shapes, including diphthong transitions; deterministic eye blinks are separate"}
    (HERE / "presenter-validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
