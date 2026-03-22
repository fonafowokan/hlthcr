#!/usr/bin/env python3
"""Generate visual assets for Healthcare Foundations scenes.

Handles:
- Versioned output (never overwrites — appends _v2, _v3, etc.)
- Prompt tracking (saves prompt JSON alongside each image)
- Excalidraw diagrams and nano-banana title cards
- Batch or single-scene generation

Usage:
    # Generate all visuals:
    python scripts/generate_visuals.py

    # Generate one scene:
    python scripts/generate_visuals.py --scene SCN-PAYOR-01-02

    # Generate all scenes for a tutorial:
    python scripts/generate_visuals.py --tutorial T-PAYOR-01

    # Dry run (show prompts without generating):
    python scripts/generate_visuals.py --dry-run
"""

import argparse
import json
import os
import re
import subprocess
import sys
import yaml
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = PROJECT_ROOT / "media" / "images"
PROMPTS_DIR = IMAGES_DIR / "prompts"
STYLE_REF = PROJECT_ROOT / "brand-assets" / "excalidraw-style-reference.png"

EXCALIDRAW_STYLE_PREFIX = """Excalidraw-style hand-drawn diagram on a clean white background. All text uses neat, consistent architect-style handwriting -- legible, slightly rounded letters with medium stroke weight. Letter sizes are uniform within each label. Titles are bold and larger. Body labels are smaller but equally neat. This is NOT sloppy handwriting -- it looks like a designer wrote it carefully with a thick marker.

Shapes are rounded rectangles with a 2-3px dark gray (#495057) hand-drawn outline and soft pastel fills. Lines and arrows are slightly wobbly and hand-drawn, not ruler-straight. Arrowheads are simple triangles. Nothing is pixel-perfect -- everything has a natural, sketched feel with visible stroke texture.

Color palette: teal (#81D4C2), soft blue (#a5d8ff), warm yellow (#ffec99), coral (#ffa8a8), light purple (#d0bfff). All text is dark charcoal (#343a40). All lines and arrows are dark gray (#495057). Background is always clean white.

People are simple stick figures with round heads, no facial features. Healthcare workers wear a small cross or stethoscope icon. Documents have a folded corner. Shields represent insurance/payors. Hospital buildings are simple rectangles with a cross. All icons are simple line drawings, not detailed or cartoonish.

Layout is clean and spacious with generous whitespace. Visual hierarchy is clear -- title is largest, labels are short (max 3 words each). The overall feel is educational, friendly, and slightly more polished than basic Excalidraw -- colored fills, intentional spacing, consistent sizing, and meaningful color coding elevate it.

Do NOT include: realistic photos, gradients, drop shadows, 3D effects, corporate clip art, stock imagery, dark backgrounds, heavy borders."""


def get_versioned_path(base_path: Path) -> Path:
    """Return a versioned path that doesn't overwrite existing files.

    first.png -> first.png (if doesn't exist)
    first.png -> first_v2.png (if first.png exists)
    first.png -> first_v3.png (if first_v2.png exists)
    """
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent

    # Check if stem already has a version
    version_match = re.match(r'^(.+)_v(\d+)$', stem)
    if version_match:
        base_stem = version_match.group(1)
        version = int(version_match.group(2))
    else:
        base_stem = stem
        version = 1

    while True:
        version += 1
        new_path = parent / f"{base_stem}_v{version}{suffix}"
        if not new_path.exists():
            return new_path


