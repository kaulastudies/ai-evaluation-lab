# ProofPay narrated product demo

This source reproduces a 2:21 product walkthrough with local Kokoro neural narration and reviewed captures of the actual ProofPay portal. The composition uses focused views of existing screenshots, timed captions and quiet mode labels. It does not create interface states or imply a continuous screen recording.

The fresh guest walkthrough uses isolated simulated payments. Scene 6 separately shows a saved, completed GPT-4.1-mini proposal and PayPal sandbox purchase with virtual funds. No model or payment API is called by this video pipeline. The application receipt is an unsigned record, not a PayPal attestation.

The reviewed film replaces the earlier Flite/illustrated-presenter cut. [Watch the public V2 video](https://youtu.be/D4UXBT-FhcE). YouTube Studio confirmed Published/Public on 8 November 2026, and watch-page playback displayed 2:21. The source here has no publishing, upload, browser or submission function.

All 43 burned-in captions are included in the published film. The exact native transcript was saved for YouTube automatic timing; public selectable captions were unavailable at the first watch-page check and remain processing. Native-caption timing QA is not claimed. No independent listening or forced-alignment result is claimed. Narration was generated locally with the free Kokoro `af_heart` preset; the film uses no avatar or paid narration service.

## Inputs and outputs

| File | Purpose |
| --- | --- |
| `narration-v2-exact.txt` | Exact approved narration: 312 words, eight paragraphs |
| `frames-v2.json` | Reviewed edit: 29 timed shots from 14 actual screenshots |
| `frames-v2.template.json` | Unreviewed capture plan for adaptation |
| `FRAMES_SHA256SUMS.txt` | Integrity fingerprints of the reviewed screenshot inputs |
| `MODELS_SHA256SUMS.txt` | Integrity fingerprints of the locally downloaded model assets |
| `synthesize_story.py` | Stock `af_heart` voice at speed 0.94 using local CPU inference |
| `align_captions.py` | Exact words mapped to the model's returned phoneme timeline |
| `compose_portal.py` | Local FFmpeg composition and SRT output |
| `validate_video_v2.py` | Decode, timing, audio peak and subtitle checks; review frame extraction |
| `offline_guard.py` | Additional Linux process network restriction before native inference imports |

The 14 reviewed actual screenshots are included under `frames/`, so the relative paths in the shot plan resolve in this checkout. Models, generated audio/video, virtual environments and fonts are excluded from Git. To make a different demonstration, capture and review your own actual states, update the shot plan and narration, and review all resulting claims. Do not set `evidence_reviewed` to true before inspecting replacement frames.

## Reproduce locally

The reviewed environment used Python 3.12 on Linux, `libseccomp.so.2`, FFmpeg/ffprobe with libx264, AAC and drawtext, and Open Sans at `/usr/share/fonts/truetype/open-sans/`. Those dependencies must already be installed. The guard intentionally fails closed on unsupported hosts. Run the scripts as dedicated processes, not from an interactive notebook: the guard closes inherited non-stdio file descriptors and is irreversible for that process and its descendants.

Create an isolated environment and install the pinned Python dependencies before offline inference:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
```

Download the two assets separately from the public upstream release. These commands access the network for setup; inference does not download anything:

```sh
mkdir -p models
curl --fail --location --proto '=https' --tlsv1.2 \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx \
  --output models/kokoro-v1.0.onnx
curl --fail --location --proto '=https' --tlsv1.2 \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin \
  --output models/voices-v1.0.bin
sha256sum --check MODELS_SHA256SUMS.txt
```

The 14 reviewed screenshots already use their original filenames in `frames/`. Run from this directory:

```sh
sha256sum --check FRAMES_SHA256SUMS.txt
.venv/bin/python synthesize_story.py
.venv/bin/python align_captions.py
python3 compose_portal.py frames-v2.json --check
python3 compose_portal.py frames-v2.json
python3 validate_video_v2.py
```

The result is `proofpay-v2-review-cut.mp4`, `proofpay-v2-captions.srt`, a contact sheet, full-size review frames and JSON validation reports. `--paragraph 6` on the compositor renders just that scene for review. Composition only needs FFmpeg, the supplied screenshots and the generated narration/timing files; it does not load Kokoro.

If using the archived reviewed narration files, copy `narration-v2/`, `narration-v2-manifest.json` and `caption-alignment.json` into this directory and skip both inference commands. This permits fully local recomposition without downloading the model or installing inference dependencies. Fresh inference or a different FFmpeg/font build may produce different bytes; compare content and validation results rather than expecting the same MP4 hash.

## Editing and verification

Each crop selects existing source pixels. Crops use integer `x`, `y`, `width`, `height` coordinates. Shots can specify increasing `start_seconds` starting at zero, or proportional weights. Every shot must last at least one second. Optional emphasis is either a thin outline or a 1.5% source-pixel zoom. It cannot fabricate UI values, change recorded amounts or imply unrecorded actions.

Scene 6 is labelled saved AI + PayPal evidence. Other scenes remain simulated rehearsal. Caption timing comes from the model's phoneme durations, checked against the identical local phonemizer; it is not independent forced alignment. Technical checks do not replace listening and visual review.

`REVIEW.md` records the frozen cut and independent sample review. The application checks and payment evidence are separate from video-production checks. A video validation pass does not certify payment security or production readiness.

## Offline and license boundary

The final narration was generated with a process-local seccomp restriction installed before ONNX/Kokoro imports, inherited non-stdio descriptors closed, and native socket/connect tests returning `EPERM`. ONNX telemetry is also disabled through its documented API. The filter adds restrictions; it does not change host protections. It does not sandbox arbitrary model code against all local file access. Use the documented trusted inputs.

Earlier attempts triggered rejected telemetry connections; their delivery and payload are unknown. They are not described as completed offline runs. See `LICENSE_REVIEW.md` for the complete technical record and publisher links.

Original pipeline code is MIT-licensed under `LICENSE`. Kokoro weights/reference code are Apache-2.0; kokoro-onnx is MIT. Upstream license texts and model/voice cards are in `licenses/`. Python dependencies and system fonts retain their own licenses. The supplied captures contain ProofPay interface content and third-party product names, logos and sandbox identifiers; those marks remain their owners’ property and are not relicensed as part of the original pipeline code. The stock English preset does not clone the founder or any identified person. No paid narration service or personal OpenAI credits were used for this film.

## YouTube publication

Public watch link: **https://youtu.be/D4UXBT-FhcE**. Publication and watch-page playback were verified on 8 November 2026. The following title/description text is retained as the prepared publication copy; this section does not claim a separate exact-text comparison with the published fields. The video URL was saved and reopened in Devpost, where the embedded player showed the correct title. The final page remains Draft (3/5 steps), and final Submit stays held.

**Title**

ProofPay: approve purchases and resolve uncertain payments | PayPal AI Hackathon

**Description**

A missing payment response should not leave a small team guessing what it can spend.

ProofPay keeps a purchase, its owner approval, shared allowance and payment outcome together. This walkthrough shows a request reserving $180, a competing request blocked by the remaining allowance, and an uncertain payment resolved by checking its original order.

Try the public portal: https://proofpay-evaluation-lab.vercel.app

Source and project documentation: https://github.com/kaulastudies/ai-evaluation-lab/tree/proofpay/purchase-desk-v0.1/hackathon/proofpay

Most scenes show an isolated guest rehearsal with simulated payments. The separately labelled saved evidence shows a completed GPT-4.1-mini proposal and PayPal sandbox purchase using $180 in virtual funds. The film is an edited walkthrough of actual captured states, not a continuous recording or a new live payment.

Receipts are unsigned application records. Six browser scenario observations and 210 local automated checks are separate from the saved external payment evidence. This is a hackathon prototype, not a production payment service or a claim of PayPal endorsement.

Narration was generated locally with the open-source Kokoro-82M model and its stock af_heart voice. No paid narration service or personal OpenAI API credits were used for the film. The reproducible production source and license notices are included in the repository.
