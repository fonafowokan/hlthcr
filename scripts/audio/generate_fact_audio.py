#!/usr/bin/env python3
"""Generate narration audio for Healthcare Foundations fact sections using Kokoro TTS.

Usage:
    # Generate all 14 fact section narrations:
    python scripts/audio/generate_fact_audio.py

    # Generate a single section:
    python scripts/audio/generate_fact_audio.py --section 3

    # Use a different voice:
    python scripts/audio/generate_fact_audio.py --voice am_michael

    # Adjust speed:
    python scripts/audio/generate_fact_audio.py --speed 0.95

    # Also generate MP3 versions:
    python scripts/audio/generate_fact_audio.py --mp3
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
import yaml
import numpy as np
import soundfile as sf
from pathlib import Path
from kokoro import KPipeline

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Defaults
DEFAULT_VOICE = "af_heart"
DEFAULT_SPEED = 1.0
SAMPLE_RATE = 24000

# Available voices (Kokoro 82M cached)
VOICES = {
    "af_heart": "American female, warm and clear",
    "af_nova": "American female, bright and energetic",
    "am_michael": "American male, steady and professional",
    "bm_george": "British male, calm and measured",
}

# Acronyms that should be spelled out letter-by-letter for TTS.
# Maps uppercase acronym to spaced letters with periods for clear pronunciation.
SPELL_OUT = {
    "PHI": "P. H. I.",
    "EHR": "E. H. R.",
    "EOB": "E. O. B.",
    "NPI": "N. P. I.",
    "ERA": "E. R. A.",
    "DME": "D. M. E.",
    "TPO": "T. P. O.",
    "HHS": "H. H. S.",
    "CMS": "C. M. S.",
    "ACA": "A. C. A.",
    "SEP": "S. E. P.",
    "MAC": "M. A. C.",
    "FMAP": "F. MAP.",
    "ASCA": "A. S. C. A.",
    "ePHI": "electronic P. H. I.",
    "DMEPOS": "D. M. E. P. O. S.",
    "PECOS": "PEE-koss",
    "HIPAA": "hippa",
    "HCPCS": "HICK-picks",
}


def preprocess_for_tts(text: str) -> str:
    """Replace acronyms with TTS-friendly pronunciations."""
    for acronym, replacement in SPELL_OUT.items():
        # Match whole word only, case-sensitive
        text = re.sub(r'\b' + re.escape(acronym) + r'\b', replacement, text)
    return text


def slugify(title: str) -> str:
    """Convert a section title to a filename-safe slug.

    Examples:
        "The Players: Who's Who" -> "the-players"
        "Providers: Types & Settings" -> "providers-types-settings"
        "HIPAA: PHI & Privacy Rule" -> "hipaa-phi-privacy-rule"
    """
    # Take the part after the colon if present, otherwise use the whole title
    if ":" in title:
        slug_part = title.split(":", 1)[1].strip()
    else:
        slug_part = title.strip()
    # Remove possessives and apostrophes
    slug_part = slug_part.replace("'s", "").replace("'", "")
    # Replace & with nothing (words around it stay)
    slug_part = slug_part.replace("&", "")
    # Lowercase
    slug_part = slug_part.lower()
    # Replace non-alphanumeric with hyphens
    slug_part = re.sub(r'[^a-z0-9]+', '-', slug_part)
    # Strip leading/trailing hyphens and collapse multiples
    slug_part = re.sub(r'-+', '-', slug_part).strip('-')
    return slug_part


def load_narrations(path: Path) -> list:
    """Load fact narrations from YAML."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return data["narrations"]


def generate_audio(pipe: KPipeline, text: str, voice: str, speed: float) -> np.ndarray:
    """Generate audio from text using Kokoro pipeline."""
    chunks = []
    for _, _, audio in pipe(text, voice=voice, speed=speed):
        chunks.append(audio)
    if not chunks:
        return np.array([], dtype=np.float32)
    return np.concatenate(chunks)


def convert_to_mp3(wav_path: Path, mp3_path: Path) -> bool:
    """Convert a WAV file to MP3 using ffmpeg. Returns True on success."""
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(wav_path),
                "-codec:a", "libmp3lame",
                "-b:a", "128k",
                str(mp3_path),
            ],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate fact section narration audio with Kokoro TTS"
    )
    parser.add_argument("--section", type=int,
                        help="Generate a single section by section_id (1-14)")
    parser.add_argument("--voice", default=DEFAULT_VOICE, choices=VOICES.keys(),
                        help=f"Voice to use (default: {DEFAULT_VOICE})")
    parser.add_argument("--speed", type=float, default=DEFAULT_SPEED,
                        help=f"Speech speed (default: {DEFAULT_SPEED})")
    parser.add_argument("--mp3", action="store_true",
                        help="Also generate MP3 versions in media/audio-mp3/facts/")
    args = parser.parse_args()

    # Load narrations
    narrations_path = PROJECT_ROOT / "content" / "fact_narrations.yaml"
    if not narrations_path.exists():
        print(f"Error: {narrations_path} not found.")
        sys.exit(1)

    narrations = load_narrations(narrations_path)

    # Filter to single section if requested
    if args.section is not None:
        narrations = [n for n in narrations if n["section_id"] == args.section]
        if not narrations:
            print(f"Error: Section {args.section} not found.")
            sys.exit(1)

    # Create output directories
    wav_dir = PROJECT_ROOT / "media" / "audio" / "facts"
    wav_dir.mkdir(parents=True, exist_ok=True)

    mp3_dir = None
    has_ffmpeg = False
    if args.mp3:
        mp3_dir = PROJECT_ROOT / "media" / "audio-mp3" / "facts"
        mp3_dir.mkdir(parents=True, exist_ok=True)
        # Check for ffmpeg
        has_ffmpeg = shutil.which("ffmpeg") is not None
        if not has_ffmpeg:
            print("Warning: ffmpeg not found. MP3 conversion will be skipped.")

    # Initialize Kokoro
    print(f"Initializing Kokoro TTS (voice: {args.voice}, speed: {args.speed})...")
    pipe = KPipeline(lang_code="a")

    total = len(narrations)
    total_duration = 0.0
    start_time = time.time()

    for i, narration in enumerate(narrations, 1):
        section_id = narration["section_id"]
        title = narration["title"]
        script = narration["script"].strip()
        slug = slugify(title)
        filename = f"facts-{section_id:02d}-{slug}.wav"

        print(f"Generating section {i}/{total}: {title}...", end=" ", flush=True)

        # Preprocess for TTS
        processed_text = preprocess_for_tts(script)

        # Generate audio
        audio = generate_audio(pipe, processed_text, args.voice, args.speed)

        if len(audio) == 0:
            print("EMPTY — skipped")
            continue

        # Write WAV
        wav_path = wav_dir / filename
        sf.write(str(wav_path), audio, SAMPLE_RATE)
        duration = len(audio) / SAMPLE_RATE
        total_duration += duration
        print(f"{duration:.1f}s -> {wav_path.name}")

        # Convert to MP3 if requested
        if args.mp3 and has_ffmpeg and mp3_dir:
            mp3_filename = f"facts-{section_id:02d}-{slug}.mp3"
            mp3_path = mp3_dir / mp3_filename
            if convert_to_mp3(wav_path, mp3_path):
                print(f"  MP3 -> {mp3_path.name}")
            else:
                print(f"  MP3 conversion failed for {filename}")

    elapsed = time.time() - start_time
    print(f"\nDone. {total} sections processed.")
    print(f"Total audio duration: {total_duration:.1f}s ({total_duration / 60:.1f} min)")
    print(f"Generation time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
