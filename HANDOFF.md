# HANDOFF — Healthcare Foundations

Running log of autonomous (CIRCA) work. Append-only; newest entries at the bottom.

---

## 2026-06-27 — Sixth pillar: Medicare vs. Medicaid contrast

**Context:** New sixth pillar requested — a contrast/disambiguation layer teaching the
difference between Medicare and Medicaid and their sub-parts. Design brainstormed and
approved; spec at `docs/superpowers/specs/2026-06-27-medicare-medicaid-contrast-pillar-design.md`.

Key decisions:
- Pillar key `contrast`, label "Medicare vs. Medicaid", positioned sixth.
- Self-contained recap + contrast; hybrid section structure (confusion hook → dimension).
- Lean module: 1 tutorial (7 sections) + ~40 questions (15 TF / 25 MCQ).
- `index.html` embeds its own data copy (not generated from YAML) → must update both in lockstep.

### Iteration 1
Completed:
- Wrote approved design spec to `docs/superpowers/specs/`.
- Registered pillar identity: added `contrast` to `meta/course.yaml` pillars and a
  `contrast:` subtopic block to `meta/subtopics.yaml`.
- Created this HANDOFF log.
Issues Found: No formal validation tooling (no tests/lint/build; `validation/` empty).
  Will build a structural traceability validator in a later iteration.
Issues Fixed: n/a (no regressions; YAML parse verified).
Remaining Work: sources/facts research, tutorial, scenes, questions, distribution+CLAUDE.md
  counts, index.html lockstep, validator.
Confidence: 8/10

### Iteration 2
Completed:
- Researched approved CMS/medicare.gov/medicaid.gov sources via WebSearch (direct WebFetch 403s).
- Added 5 sources SRC-CON-001..005 (Part C, Part D, dual-eligible MMCO factsheet, CHIP, Medicaid LTSS).
- Added 10 facts FACT-CON-001..010 (Medicare four parts/C/D, CHIP, LTSS coverage gap, dual eligibility,
  payer-of-last-resort, administration contrast). Single-program basics reused from FACT-PAY-*.
- Noted repo precedent: medicare.gov/medicaid.gov already cited (SRC-PAY-001/004); treated as CMS-operated.
Issues Found: gov sites block automated WebFetch (HTTP 403); used WebSearch on approved domains instead.
Issues Fixed: none (validation PASS: all fact source_ids resolve; all SRC-CON domains approved).
Remaining Work: tutorial, scenes, questions, distribution+CLAUDE.md counts, index.html lockstep, validator.
Confidence: 8/10

### Iteration 3
Completed:
- Added tutorial T-CONTRAST-01 "Medicare vs. Medicaid: Telling Them Apart" (7 sections, hybrid
  confusion-hook -> dimension structure), 6 objectives, 6 summary points, 21 linked_facts.
Issues Found: none.
Issues Fixed: none (validation PASS: 7 sections; all 21 linked_facts resolve; 6 tutorials total).
Remaining Work: scenes, questions, distribution+CLAUDE.md counts, index.html lockstep, validator.
Confidence: 8/10

### Iteration 4
Completed:
- Added 9 scenes SCN-CONTRAST-01-01..09 (1 intro nano-banana, 7 lesson excalidraw, 1 assessment text_only),
  one lesson scene per tutorial section + a recap-table scene; condensed screen_text, per-scene fact links.
Issues Found: none.
Issues Fixed: none (validation PASS: 9 scenes, correct type mix, orders 1..9 contiguous, all fact/tut links resolve).
Remaining Work: questions, distribution+CLAUDE.md counts, index.html lockstep, validator.
Confidence: 8/10

### Iteration 5
Completed:
- Added 40 contrast questions Q-CON-001..040 (15 TF + 25 MCQ) via a generator script
  (scratchpad/gen_questions.py) with a house-style YAML emitter. Each maps to a contrast/PAY fact.
- Caught and fixed an answer-position tell: initial MCQ correct-letter spread was B=20/25. Added a
  deterministic balance() step that relabels option positions (content unchanged) -> A:7 B:6 C:6 D:6.
Issues Found: MCQ correct answers clustered on "B" (position bias a savvy test-taker could exploit).
Issues Fixed: rebalanced via positional relabel; re-validated (keys aligned, no correct-in-wrong-expl,
  all fact_ids resolve, total questions 400 -> 440).
Remaining Work: distribution.yaml counts + CLAUDE.md tables; index.html lockstep; traceability validator.
Confidence: 8/10

### Iteration 6
Completed:
- questions.yaml header -> "440 questions: 135 TF + 305 MCQ" with per-pillar note.
- distribution.yaml (aspirational target) -> total 1040, TF 315, MCQ 725, by_pillar contrast: 40,
  tutorials.contrast: 1; added a comment that contrast is a lean module.
