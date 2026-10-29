# ProofGate team media

The vector graphics acknowledge mentorship from Prof. Nithya Ravi Kumar and implementation by Rama Chandra. They do not claim completed research review, historical authorship or institutional endorsement.

- `proofgate-team-card.svg`: 1200 × 800, suitable for a 3:2 Devpost thumbnail.
- `proofgate-video-credits.svg`: 1920 × 1080, used as the ten-second video end card.

PNG exports, the 119-second captioned walkthrough, all nine source screenshots in `captures/`, and `build_walkthrough.py` are committed here. The SVGs use exact text and original code-native graphics; no portrait or third-party logo is used.

The video is a silent, captioned sequence of real execution screenshots, followed by a credit card. It is not a continuous recording and does not show fresh model inference. See [video provenance](../VIDEO_PROVENANCE.md).

## Rebuild the media

Install FFmpeg with the `drawtext` filter and DejaVu Sans fonts. On Debian/Ubuntu, the required packages are `ffmpeg` and `fonts-dejavu-core`. Then, from the repository root:

```bash
python hackathon/nebius-nvidia-rarb-demo/submission/media/build_walkthrough.py
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 hackathon/nebius-nvidia-rarb-demo/submission/media/proofgate-walkthrough.mp4
```

Expected duration: 119 seconds. Intermediate renders are ignored by Git. The included PNG credit card is generated from `proofgate-video-credits.svg`; FFmpeg builds with librsvg can reproduce the PNG with `ffmpeg -i proofgate-video-credits.svg -frames:v 1 proofgate-video-credits.png`. The team card follows the same command pattern. PNGs are committed so video rebuilding does not require an SVG renderer.

The original captures remain historical evidence. Rebuilding the video adds captions without altering their recorded execution outcomes.

Public files:
- https://kaulastudies.github.io/ai-evaluation-lab/proofgate/proofgate-team-card.png
- https://kaulastudies.github.io/ai-evaluation-lab/proofgate/proofgate-video-credits.png
- https://kaulastudies.github.io/ai-evaluation-lab/proofgate/proofgate-walkthrough.mp4