def save_prompt(image_path: Path, prompt: str, scene: dict, visual_type: str):
    """Save the generation prompt as a JSON file alongside the image."""
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file = PROMPTS_DIR / (image_path.stem + ".json")
    # Version the prompt file too
    prompt_file = get_versioned_path(prompt_file) if prompt_file.exists() else prompt_file

    data = {
        "image_file": image_path.name,
        "scene_id": scene.get("scene_id"),
        "tutorial_id": scene.get("tutorial_id"),
        "visual_type": visual_type,
        "visual_prompt_hint": scene.get("visual_prompt_hint", ""),
        "prompt": prompt,
        "generated_at": datetime.now().isoformat(),
        "aspect_ratio": "16:9",
    }

    with open(prompt_file, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return prompt_file


def generate_excalidraw(scene: dict, output_path: Path, dry_run: bool = False) -> bool:
    """Generate an excalidraw-style diagram."""
    hint = scene.get("visual_prompt_hint", "")

    prompt = f"""{EXCALIDRAW_STYLE_PREFIX}

STYLE REFERENCE: Match the visual style of the reference image exactly -- same font, same shapes, same colors, same level of polish.

{hint}"""

    if dry_run:
        print(f"    PROMPT: {hint[:100]}...")
        return True

    save_prompt(output_path, prompt, scene, "excalidraw")

    cmd = [
        "node", str(PROJECT_ROOT / "scripts" / "excalidraw-visuals" / "generate-visual.js"),
        prompt,
        str(output_path),
        "16:9",
        "--input", str(STYLE_REF),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        print(f"    ERROR: {result.stderr[:200]}")
        return False
    return True


def generate_nano_banana(scene: dict, output_path: Path, dry_run: bool = False) -> bool:
    """Generate a nano-banana title card."""
    hint = scene.get("visual_prompt_hint", "")
    screen_text = scene.get("screen_text", "")

    prompt_json = {
        "prompt": f"Clean modern healthcare education title card, 16:9 aspect ratio. {hint}. Bold clean sans-serif text at center reads '{screen_text}' in dark navy (#1A1A2E). Professional, minimal, educational feel. No people, no photos. Flat design with subtle depth. Color palette: teal (#2A6F97), light blue (#A9D6E5), white, dark navy text.",
        "negative_prompt": "blurry, low resolution, cartoon, CGI, oversaturated, dark background, cluttered, realistic photos, 3D effects, drop shadows, stock imagery",
        "image_input": [],
        "api_parameters": {
            "resolution": "1K",
            "output_format": "png",
            "aspect_ratio": "16:9"
        },
        "settings": {
            "style": "flat modern educational",
            "lighting": "soft even",
            "quality": "high detail, clean"
        }
    }

    if dry_run:
        print(f"    PROMPT: {hint[:100]}...")
        return True

    save_prompt(output_path, json.dumps(prompt_json, indent=2), scene, "nano-banana")

    # Write temp prompt file
    tmp_prompt = PROJECT_ROOT / "projects" / "nano-banana" / "prompts" / f"_tmp_{scene['scene_id']}.json"
    tmp_prompt.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp_prompt, "w") as f:
        json.dump(prompt_json, f)

    cmd = [
        "python3",
        str(PROJECT_ROOT / "scripts" / "nano-banana" / "generate_kie.py"),
        str(tmp_prompt),
        str(output_path),
        "16:9",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    tmp_prompt.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"    ERROR: {result.stderr[:200]}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate visual assets for scenes")
    parser.add_argument("--scene", help="Generate for a single scene ID")
    parser.add_argument("--tutorial", help="Generate for all scenes in a tutorial")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts without generating")
    args = parser.parse_args()

    # Load scenes
    with open(PROJECT_ROOT / "scenes" / "scenes.yaml") as f:
        scenes = yaml.safe_load(f)["scenes"]

    # Filter to scenes that have visuals
    scenes = [s for s in scenes if s.get("visual_asset") and s.get("visual_type")]

    if args.scene:
        scenes = [s for s in scenes if s["scene_id"] == args.scene]
    elif args.tutorial:
        scenes = [s for s in scenes if s["tutorial_id"] == args.tutorial]

    if not scenes:
        print("No matching scenes found.")
        return

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    total = len(scenes)
    success = 0
    failed = 0

    print(f"Generating {total} visuals {'(dry run)' if args.dry_run else ''}...\n")

    for i, scene in enumerate(scenes, 1):
        scene_id = scene["scene_id"]
        visual_type = scene["visual_type"]
        base_filename = scene["visual_asset"].replace("images/", "")
        base_path = IMAGES_DIR / base_filename

        # Version the output path
        output_path = get_versioned_path(base_path)
        version_note = f" (-> {output_path.name})" if output_path != base_path else ""

        print(f"  [{i}/{total}] {scene_id} [{visual_type}]{version_note}")

        if visual_type == "excalidraw":
            ok = generate_excalidraw(scene, output_path, args.dry_run)
        elif visual_type == "nano-banana":
            ok = generate_nano_banana(scene, output_path, args.dry_run)
        else:
            print(f"    SKIP: unknown visual_type '{visual_type}'")
            continue

        if ok:
            success += 1
            if not args.dry_run:
                print(f"    OK: {output_path.name}")
        else:
            failed += 1

    print(f"\nDone. {success} succeeded, {failed} failed out of {total}.")


if __name__ == "__main__":
    main()