- CLAUDE.md: added Contrast pillar to the §1 intent text and updated the §6 distribution summary.
Issues Found: distribution.yaml is the aspirational target (1000) and never matched the actual built bank
  (400) — kept the two layers distinct rather than conflating them.
Issues Fixed: none (validation PASS: contrast target 40 == actual 40; by_pillar sum == total == types sum == 1040).
Remaining Work: index.html lockstep (embedded JS constants); traceability validator.
Confidence: 8/10

### Iteration 7
Completed:
- Lockstepped the web player (index.html embedded JS) with the YAML via a guarded patch script
  (scratchpad/patch_index.py — every insertion asserts its anchor matches exactly once):
  TUTORIALS +1, TUTORIAL_SECTIONS +1 (7 full section texts), FACT_ORDER +1 (section 15),
  FACTS +10, SCENES +9 (.mp3->.wav, aspect_ratio dropped to match player shape), QUESTIONS +40,
  PILLAR_COLORS/PILLAR_LABELS +contrast, and fixed the hardcoded '125 Facts' -> '135 Facts' (x2).
- Validated with a Node harness (scratchpad/validate_index.js) that extracts and eval()s each const:
  ALL PASS — 6 tutorials, 135 facts, 51 scenes, 440 questions, MCQ option/explanation shapes valid,
  Q->FACTS traceability holds inside the player data.
Issues Found: player MCQ serialization is inconsistent across legacy batches (object vs flat _A/_C/_D
  keys) and '125 Facts' was hardcoded in two spots. Chose the object form; fixed both counts.
Issues Fixed: as above; backups saved in scratchpad (index.html.bak, questions.yaml.bak).
Remaining Work: standing traceability validator (committed deliverable) + full cross-file run.
Confidence: 9/10

### Iteration 8
Completed:
- Added scripts/validate_content.py — a standing traceability validator (fills the empty validation/
  deliverable, CLAUDE.md §7/§13): YAML parse, fact->source, source domain approval, tutorial/scene/
  question -> tutorial/fact links, pillar registration, MCQ structural rules, distribution vs actual.
  Writes validation/validation_report.md and exits non-zero on error.
- First run surfaced a PRE-EXISTING legacy bug (not mine): MCQ Q-CRS-055 (cross_domain) had a garbled
  explanation_incorrect (copy-pasted "digits" text) including a stray 'B:' key for its own correct answer.
  Fixed the source-of-truth questions.yaml with correct A/C/D distractor explanations (B removed).
- Player copy of Q-CRS-055 already renders the correct object-form explanation; its stale flat
  explanation_incorrect_* keys are dead/ignored legacy data — left as-is (cleanup unrelated to this task).
Issues Found: legacy Q-CRS-055 explanation bug (surfaced by the new validator).
Issues Fixed: Q-CRS-055 in questions.yaml; re-validated.
Result: scripts/validate_content.py -> PASS (0 errors, 5 warnings = the five primary pillars built 80/200,
  expected/pre-existing). Node player validation -> ALL PASS. Contrast pillar 40/40.
Remaining Work: media generation for the 9 contrast scenes (Kokoro audio WAVs + scene visuals) — a
  separate resource-heavy pipeline phase (§5, §8a), recommended as the next step; not run autonomously.
Confidence: 9/10

## 2026-06-27 — Sixth pillar COMPLETE

The Medicare-vs-Medicaid contrast pillar is fully built and validated across the whole pipeline:
sources (5) -> facts (10) -> tutorial (1, 7 sections) -> scenes (9) -> questions (40), plus meta
(course/subtopics/distribution), CLAUDE.md, and the web player (index.html embedded JS). Two validators
green. Only follow-up is media generation (audio/visuals) for the new scenes.

### Iteration 9
Completed:
- Generated Kokoro TTS narration for all 9 contrast scenes (af_heart, 24kHz WAV) via
  `python scripts/audio/generate_narration.py --tutorial T-CONTRAST-01`. Lesson scenes narrate full
  tutorial section text (760-977 chars); intro/assessment use short text. Files: media/audio/contrast-01-0[1-9].wav (~19MB).
Issues Found: none.
Issues Fixed: none.
Remaining Work: VISUALS for the 9 contrast scenes (excalidraw lesson diagrams + nano-banana title card)
  — deferred per user choice ("audio now, visuals later"). 8 excalidraw + 1 nano-banana title card needed;
  prompts already specified in scenes.yaml visual_prompt_hint and visual_asset paths (images/contrast-*.png).
Confidence: 9/10

