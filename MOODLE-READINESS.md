# Moodle Readiness — Healthcare Foundations (hlthcr)

Goal: bring this course to **feature parity with the AI Governance Academy (`aig-crs`)** for Moodle delivery.
A **"Coming Soon" placeholder** already exists in Moodle: course shortname **`hlthcr-foundations`**
(created by `moodle-infra/create-coming-soon-courses.php`).

> Status (2026-06-26): `exports/lms/` is empty — no GIFT/SCORM generated yet. This file is the launch plan.

## Target — what aig-crs delivers in Moodle
1. Per-module **SCORM lesson player** (lesson scenes → quiz); score reports to the gradebook; with **question
   flagging** + a **Google-AI "look it up"** link.
2. **Quizzes → question bank** via **GIFT** (auto-graded MC/TF + essay), with **per-option fact-based
   explanations** (feedback on correct AND incorrect answers).
3. **"Additional Resources"** + **"Stretch & High-Impact Exercises"** per topic — in the player and as Moodle
   **Pages** (module-scoped link names).
4. Moodle **hardening** (disable low-value features; nav override).
5. **`course-manifest.json`** (platform contract) + **`/course-check`** consistency gate.

## What this repo already has
- `content/{questions.yaml, tutorials.yaml, facts.yaml, fact_narrations.yaml}` — content + assessment.
- `scripts/` (audio, excalidraw visuals, export_zip) + a web player (`index.html` / `exports/web`).
- **Gap:** no GIFT/SCORM (`exports/lms` empty), no per-option explanations, no resources/exercises pages.

## Launch steps (run in this repo)
1. **Quizzes → GIFT/CSV/JSON** — aig-crs's converter already supports this repo's schema:
   `python3 ../aig-crs/tools/quiz_to_lms.py hlthcr --hlthcr-root .` → writes `exports/lms/{gift,csv,json}/`.
2. **SCORM player** — adapt `../aig-crs/tools/build_lesson_player.py` to this repo's `scenes/`+`tutorials.yaml`
   workspace (it consumes scenes.yaml + tutorials.yaml + the quiz JSON). Output: per-tutorial SCORM `.zip`
   (lesson + quiz + flagging). Run `--scorm all`.
3. **Per-option explanations** — author `*-explanations` per question (model: `aig-crs/modules/*/04-explanations.yaml`,
   keyed Q1.. with `correct:` + `wrong:`), so feedback is fact-based for every option.
4. **Resources + exercises (optional parity)** — author per-topic resources + stretch exercises, number with
   `../aig-crs/tools/number_items.py`, surface via `build_moodle_pages.py` + `add-content-pages.php`.
5. **Upload** — import the GIFT into the `hlthcr-foundations` question bank; add the SCORM packages per topic
   section; then **remove the "Coming Soon" label** and the placeholder note.
6. **Validate** — add a `.course-check.yml` (scenario orgs, `capstone_count`, `meta_words`) and run `/course-check`.

## Reuse vs. adapt
- **Works cross-repo today:** `quiz_to_lms.py hlthcr` (GIFT), `/course-check` (global skill).
- **Needs a small adapter** (this repo uses `content/`+`scenes/`, not aig-crs's `modules/NN/` layout):
  `build_lesson_player.py`, `build_moodle_pages.py`, `add-content-pages.php`.
- Moodle hardening scripts in `moodle-infra/` are course-agnostic and reusable as-is.
