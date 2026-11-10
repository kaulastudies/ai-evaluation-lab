# Free offline ProofPay demo video

This directory contains the source for the reviewed ProofPay walkthrough: an original illustrated presenter, local synthetic narration, captions and thirteen actual screenshots. It uses Python's standard library, Flite and FFmpeg. It makes no network requests and needs no API key, subscription, hosted avatar account or provider credit.

The presenter is a generic original character labelled **Synthetic presenter**. It does not depict a teammate or PayPal employee. Its mouth follows actual phoneme timings produced by Flite; it is not an audio-volume animation, voice clone or photorealistic face model.

## What the video shows

The 347-word narration distinguishes two sequences:

- Saved evidence from the completed model-to-PayPal sandbox purchase. Those scenes describe the recorded result, not a replay of that execution.
- A separate public rehearsal with deterministic proposals and a simulated payment provider. That sequence makes no model or PayPal calls.

The thirteen screenshots are reviewed inputs, not invented UI. `frames-manifest.json` maps them to nine scenes; `FRAMES_SHA256SUMS.txt` records their hashes. The completed film says **Edited actual UI states · Synthetic narration** throughout. The presenter has a separate column and does not cover app controls or evidence.

`DEMO_SCRIPT.md` is the approved narration snapshot for the reviewed build. Its “210 local checks” statement describes that review, not an automatically updated test count. `narration-exact-script.txt` contains the same words without Markdown. Update the evidence and review the narration before changing a claim.

## Local dependencies

Use Python 3.9 or later, `ffmpeg`, `ffprobe`, Flite shared libraries including the SLT voice, the FFmpeg `flite` filter and `librsvg` decoder, and Open Sans fonts. The reviewed environment used Flite 2.2 and FFmpeg 7.1.5 on Linux. No Python package installation is required.

The scripts currently expect these installed Linux library names:

- `libflite.so.1`
- `libflite_cmu_us_slt.so.1`

The compositor uses `OpenSans-Regular.ttf` and `OpenSans-Bold.ttf` under `/usr/share/fonts/truetype/open-sans/`. Adjust the font constants in `compose_video.py` and `validate_video.py` for another local installation. No dependencies, binaries, voice models or font files are bundled here.

## Rebuild from this directory

```sh
python3 prepare_narration.py --script DEMO_SCRIPT.md
python3 extract_phonemes.py
python3 render_presenter.py
python3 compose_video.py frames-manifest.json --check
python3 compose_video.py frames-manifest.json
python3 validate_video.py
```

The preparation step generates nine narration WAVs locally. The reviewed cadence is fixed for this exact script; the build refuses a different paragraph or word count until the script is deliberately updated. Each paragraph has a short silent pause, and the final video must stay below 170 seconds. No prerecorded narration WAV is needed in Git.

The main output is `proofpay-narrated-review-cut.mp4`. It is a review cut; the command does not publish or submit anything. Other generated outputs include `captions.srt`, `proofpay-video-contact-sheet.jpg`, `video-validation.json` and the source manifests. `.gitignore` excludes generated audio, video and caches while keeping the approved screenshots and source text tracked.

To regenerate one approved paragraph while retaining the other WAVs and the existing tempo:

```sh
python3 prepare_narration.py --paragraph 8 --script DEMO_SCRIPT.md
python3 extract_phonemes.py
python3 render_presenter.py
python3 compose_video.py frames-manifest.json
python3 validate_video.py
```

For a local source-and-input archive after a complete build:

```sh
python3 package_source.py
```

That archive includes code, notices, screenshots, generated audio, raw synthesis references and the presenter clip for direct local recomposition. It excludes credentials and dependency binaries. The combined MP4 is delivered separately. The archive is ignored by Git.

## How timing and checks work

`extract_phonemes.py` calls Flite's `flite_synth_text`, reads the `Segment` relation and extracts each phoneme name and end time. Every paragraph runs in a fresh process. Its returned utterance waveform must match the raw narration waveform byte for byte before a timing record is accepted. This avoids treating timings from a different synthesis as matching evidence.

`render_presenter.py` maps those segments to twelve vector mouth shapes, including diphthong transitions. It never uses waveform amplitude to choose a mouth shape. Segment times scale with the processed narration duration. Eye blinks are separate deterministic animation. Edit `avatar_svg()` in that file to change the original artwork; `presenter-original.svg` is the reference artwork and is regenerated from that function.

The reviewed cut was 1920 × 1080 at 30 fps and 163.521 seconds long. It used 1,687 phoneme segments, 4,905 frames and 35 subtitle entries. Full decoding passed, the AAC peak was −3.446 dBFS, and no full-scale audio samples were found. `validate_video.py` repeats duration, decode, audio-signal and subtitle-boundary checks and extracts nine actual preview frames for visual review. Different dependency versions may produce different timings; the generated reports describe each local build.

The voice is intelligible but more mechanical than a recorded narrator. Animation uses grouped visemes and discrete mouth changes. Caption words are exact, but their timings are estimated from speech lengths and punctuation rather than forced alignment. Listen at normal speed and review the contact sheet before publishing; signal checks do not replace that review.

## Adapting the inputs

`frames-manifest.template.json` starts with empty frame lists and unreviewed flags. Populate it only with actual screenshots. Review each screenshot's operation identity and evidence context before setting `evidence_reviewed`. Saved completed evidence and simulated rehearsal must remain visibly distinct; the compositor requires those scene labels. Screenshots are scaled uniformly and never retouched by the pipeline.

The supplied `frames-manifest.json` records the reviewed inputs. Its approval flags do not establish the truth of replacement images. Re-review it when changing screenshots or presenter footage. Optional supplied presenter footage must cover the complete narration timeline; the compositor does not loop or stretch a shorter clip.

## License and sources

Original Python and SVG work is MIT licensed under `LICENSE`. `THIRD_PARTY_NOTICES.txt` identifies the local dependencies and includes the installed Flite copyright notice. PayPal and other third-party names, marks and UI elements in screenshots remain those of their respective owners; this source license does not grant trademark rights or imply endorsement.

- [Flite source](https://github.com/festvox/flite)
- [Flite synthesizer API](https://github.com/festvox/flite/blob/master/include/flite.h)
- [Flite segment-reporting reference](https://github.com/festvox/flite/blob/master/main/flite_main.c)
- [Flite notices](https://github.com/festvox/flite/blob/master/COPYING)
- [FFmpeg Flite filter](https://ffmpeg.org/ffmpeg-filters.html#flite)

This is a local command-line pipeline. It does not install an MCP connector or expose a network service.