### Iteration 10
Completed:
- Ran `python scripts/generate_visuals.py --tutorial T-CONTRAST-01 --dry-run` (no API spend).
  Result: 8 succeeded / 0 failed (8 visuals = 1 nano-banana title card + 7 excalidraw diagrams;
  scene 9 assessment is text_only and correctly has no visual). All prompts resolve from scenes.yaml
  visual_prompt_hint fields. Reviewed full untruncated prompts with the user.
Issues Found: none.
Issues Fixed: none.
Remaining Work: actual (paid) visual generation via kie.ai — GATED on explicit user go-ahead
  (KIE_AI_API_KEY in .env; ~8 image generations; 3-attempt-per-image regen cap).
Confidence: 9/10

### Iteration 11
Completed:
- User authorized paid generation. Ran `python scripts/generate_visuals.py --tutorial T-CONTRAST-01`
  (kie.ai, same path pillars 1-5 used). 8/8 images generated (v1) + sidecar prompt JSONs.
- Visually QA'd all 8. Result: 4 good, 4 defective (AI text/table corruption on dense diagrams):
  GOOD  -> contrast-title-card (minor imbalance), contrast-who-qualifies, contrast-funding, contrast-dual.
  REGEN -> contrast-coverage (wrong/misspelled title "MEDICAD", stray payor shields),
           contrast-subparts ("FFART B"/"FFECT C", duplicated boxes),
           contrast-cost (generic "System Flow" dominates, Medicaid cost wrong),
           contrast-recap-table (cells shuffled to wrong rows, 3 columns instead of 2, typos).
Issues Found: 4/8 images have garbled text — the failures are all the text-dense/tabular prompts;
  simple 2-element diagrams rendered cleanly.
Issues Fixed: none yet (regen pending).
Remaining Work: regen the 4 defective images. Same-prompt retries will likely fail the same way, so the
  prompts should be simplified/constrained first (fewer boxes; avoid table layout for recap; drop
  cross-pillar 'system flow' framing). Respect the 3-attempt-per-image cap, then pick best + note issues.
Confidence: 8/10

### Iteration 12
Completed:
- Constrained the 4 failing prompts in scenes.yaml (exactly-N-boxes, "two columns only / not a grid",
  "nothing else / no flow chart / no shields", minimal text). Archived the 4 defective v1 images to
  media/images/_archive/contrast-*-v1.png (never delete).
- Regenerated the 4 scenes (attempt 2): all 4 _v2 came out clean:
  coverage_v2 (correct Venn, no stray shields), subparts_v2 (clean 6 boxes; minor: 'C' box outline missing,
  'D D' doubled letter — legible/correct), cost_v2 (two cards, system-flow gone), recap-table_v2 (clean
  two columns, all labels correct, no grid garble). Promoted all 4 _v2 -> base filenames.
- Final: all 8 contrast images are good. 4 kept from v1 (title-card, who-qualifies, funding, dual),
  4 from v2 (coverage, subparts, cost, recap-table). v2 files retained alongside base as record.
Issues Found: subparts_v2 has two cosmetic glitches ('C' box outline, 'D D'); within tolerance, not worth
  a 3rd attempt (risk of regressing the good labels).
Issues Fixed: 4/4 defective images corrected via constrained-prompt regen (1 retry each, under the 3-cap).
Remaining Work: NONE for the sixth pillar. Optional polish: a 3rd pass on subparts for the 'C' box;
  optional rebalance of the title card. Note: scenes.yaml visual_prompt_hint for the 4 regenerated scenes
  now differs from index.html's embedded SCENES hint (generation metadata only, not displayed) — minor drift.
Confidence: 9/10

### Iteration 13
Completed:
- 3rd (final, per cap) regen pass on subparts with a prompt targeting the v2 glitches (four identical
  fully-outlined boxes, each label once). v3 result: fixed the 'D D' doubling ('Part D: Drugs') and gave
  the 'C' box a complete border. Promoted v3 -> active base; archived v2 to _archive. All 3 versions retained.
Issues Found: residual tiny issue in v3 — third box reads 'C. All-in-one' instead of 'Part C:' (dropped the
  word 'Part'); legible and correct, best of the 3 attempts, accepted per the 3-attempt cap.
Issues Fixed: subparts missing-'C'-box-border and 'D D' duplication both resolved.
Remaining Work: NONE. Sixth pillar fully complete (content + player + audio + 8 visuals).
Confidence: 9/10

## 2026-06-27 — Moodle course from the sixth pillar ("Medicare vs. Medicaid: Telling Them Apart")

Task: build a standalone Moodle course for moodle-infra based on JUST the contrast pillar, named as the
contrast ("Medicare vs. Medicaid: Telling Them Apart", shortname medicare-vs-medicaid) — NOT
"Introduction to Medicare/Medicaid". Pillar key 'contrast' stays unchanged in content files.

