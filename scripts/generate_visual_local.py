#!/usr/bin/env python3
"""Generate excalidraw-style visuals locally via ComfyUI + Flux + IPAdapter.

Uses the style reference image with IPAdapter style transfer to maintain
consistent excalidraw aesthetic across all generated diagrams.

Usage:
    # Generate one scene:
    python scripts/generate_visual_local.py --scene SCN-PAYOR-01-02

    # Generate all scenes for a tutorial:
    python scripts/generate_visual_local.py --tutorial T-PAYOR-01

    # Generate all visuals:
    python scripts/generate_visual_local.py

    # Dry run:
    python scripts/generate_visual_local.py --dry-run
"""

import argparse
import base64
import io
import json
import os
import re
import shutil
import sys
import time
import urllib.request
import urllib.parse
import yaml
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = PROJECT_ROOT / "media" / "images"
PROMPTS_DIR = IMAGES_DIR / "prompts"
SHARED_DIR = Path("/home/femi/projects/shared/HLTHCR/images")
STYLE_REF = PROJECT_ROOT / "brand-assets" / "excalidraw-style-reference.png"

COMFYUI_URL = "http://localhost:8188"

EXCALIDRAW_STYLE_PREFIX = """Excalidraw-style hand-drawn diagram on a clean white background. All text uses neat, consistent architect-style handwriting -- legible, slightly rounded letters with medium stroke weight. Letter sizes are uniform within each label. Titles are bold and larger. Body labels are smaller but equally neat.

Shapes are rounded rectangles with a 2-3px dark gray hand-drawn outline and soft pastel fills. Lines and arrows are slightly wobbly and hand-drawn, not ruler-straight. Arrowheads are simple triangles. Everything has a natural, sketched feel.

Color palette: teal (#81D4C2), soft blue (#a5d8ff), warm yellow (#ffec99), coral (#ffa8a8), light purple (#d0bfff). All text is dark charcoal. All lines are dark gray. Background is clean white.

Do NOT include: realistic photos, gradients, drop shadows, 3D effects, dark backgrounds."""

NANO_BANANA_PREFIX = """Clean modern healthcare education title card, 16:9 aspect ratio. Professional, minimal, educational feel. No people, no photos. Flat design with subtle depth. Color palette: teal (#2A6F97), light blue (#A9D6E5), white, dark navy text."""


def get_versioned_path(base_path: Path) -> Path:
    """Return a versioned path that doesn't overwrite existing files."""
    if not base_path.exists():
        return base_path
    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent
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


def save_prompt(image_path: Path, prompt: str, scene: dict, visual_type: str, notes: str = ""):
    """Save generation prompt as JSON."""
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file = PROMPTS_DIR / (image_path.stem + ".json")
    if prompt_file.exists():
        prompt_file = get_versioned_path(prompt_file)
    data = {
        "image_file": image_path.name,
        "scene_id": scene.get("scene_id"),
        "tutorial_id": scene.get("tutorial_id"),
        "visual_type": visual_type,
        "visual_prompt_hint": scene.get("visual_prompt_hint", ""),
        "prompt": prompt,
        "engine": "comfyui-flux-dev",
        "generated_at": datetime.now().isoformat(),
        "aspect_ratio": "16:9",
        "notes": notes,
    }
    with open(prompt_file, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return prompt_file


def upload_image_to_comfyui(image_path: Path) -> str:
    """Upload an image to ComfyUI and return the filename."""
    with open(image_path, "rb") as f:
        image_data = f.read()

    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    filename = image_path.name

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + image_data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{COMFYUI_URL}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    return result.get("name", filename)


def build_workflow(prompt_text: str, style_ref_name: str, width: int = 1344, height: int = 768) -> dict:
    """Build a ComfyUI workflow for Flux + IPAdapter style transfer."""
    workflow = {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "flux1-dev.safetensors",
                "weight_dtype": "default"
            }
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "t5xxl_fp16.safetensors",
                "type": "flux"
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt_text,
                "clip": ["2", 0]
            }
        },
        "4": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "ae.safetensors"
            }
        },
        "5": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            }
        },
        "6": {
            "class_type": "LoadImage",
            "inputs": {
                "image": style_ref_name
            }
        },
        "7": {
            "class_type": "IPAdapterUnifiedLoader",
            "inputs": {
                "preset": "PLUS (high strength)",
                "model": ["1", 0]
            }
        },
        "8": {
            "class_type": "IPAdapterAdvanced",
            "inputs": {
                "model": ["7", 0],
                "ipadapter": ["7", 1],
                "image": ["6", 0],
                "weight": 0.7,
                "weight_type": "style transfer",
                "start_at": 0.0,
                "end_at": 1.0,
                "combine_embeds": "concat"
            }
        },
        "9": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["8", 0],
                "positive": ["3", 0],
                "negative": ["10", 0],
                "latent_image": ["5", 0],
                "seed": int(time.time()) % (2**32),
                "steps": 28,
                "cfg": 4.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0
            }
        },
        "10": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "realistic photo, gradient, drop shadow, 3D, dark background, blurry, low quality",
                "clip": ["2", 0]
            }
        },
        "11": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["9", 0],
                "vae": ["4", 0]
            }
        },
        "12": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["11", 0],
                "filename_prefix": "hlthcr"
            }
        }
    }
    return {"prompt": workflow}


