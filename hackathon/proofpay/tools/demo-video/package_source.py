#!/usr/bin/env python3
"""Package only the explicit reproducible video inputs; no workspace sweep."""
from pathlib import Path
import hashlib
import json
import zipfile

HERE = Path(__file__).resolve().parent
FILES = [
    'README.md','LICENSE','THIRD_PARTY_NOTICES.txt','DEMO_SCRIPT.md','.gitignore','FRAMES_SHA256SUMS.txt',
    'prepare_narration.py','extract_phonemes.py','render_presenter.py','compose_video.py',
    'validate_video.py','package_source.py','frames-manifest.template.json','frames-manifest.json',
    'narration-exact-script.txt','narration-manifest.json','phoneme-timeline.json',
    'presenter-original.svg','presenter-phoneme-silent.mp4','presenter-validation.json',
    'captions.srt','video-source-manifest.json','video-validation.json','proofpay-video-contact-sheet.jpg',
]


def main():
    sources = [HERE / name for name in FILES]
    for pattern in ('frames/*.png','narration/scene-*.wav','render-work/raw-*.wav','text/scene-*-spoken.txt','text/scene-*-exact.txt'):
        sources.extend(sorted(HERE.glob(pattern)))
    assert len(list(HERE.glob('frames/*.png'))) == 13
    assert len(list(HERE.glob('narration/scene-*.wav'))) == 9
    assert len(list(HERE.glob('render-work/raw-*.wav'))) == 9
    assert all(path.is_file() for path in sources)
    sources = sorted(set(sources))
    hashes = ''.join(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(HERE)}\n' for path in sources)
    (HERE/'BUNDLE_SHA256SUMS.txt').write_text(hashes)
    sources.append(HERE/'BUNDLE_SHA256SUMS.txt')
    output=HERE/'proofpay-free-presenter-complete-source.zip'
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as package:
        for path in sources:
            package.write(path,Path('proofpay-free-presenter-source')/path.relative_to(HERE))
    with zipfile.ZipFile(output) as package:
        assert package.testzip() is None
        for path in sources:
            assert package.read(str(Path('proofpay-free-presenter-source')/path.relative_to(HERE))) == path.read_bytes()
    report={'file':output.name,'bytes':output.stat().st_size,'files':len(sources),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'zip_integrity_verified':True,'source_screenshots':13,'narration_wavs':9,'raw_synthesis_wavs':9,'final_combined_mp4':'Delivered separately; not duplicated in source ZIP'}
    (HERE/'source-package-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
