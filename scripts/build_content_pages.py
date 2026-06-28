#!/usr/bin/env python3
"""
build_content_pages.py — Generate exports/moodle/content-pages.json for the
Healthcare Foundations Moodle course (consumed by moodle-infra/add-content-pages.php,
which creates a "M{n}: Additional Resources" + "M{n}: Stretch & High-Impact Exercises"
Page per module section).

- Resources: the authoritative approved sources for each module's pillar (sources.yaml).
- Exercises: authored foundational stretch prompts per module.

Module order mirrors build_moodle_course.py's hlthcr-foundations course.

generated_by: cc
"""
import html
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

# (tutorial_id, pillar==source domain) in course/module order.
MODULES = [
    ("T-PAYOR-01", "payor"), ("T-PROVIDER-01", "provider"), ("T-PATIENT-01", "patient"),
    ("T-DATA-01", "data"), ("T-CROSS-01", "cross_domain"), ("T-CONTRAST-01", "contrast"),
]

# Authored foundational "stretch" exercises per pillar (HTML <li> bodies).
EXERCISES = {
    "payor": [
        "For three people — a 70-year-old retiree, a low-income parent of two, and a salaried "
        "software engineer — decide which payor category (government, commercial, or self-pay) most "
        "likely covers each, and justify your choice.",
        "A patient has both an employer plan and Medicare. Explain coordination of benefits: which "
        "is the primary payer, and what does the secondary payer do?",
    ],
    "provider": [
        "Classify five entities — a general hospital, a wheelchair supplier, an air ambulance, an "
        "independent lab, and a physician office — as a Medicare 'provider' or 'supplier', and name "
        "the claim form each uses (CMS-1500/837P vs CMS-1450/837I).",
        "Trace how a newly licensed physician enrolls to bill Medicare, naming each step (NPI → PECOS "
        "→ MAC) and the form they file.",
    ],
    "patient": [
        "A 24-year-old is covered under a parent's plan. Identify who is the subscriber and who is the "
        "dependent, and list two life events that would open a Special Enrollment Period for them.",
        "Given a plan with a $1,000 deductible, 20% coinsurance, and a $6,000 out-of-pocket maximum, "
        "work out what the patient pays for a single $3,000 covered procedure (assume the deductible is "
        "not yet met).",
    ],
    "data": [
        "Take a simple clinical scenario (e.g., a knee X-ray for knee pain) and identify which code "
        "types appear on the claim — the ICD-10-CM diagnosis and the CPT/HCPCS procedure — and explain "
        "why both are required.",
        "Decide whether each item is PHI: a patient's name alone, a lab result linked to a patient, and "
        "a de-identified count of flu cases. Name the HIPAA rule that governs PHI.",
    ],
    "cross_domain": [
        "Walk a claim end-to-end: eligibility check (270/271) → claim submission (837) → adjudication → "
        "remittance (835)/EOB. Identify one point where the claim could be rejected and one where it "
        "could be denied, and explain the difference.",
        "Explain how a clearinghouse and the National Provider Identifier (NPI) together let any provider "
        "submit a claim to any health plan.",
    ],
    "contrast": [
        "For four people — a child in a family earning just above the Medicaid limit, a 70-year-old "
        "retiree, a low-income senior, and a low-income adult under 65 — decide whether each is best "
        "matched to Medicare, Medicaid, CHIP, or dual eligibility, and justify each.",
        "For a dual-eligible individual, explain which program pays first, which is the payer of last "
        "resort, and name a major category of care (long-term services and supports) that Medicaid "
        "covers but Original Medicare generally does not.",
    ],
}


def esc(s):
    return html.escape(str(s), quote=False)


def resources_html(title, sources):
    parts = [f"<h2>Additional Resources — {esc(title)}</h2>",
             "<p>Authoritative, approved sources (HHS / CMS / CDC / healthcare.gov and CMS-operated "
             "Medicare.gov &amp; Medicaid.gov) that deepen this module. Each links to the primary source.</p>",
             "<ul>"]
    for s in sources:
        kp = (s.get("key_points") or [""])[0]
        parts.append(
            f'<li><strong>{esc(s["title"])}</strong> — {esc(kp)} '
            f'<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["url"])}</a></li>')
    parts.append("</ul>")
    return "".join(parts)


def exercises_html(title, pillar):
    parts = [f"<h2>Stretch &amp; High-Impact Exercises — {esc(title)}</h2>",
             "<p>Apply this module's ideas to realistic situations. These are foundational — they "
             "reinforce the core distinctions rather than introduce advanced topics.</p>",
             "<ol>"]
    for ex in EXERCISES[pillar]:
        parts.append(f"<li>{esc(ex)}</li>")
    parts.append("</ol>")
    return "".join(parts)


def main():
    tuts = {t["tutorial_id"]: t for t in yaml.safe_load(open(ROOT / "content" / "tutorials.yaml"))["tutorials"]}
    sources = yaml.safe_load(open(ROOT / "sources" / "sources.yaml"))["sources"]
    by_domain = {}
    for s in sources:
        by_domain.setdefault(s.get("domain"), []).append(s)

    modules = []
    for i, (tid, pillar) in enumerate(MODULES, 1):
        title = tuts[tid]["title"]
        modules.append({
            "num": i,
            "resources": resources_html(title, by_domain.get(pillar, [])),
            "exercises": exercises_html(title, pillar),
        })

    out = ROOT / "exports" / "moodle" / "content-pages.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"modules": modules}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)} — {len(modules)} modules")
    for m in modules:
        src_n = m["resources"].count("<li>")
        ex_n = m["exercises"].count("<li>")
        print(f"  M{m['num']}: {src_n} resource links, {ex_n} exercises")


if __name__ == "__main__":
    main()
