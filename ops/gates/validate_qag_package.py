"""Check the built QAG wheel carries the repository's Apache license."""
from email.parser import BytesParser
from pathlib import Path
import sys
import zipfile


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: validate_qag_package.py PATH_TO_WHEEL")
    root = Path(__file__).resolve().parents[2]
    expected = (root / "LICENSE").read_bytes().rstrip(b"\r\n") + b"\n"
    with zipfile.ZipFile(sys.argv[1]) as wheel:
        metadata_files = [p for p in wheel.namelist() if p.endswith(".dist-info/METADATA")]
        if len(metadata_files) != 1:
            raise SystemExit("Expected exactly one wheel METADATA file")
        metadata_path = metadata_files[0]
        metadata = BytesParser().parsebytes(wheel.read(metadata_path))
        if metadata["License-Expression"] != "Apache-2.0":
            raise SystemExit("Wheel must declare Apache-2.0")
        if metadata.get_all("License-File") != ["LICENSE-APACHE-2.0"]:
            raise SystemExit("Wheel must declare the bundled Apache license")
        license_path = metadata_path.rsplit("/", 1)[0] + "/licenses/LICENSE-APACHE-2.0"
        if wheel.read(license_path) != expected:
            raise SystemExit("Wheel license differs from repository LICENSE")
    print("QAG wheel license metadata and bundled text verified")


if __name__ == "__main__":
    main()
