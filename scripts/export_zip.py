#!/usr/bin/env python3
"""Build a self-contained zip of the Healthcare Foundations course.

Creates a zip file with:
  - index.html (audio refs updated to .mp3)
  - media/audio/*.mp3
  - media/images/*.png (if any exist)

Usage:
    python scripts/export_zip.py
    python scripts/export_zip.py --output /path/to/output.zip
"""

import argparse
import os
import re
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def build_export_html(html_path: Path) -> str:
    """Read index.html and swap .wav references to .mp3."""
    html = html_path.read_text()
    # Update audio asset paths: audio/xxx.wav -> audio/xxx.mp3
    html = re.sub(r'(audio/[^"\']+)\.wav', r'\1.mp3', html)
    return html


def main():
    parser = argparse.ArgumentParser(description="Export course as self-contained zip")
    parser.add_argument("--output", default=None, help="Output zip path")
    args = parser.parse_args()

    output_path = args.output or str(PROJECT_ROOT / "exports" / "healthcare-foundations.zip")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    mp3_dir = PROJECT_ROOT / "media" / "audio-mp3"
    images_dir = PROJECT_ROOT / "media" / "images"
    html_path = PROJECT_ROOT / "index.html"

    if not html_path.exists():
        print("Error: index.html not found")
        return

    print("Building export zip...")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # HTML with .mp3 references
        export_html = build_export_html(html_path)
        zf.writestr("healthcare-foundations/index.html", export_html)
        print(f"  + index.html ({len(export_html) // 1024}KB)")

        # MP3 audio files
        mp3_count = 0
        if mp3_dir.exists():
            for f in sorted(mp3_dir.glob("*.mp3")):
                arcname = f"healthcare-foundations/media/audio/{f.name}"
                zf.write(f, arcname)
                mp3_count += 1
        print(f"  + {mp3_count} MP3 audio files")

        # Images (if any)
        img_count = 0
        if images_dir.exists():
            for f in sorted(images_dir.iterdir()):
                if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".svg"):
                    arcname = f"healthcare-foundations/media/images/{f.name}"
                    zf.write(f, arcname)
                    img_count += 1
        if img_count:
            print(f"  + {img_count} image files")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\nExported: {output_path} ({size_mb:.1f}MB)")


if __name__ == "__main__":
    main()