Environment boundary: the live Moodle import (running moodle-infra/*.php against a running Moodle) cannot
be done here. Deliverables = all importable artifacts (GIFT, rich JSON, SCORM zip, course-manifest.json)
+ catalog registration; the import itself is an ops step on the Moodle host.

### Iteration 1 (Moodle)
Completed:
- Added scripts/build_moodle_course.py — filters questions.yaml to one pillar and reuses
  aig-crs/tools/quiz_to_lms.py (parse_hlthcr + emit_gift/csv/json) without duplicating logic; relabels the
  Moodle category from the fallback "HLTHCR: Contrast" to "Medicare vs. Medicaid".
- Built the question bank: exports/lms/{gift,csv,json}/medicare-vs-medicaid* — 40 Qs (25 MCQ + 15 TF).
Issues Found: converter has no --pillar flag (as predicted); solved by filtering input in the hlthcr-side
  build script (no change to the shared aig-crs tool).
Issues Fixed: none (validation PASS: GIFT braces 40/40 balanced; 25 '=' correct lines + 75 '~' distractors
  + 15 TF inline; per-option '#' feedback present on MCQs; JSON=40; CSV=40).
Remaining Work: SCORM lesson package; course-manifest.json; moodle-infra catalog registration; validation.
Confidence: 9/10

### Iteration 2 (Moodle)
Completed:
- Extended build_moodle_course.py with a SCORM 1.2 build step: self-contained lesson player (intro + 7
  section scenes, each with image + audio) + 40-question quiz with per-option feedback that reports
  score/completion to Moodle via a SCORM API shim. Reused the proven SCORM_MANIFEST + API pattern.
- Audio WAV -> MP3 via ffmpeg (q:a 5): package is 8.7 MB (vs ~25 MB raw), Moodle-uploadable.
- Output: exports/lms/scorm/medicare-vs-medicaid.zip (imsmanifest.xml + index.html + scorm_api.js +
  8 images + 8 audio).
Issues Found: none.
Issues Fixed: none. Validation PASS: 19 zip entries; imsmanifest.xml well-formed XML; all image/audio refs
  in index.html resolve; embedded COURSE parses (8 scenes, 40 questions); player JS + scorm_api.js both
  `node --check` SYNTAX OK.
Remaining Work: course-manifest.json; moodle-infra catalog registration; final validation (browser smoke).
Confidence: 9/10

### Iteration 3 (Moodle)
Completed:
- Added a `manifest` step to build_moodle_course.py; derives counts from the data and emits
  exports/lms/medicare-vs-medicaid.manifest.json (1 module: M1.lesson 8 scenes + M1.quiz 40 Q,
  passMark 0.8, delivery.player=scorm, moodle.gift path, contentVersion=git sha).
Issues Found: none.
Issues Fixed: none. Validation PASS: jsonschema.validate against moodle-infra/course-manifest.schema.json
  succeeded; all referenced artifact paths (gift/scorm/json) exist on disk.
Remaining Work: moodle-infra catalog registration; final validation.
Confidence: 9/10

### Iteration 4 (Moodle)
Completed:
- Registered the course in moodle-infra/catalog.json: new entry shortname 'medicare-vs-medicaid',
  fullname 'Medicare vs. Medicaid: Telling Them Apart', repo 'hlthcr', status 'coming-soon' with a note
  that artifacts are built (GIFT+SCORM+manifest) and import is pending; notes it supersedes the
  intro-medicare/intro-medicaid placeholders (left in place, not deleted).
Issues Found: status is 'coming-soon' not 'live' because the live Moodle import (running the PHP against a
  running Moodle) can't be done in this environment — honest boundary.
Issues Fixed: none. Validation PASS: catalog.json valid JSON (7 courses); create-coming-soon-courses.php
  reads catalog.json so the placeholder provisions from it.
Remaining Work: final consolidated validation.
Confidence: 9/10

### Iteration 5 (Moodle)
Completed:
- Rebuilt all artifacts (idempotent) and ran consolidated cross-artifact validation.
Issues Found: none.
Issues Fixed: none. Validation PASS: question count == 40 across source/JSON/GIFT/manifest; SCORM zip has
  index.html+imsmanifest.xml+scorm_api.js + 8 images + 8 audio; catalog.json contains the course;
  scripts/validate_content.py still PASS (content pipeline unaffected).
Remaining Work: NONE buildable here. ONLY remaining step is the live Moodle import (ops, needs running
  Moodle): import exports/lms/gift/medicare-vs-medicaid.gift into the course question bank, add the SCORM
  zip as an activity, flip catalog status coming-soon -> live. Optional: browser smoke-test of the SCORM
  player; retire intro-medicare/intro-medicaid placeholders.
Confidence: 9/10
