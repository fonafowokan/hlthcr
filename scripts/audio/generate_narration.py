#!/usr/bin/env python3
"""Generate narration audio for Healthcare Foundations scenes using Kokoro TTS.

Usage:
    # Generate all scenes:
    python scripts/audio/generate_narration.py

    # Generate a single scene:
    python scripts/audio/generate_narration.py --scene SCN-PAYOR-01-02

    # Generate all scenes for a tutorial:
    python scripts/audio/generate_narration.py --tutorial T-PAYOR-01

    # Use a different voice:
    python scripts/audio/generate_narration.py --voice am_michael

    # Adjust speed:
    python scripts/audio/generate_narration.py --speed 0.95
"""

import argparse
import os
import sys
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


def load_scenes(scenes_path: Path) -> list:
    with open(scenes_path) as f:
        data = yaml.safe_load(f)
    return data["scenes"]


def load_tutorials(tutorials_path: Path) -> dict:
    """Load tutorials indexed by tutorial_id for narration text."""
    with open(tutorials_path) as f:
        data = yaml.safe_load(f)
    return {t["tutorial_id"]: t for t in data["tutorials"]}


def get_narration_text(scene: dict, tutorials: dict) -> str:
    """Build narration text for a scene.

    For intro scenes: use the title.
    For lesson scenes: use the full tutorial section text (richer than screen_text).
    For assessment scenes: use the screen_text as-is.
    """
    scene_type = scene.get("scene_type", "lesson")
    tutorial_id = scene["tutorial_id"]
    tutorial = tutorials.get(tutorial_id)

    if scene_type == "intro":
        title = tutorial["title"] if tutorial else scene["screen_text"]
        return f"Welcome to {title}."

    if scene_type == "assessment":
        return scene["screen_text"]

    # Lesson scenes: find matching tutorial section by order
    # Intro is order 1, so lesson sections start at order 2
    if tutorial:
        section_index = scene["order"] - 2  # offset for intro scene
        sections = tutorial.get("sections", [])
        if 0 <= section_index < len(sections):
            return sections[section_index]["text"].strip()

    # Fallback to screen_text
    return scene["screen_text"]


def generate_audio(pipe: KPipeline, text: str, voice: str, speed: float) -> np.ndarray:
    """Generate audio from text using Kokoro pipeline."""
    chunks = []
    for _, _, audio in pipe(text, voice=voice, speed=speed):
        chunks.append(audio)
    if not chunks:
        return np.array([], dtype=np.float32)
    return np.concatenate(chunks)


def main():
    parser = argparse.ArgumentParser(description="Generate narration audio with Kokoro TTS")
    parser.add_argument("--scene", help="Generate a single scene by ID")
    parser.add_argument("--tutorial", help="Generate all scenes for a tutorial")
    parser.add_argument("--voice", default=DEFAULT_VOICE, choices=VOICES.keys(),
                        help=f"Voice to use (default: {DEFAULT_VOICE})")
    parser.add_argument("--speed", type=float, default=DEFAULT_SPEED,
                        help=f"Speech speed (default: {DEFAULT_SPEED})")
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "media" / "audio"),
                        help="Output directory for audio files")
    parser.add_argument("--format", default="wav", choices=["wav", "mp3"],
                        help="Output audio format (default: wav)")
    parser.add_argument("--list-voices", action="store_true",
                        help="List available voices and exit")
    args = parser.parse_args()

    if args.list_voices:
        print("Available voices:")
        for voice_id, desc in VOICES.items():
            print(f"  {voice_id}: {desc}")
        return

    # Load data
    scenes = load_scenes(PROJECT_ROOT / "scenes" / "scenes.yaml")
    tutorials = load_tutorials(PROJECT_ROOT / "content" / "tutorials.yaml")

    # Filter scenes
    if args.scene:
        scenes = [s for s in scenes if s["scene_id"] == args.scene]
        if not scenes:
            print(f"Scene {args.scene} not found.")
            sys.exit(1)
    elif args.tutorial:
        scenes = [s for s in scenes if s["tutorial_id"] == args.tutorial]
        if not scenes:
            print(f"No scenes found for tutorial {args.tutorial}.")
            sys.exit(1)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize Kokoro
    print(f"Initializing Kokoro TTS (voice: {args.voice}, speed: {args.speed})...")
    pipe = KPipeline(lang_code="a")

    # Generate audio for each scene
    total = len(scenes)
    for i, scene in enumerate(scenes, 1):
        scene_id = scene["scene_id"]
        audio_filename = scene.get("audio_asset", "").replace("audio/", "")
        if not audio_filename:
            audio_filename = f"{scene_id.lower()}.wav"

        # Replace .mp3 extension with chosen format
        audio_filename = Path(audio_filename).stem + f".{args.format}"
        output_path = output_dir / audio_filename

        narration = get_narration_text(scene, tutorials)
        if not narration:
            print(f"  [{i}/{total}] {scene_id} — skipped (no text)")
            continue

        print(f"  [{i}/{total}] {scene_id} — {len(narration)} chars...", end=" ", flush=True)

        audio = generate_audio(pipe, narration, args.voice, args.speed)

        if len(audio) == 0:
            print("EMPTY")
            continue

        sf.write(str(output_path), audio, SAMPLE_RATE)
        duration = len(audio) / SAMPLE_RATE
        print(f"{duration:.1f}s -> {output_path.name}")

    print(f"\nDone. {total} scenes processed.")


if __name__ == "__main__":
    main()
