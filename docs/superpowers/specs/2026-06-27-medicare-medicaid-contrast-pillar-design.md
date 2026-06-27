---
title: "Sixth Pillar — Medicare vs. Medicaid Contrast"
date: 2026-06-27
status: approved
generated_by: cc
---

# Sixth Pillar — Medicare vs. Medicaid Contrast

## Goal

Add a sixth content pillar that resolves the most common confusion in foundational
healthcare: the difference between **Medicare** and **Medicaid** and their sub-parts.
The learner should leave able to tell the two programs apart on every axis that
matters. Pedagogy is **learning by contrast**: a self-contained recap of each program
followed by a side-by-side comparison.

## Pillar identity

- **Key:** `contrast`
- **Label:** "Medicare vs. Medicaid"
- **Position:** sixth pillar, after `cross_domain`
- **Color:** violet/purple (distinct from the existing five pillar colors)
- **Role:** capstone disambiguation. Self-contained recap + contrast — stands alone
  but rewards prior Payor exposure. Intentionally **leaner** than the other pillars
  because it recaps known material.

## Tutorial — `T-CONTRAST-01` "Medicare vs. Medicaid: Telling Them Apart"

Seven sections, hybrid structure: each section opens with a **confusion hook** and
resolves it with a **dimension contrast**.

| # | Confusion hook | Dimension delivered |
|---|----------------|--------------------|
| S1 | "Old people or poor people?" | Who qualifies (age/disability vs. income) |
| S2 | "Who's behind each one?" | Funding + administration (federal/CMS vs. fed+state) |
| S3 | "Do they cover the same things?" | What's covered |
| S4 | "A, B, C, D — whose parts are those?" | Sub-parts: Medicare A/B/C/D vs. Medicaid + CHIP |
| S5 | "Is it free?" | Cost to the patient (premiums/deductibles vs. little/no cost) |
| S6 | "Can you have both at once?" | Dual eligibility (dual-eligibles, who pays first) |
| S7 | "The six differences at a glance" | Recap + side-by-side comparison table |

## Questions — `Q-CON-001…040`

- Volume: **~40** (15 TF / 25 MCQ) — leaner than the 80-per-pillar of the other five.
- Each carries `pillar: contrast`, `tutorial_id: T-CONTRAST-01`, and a `fact_id`.
- Designed to **test the distinction**, not each program in isolation.
- Rules (CLAUDE.md §5): one concept each, no trick questions, MCQ = 1 correct + 3
  plausible distractors, no "all of the above", TF unambiguous.

## Facts & Sources (traceability — CLAUDE.md §4, §13)

- **Reuse** existing `FACT-PAY-*` Medicare/Medicaid facts where they apply.
- **Add** `FACT-CON-*` for new contrast-specific points (dual eligibility, CHIP,
  who-pays-first between the two programs).
- **Add** `SRC-CON-*` source entries — **approved domains only**: cms.gov,
  healthcare.gov, hhs.gov. (`medicare.gov` / `medicaid.gov` are CMS-operated; cite via
  cms.gov equivalents to stay strictly inside the approved-source list.)

## Scenes & Audio (CLAUDE.md §8, §8a)

- `SCN-CONTRAST-01-01..09`: 1 intro + 7 lesson + 1 assessment, matching the existing
  scene schema (`screen_text`, `visual_asset`, `visual_type`, `audio_asset`, `layout`).
- Lesson scenes narrate full section text; audio via Kokoro (`af_heart`, 24kHz WAV).
- S7 gets a comparison-table visual (excalidraw, house style).

## Metadata & player edits — the lockstep

The web player (`index.html`) embeds its own copy of the data as JS constants and is
**not generated from the YAML**. Both must be updated together or they drift.

- **YAML:** `course.yaml` (add pillar), `subtopics.yaml` (new `contrast:` block),
  `distribution.yaml` (add `contrast: 40`; totals 400→440, TF 120→135, MCQ 280→305) —
  counts updated only after questions exist.
- **`index.html`:** extend `TUTORIALS`, `TUTORIAL_SECTIONS`, `QUESTIONS`, `FACTS`,
  `SCENES`, `PILLAR_COLORS`, `PILLAR_LABELS`.
- **`CLAUDE.md`:** add the sixth pillar to the §1 pillar table and §6 distribution summary.

## Validation (CLAUDE.md §7)

No formal test/lint/build tooling exists. Validation is structural, via a new script:
- every YAML file parses;
- every question's `fact_id` and `tutorial_id` resolve to real entries;
- the new pillar is registered in `course.yaml`;
- declared `distribution.yaml` counts match actual question counts;
- every `SRC-CON-*` URL is on an approved domain.

## Build order (CIRCA iterations)

1. Spec + HANDOFF + register pillar identity (course.yaml, subtopics.yaml).
2. Research approved sources → add `SRC-CON-*` and `FACT-CON-*`.
3. Add tutorial `T-CONTRAST-01`.
4. Add scenes `SCN-CONTRAST-01-*`.
5. Add ~40 questions `Q-CON-*`.
6. Update `distribution.yaml` counts + `CLAUDE.md` tables.
7. Update `index.html` embedded constants.
8. Build traceability validator; run full validation; fix issues.
