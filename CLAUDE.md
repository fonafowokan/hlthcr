# HLTHCR — Claude Code Operating Rules

## 1. Project Intent

Build a **Healthcare Foundations Learning Product** — a tutorial-first, assessment-backed course covering four pillars of introductory healthcare knowledge:

| Pillar | Focus |
|--------|-------|
| **Payor** | Government (Medicare A/B, Medicaid), Commercial (Aetna, BCBS, UHC), Self-pay |
| **Provider** | Physician offices, hospitals, DME, transportation (air ambulance, taxi), ancillary |
| **Patient** | Subscriber vs dependent, eligibility, rights, consent |
| **Healthcare Data** | ICD-9/10, HCPCS, CPT, in-network/out-of-network, PHI, HIPAA |

Plus a **Cross-Domain** pillar covering claims flow, billing interactions, eligibility checks, and HIPAA across entities.

**Level**: Foundational only. Plain language. No advanced topics, edge cases, or jargon overload.

**Target outcome**: A learner who finishes this can explain how the healthcare system works at a basic level — who pays, who provides, who receives, and what data is exchanged.

## 2. Deliverables

| Artifact | Description |
|----------|-------------|
| Tutorials | 40–60 plain-language lesson modules (teach before test) |
| Question Bank | 1000 questions (300 T/F + 700 MCQ), 200 per pillar |
| Answer Key | Correct answers only |
| Explained Key | Correct + wrong answer explanations |
| Source Map | Every question traceable to a fact and source |
| Visual Pack | Consistent artwork, diagrams, icons per style guide |
| Audio Narration | Pre-recorded WAV per scene via Kokoro TTS (local, free) |
| Scenes | Screen-level definitions linking text, visuals, and audio |
| Video Export | MP4 lessons for Udemy/Coursera portability |

## 3. Architecture (Content Pipeline)

```
Sources (authoritative only)
  -> Facts (atomic, traceable)
    -> Tutorials (grouped, plain-language lessons)
      -> Scenes (screen text + visual + audio)
        -> Questions (assess understanding)
          -> Answer Keys + Explanations
```

Every question must map to a `tutorial_id` and `fact_id`. No hallucinated content.

## 4. Approved Sources

CC must search **only** these for content:
- hhs.gov
- cms.gov
- cdc.gov
- nih.gov
- healthcare.gov
- Peer-reviewed summaries (no blogs)

## 5. Question Design Rules

- **MCQ**: 1 correct answer, 3 plausible distractors (same category). No "all of the above."
- **True/False**: Unambiguous. No double negatives.
- **Foundational filter**: Would a beginner need to know this to understand how the system works?
- One concept per question.
- No trick questions, no multi-step reasoning, no "best answer" ambiguity.

## 6. Distribution Rules

See `meta/distribution.yaml` for exact numbers. Summary:

- 1000 total: 300 T/F + 700 MCQ
- 200 per pillar (Payor, Provider, Patient, Data, Cross-Domain)
- 40–60 tutorials, 3–5 scenes each

## 7. Project Structure

```
/healthcare-foundations/
  /content/          # facts.yaml, tutorials.yaml, questions.yaml
  /media/
    /images/         # artwork, diagrams, icons
    /audio/          # narration MP3s
    /video/          # lesson MP4s
  /scenes/           # scenes.yaml
  /sources/          # sources.yaml
  /exports/
    /web/            # web app build
    /video/          # stitched lesson videos
    /lms/            # Udemy/Coursera packages
  /meta/             # course.yaml, distribution.yaml, style_guide.yaml, subtopics.yaml
  /validation/       # validation reports
```

## 8. Delivery Model

1. **Web server first** — lesson player with tutorial, visuals, audio controls, quiz
2. **Video export** — MP4 lessons with synced narration + captions for marketplace portability
3. **Platform publish** — Udemy (HD video + audio required, 30min minimum) and Coursera (module-based)

Build as **modular lesson scenes** — one canonical source that drives web pages, narrated videos, slide exports, and LMS uploads.

## 8a. Audio Pipeline

**Engine**: Kokoro TTS (hexgrad/Kokoro-82M) — local, open-source, zero cost.

| Voice | Description |
|-------|-------------|
| `af_heart` | American female, warm and clear (default) |
| `af_nova` | American female, bright and energetic |
| `am_michael` | American male, steady and professional |
| `bm_george` | British male, calm and measured |

**Generation**: `python scripts/audio/generate_narration.py`
- Reads scenes.yaml + tutorials.yaml
- Lesson scenes use full tutorial section text (not condensed screen_text)
- Outputs WAV at 24kHz to `media/audio/`
- Supports per-scene, per-tutorial, or full-batch generation

## 9. Shared Folder

All generated documents (docx, pdf, exports) saved to:

```
/home/femi/projects/shared/HLTHCR/
```

## 10. Context Window Management

200k token context window. Proactive warnings at:
- **20% remaining** — flag to user, suggest summarising completed work
- **40% remaining** — recommend closing non-essential context
- **60% remaining** — normal awareness
- **80% remaining** — no action needed

## 11. Conventions

- Never delete files — archive instead
- Never modify `> [!human]` blocks
- Commit changes only when explicitly asked
- All CC-created files should include `generated_by: cc` in frontmatter where applicable
- Files may exceed 2,000 words if warranted
- Foundational level only — if content is not essential to understanding how healthcare works at a basic level, exclude it

## 12. Build Phases

| Phase | Task |
|-------|------|
| 1 | Source harvest — structured notes from approved sites |
| 2 | Fact extraction — atomic facts, one per statement, traceable |
| 3 | Tutorial generation — group facts into plain-language lessons |
| 4 | Scene generation — one per tutorial section (text + visual ref + audio ref) |
| 5 | Audio script generation — narration scripts per scene |
| 6 | Question generation — enforce distribution rules |
| 7 | Validation — accuracy, duplication, coverage, traceability |

## 13. Governance

| Risk | Control |
|------|---------|
| Hallucinated content | Source-only fact extraction |
| Regulatory error | Tag + validate HIPAA-specific questions |
| Bias / ambiguity | Validation pass |
| Drift over time | Versioned runs |
| Audit need | Source traceability (question -> fact -> source) |