def queue_prompt(workflow: dict) -> str:
    """Queue a workflow and return the prompt_id."""
    data = json.dumps(workflow).encode()
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    return result.get("prompt_id")


def wait_for_result(prompt_id: str, timeout: int = 300) -> str:
    """Poll ComfyUI until the image is ready, return the filename."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}")
            history = json.loads(resp.read())
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                for node_id, node_output in outputs.items():
                    images = node_output.get("images", [])
                    if images:
                        return images[0]["filename"]
        except Exception:
            pass
        time.sleep(2)
    return None


def download_image(filename: str, output_path: Path):
    """Download a generated image from ComfyUI."""
    url = f"{COMFYUI_URL}/view?filename={urllib.parse.quote(filename)}&type=output"
    resp = urllib.request.urlopen(url)
    with open(output_path, "wb") as f:
        f.write(resp.read())


def generate_image(scene: dict, output_path: Path, style_ref_name: str, dry_run: bool = False) -> bool:
    """Generate an image for a scene."""
    visual_type = scene.get("visual_type", "excalidraw")
    hint = scene.get("visual_prompt_hint", "")
    screen_text = scene.get("screen_text", "")

    if visual_type == "excalidraw":
        prompt_text = f"{EXCALIDRAW_STYLE_PREFIX}\n\n{hint}"
    else:
        prompt_text = f"{NANO_BANANA_PREFIX}\n\n{hint}. Bold text reads '{screen_text}' in dark navy."

    if dry_run:
        print(f"    PROMPT: {hint[:80]}...")
        return True

    save_prompt(output_path, prompt_text, scene, visual_type)

    # Build and queue workflow
    # 16:9 at ~1MP: 1344x768
    workflow = build_workflow(prompt_text, style_ref_name, width=1344, height=768)
    prompt_id = queue_prompt(workflow)

    if not prompt_id:
        print("    ERROR: Failed to queue prompt")
        return False

    print(f"    Queued: {prompt_id[:12]}...", end=" ", flush=True)

    # Wait for result
    result_filename = wait_for_result(prompt_id)
    if not result_filename:
        print("TIMEOUT")
        return False

    # Download
    download_image(result_filename, output_path)
    size_kb = output_path.stat().st_size // 1024
    print(f"OK ({size_kb}KB)")

    # Copy to shared folder
    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output_path, SHARED_DIR / output_path.name)

    return True


def main():
    parser = argparse.ArgumentParser(description="Generate visuals locally via ComfyUI + Flux")
    parser.add_argument("--scene", help="Generate for a single scene ID")
    parser.add_argument("--tutorial", help="Generate for all scenes in a tutorial")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts without generating")
    args = parser.parse_args()

    # Check ComfyUI
    try:
        urllib.request.urlopen(f"{COMFYUI_URL}/system_stats")
    except Exception:
        print("ERROR: ComfyUI not responding at", COMFYUI_URL)
        sys.exit(1)

    # Upload style reference
    style_ref_name = None
    if STYLE_REF.exists():
        print("Uploading style reference...")
        style_ref_name = upload_image_to_comfyui(STYLE_REF)
        print(f"  Style ref: {style_ref_name}")
    else:
        print("WARNING: No style reference image found")
        sys.exit(1)

    # Load scenes
    with open(PROJECT_ROOT / "scenes" / "scenes.yaml") as f:
        scenes = yaml.safe_load(f)["scenes"]

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

    print(f"\nGenerating {total} visuals via ComfyUI {'(dry run)' if args.dry_run else ''}...\n")

    for i, scene in enumerate(scenes, 1):
        scene_id = scene["scene_id"]
        visual_type = scene["visual_type"]
        base_filename = scene["visual_asset"].replace("images/", "")
        base_path = IMAGES_DIR / base_filename
        output_path = get_versioned_path(base_path)
        version_note = f" (-> {output_path.name})" if output_path != base_path else ""

        print(f"  [{i}/{total}] {scene_id} [{visual_type}]{version_note}")

        ok = generate_image(scene, output_path, style_ref_name, args.dry_run)

        if ok:
            success += 1
        else:
            failed += 1

    print(f"\nDone. {success} succeeded, {failed} failed out of {total}.")


if __name__ == "__main__":
    main()
