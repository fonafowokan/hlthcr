---
name: nano-banana-images
description: Use when someone asks to generate a hyper-realistic photo, nano banana image, realistic portrait, product shot, or photorealistic render. This generates high-detail PNG/JPG images via Nano Banana 2 (Gemini 3.1 Flash) through parameterized JSON prompting.
---

## What This Skill Does

Generates hyper-realistic, highly-controlled images using the Nano Banana 2 model through parameterized JSON prompting via kie.ai API. Costs ~$0.04-0.09 per image.

For the full JSON schema breakdown, parameter options, and multi-panel grid structures, see [master_prompt_reference.md](master_prompt_reference.md).

For project organization conventions, see [gemini.md](gemini.md).

## Prerequisites

1. `KIE_AI_API_KEY` in `.env`
2. Python 3 with `requests` installed
3. Scripts at `scripts/nano-banana/generate_kie.py` and `scripts/nano-banana/get_kie_image.py`

## Step 1: Understand the Request

Get from the user:
- What subject to generate (person, product, nature, infographic)
- Any specific style, lighting, or camera requirements
- Aspect ratio preference (default: `auto`, options: `16:9`, `4:5`, `3:4`, `1:1`)
- Resolution preference (default: `1K`, options: `2K`, `4K`)

If the request is vague, ask 1-2 clarifying questions about the specific look they want.

## Step 2: Build the JSON Prompt

Construct a prompt JSON file using the Dense Narrative Format:

```json
{
  "prompt": "Dense ultra-descriptive narrative with camera math (85mm, f/1.8, ISO 200), explicit imperfections, lighting behavior, and direct negative commands.",
  "negative_prompt": "blurry, low resolution, distorted face, extra fingers, overexposed, heavy makeup, unrealistic skin, cartoon, CGI, oversaturated colors, anatomy normalization, skin smoothing, plastic skin, airbrushed texture",
  "image_input": [],
  "api_parameters": {
    "resolution": "1K",
    "output_format": "jpg",
    "aspect_ratio": "auto"
  },
  "settings": {
    "resolution": "1024x1792",
    "style": "documentary realism",
    "lighting": "natural light",
    "camera_angle": "eye level",
    "depth_of_field": "shallow",
    "quality": "high detail, unretouched"
  }
}
```

### Prompt Construction Rules

1. **Camera Mathematics:** Always define exact focal length, aperture, ISO (e.g., `85mm lens, f/2.0, ISO 200`).
2. **Explicit Imperfections:** Dictate flaws: `mild redness`, `subtle freckles`, `light acne marks`, `visible pores`.
3. **Direct Commands:** Use imperative negatives inside the positive prompt: `Do not beautify or alter facial features.`
4. **Lighting Behavior:** Name what light does, not just what it is: `direct flash creating sharp highlights on skin`.
5. **Non-Human Materials:** Replace skin logic with material physics: `micro-scratches on anodized aluminum`, `subsurface scattering through dew-covered petals`.
6. **Mandatory Negative Stack:** Always include the extensive negative prompt block.
7. **Avoid Over-Degradation:** Keep ISO below 800. Use physical subject imperfections rather than heavy camera noise.

## Step 3: Save the Prompt

Save the JSON prompt file to:
```
projects/nano-banana/prompts/[YYYY-MM-DD]-[slug].json
```

Create the directories if they don't exist.

## Step 4: Generate the Image

Run the generation script:
```bash
python scripts/nano-banana/generate_kie.py "projects/nano-banana/prompts/[slug].json" "projects/nano-banana/images/[slug].jpg" "[aspect_ratio]"
```

The script will:
1. Create a task via kie.ai API
2. Poll for completion
3. Download and save the image

If you need to retrieve a previously generated image by task ID:
```bash
python scripts/nano-banana/get_kie_image.py "<taskId>" "projects/nano-banana/images/[slug].jpg"
```

## Step 5: Present Result

- Show the file path for preview
- Summarize what was generated and key prompt parameters
- Ask if adjustments are needed

If adjustments needed: modify the prompt JSON and regenerate.

## File Locations

| What | Path |
|------|------|
| Skill | `.claude/skills/nano-banana-images/SKILL.md` |
| Master reference | `.claude/skills/nano-banana-images/master_prompt_reference.md` |
| Project organizer | `.claude/skills/nano-banana-images/gemini.md` |
| Generate script | `scripts/nano-banana/generate_kie.py` |
| Retrieve script | `scripts/nano-banana/get_kie_image.py` |
| Prompts output | `projects/nano-banana/prompts/` |
| Images output | `projects/nano-banana/images/` |
| API key | `.env` (KIE_AI_API_KEY) |

## Notes

- Uses Nano Banana 2 (Gemini 3.1 Flash) via kie.ai (~$0.04-0.09 per image)
- The Dense Narrative Format is preferred for API calls
- Reference images can be passed via `image_input` array (up to 14 URLs)
- For multi-panel grids (2x2, side-by-side), use the Deep Grid paradigm from the master reference
- Always include the full negative prompt stack for realism
