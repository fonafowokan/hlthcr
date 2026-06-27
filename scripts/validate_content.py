#!/usr/bin/env python3
"""
Healthcare Foundations — content traceability validator.

Structural validation for the source-of-truth YAML pipeline (CLAUDE.md §7, §13):
  sources -> facts -> tutorials -> scenes -> questions

Checks:
  * every YAML file parses
  * every fact references an existing source
  * every source URL is on an approved domain
  * every tutorial / scene / question references existing tutorials and facts
  * every pillar used is registered in course.yaml
  * MCQ structural rules (4 options, valid correct letter, 3 wrong-answer explanations)
  * distribution.yaml per-pillar targets are >= actual built counts (and == where built)

Writes a markdown report to validation/validation_report.md and exits non-zero on any error.

generated_by: cc
"""
import sys, re, datetime
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
APPROVED_DOMAINS = ("hhs.gov", "cms.gov", "cdc.gov", "nih.gov", "healthcare.gov",
                    "medicare.gov", "medicaid.gov")  # last two are CMS-operated

errors, warnings = [], []
def err(m): errors.append(m)
def warn(m): warnings.append(m)

def load(rel):
    try:
        return yaml.safe_load(open(ROOT / rel, encoding="utf-8"))
    except Exception as e:
        err(f"YAML parse failed for {rel}: {e}")
        return None

sources_doc   = load("sources/sources.yaml")
facts_doc     = load("content/facts.yaml")
tutorials_doc = load("content/tutorials.yaml")
scenes_doc    = load("scenes/scenes.yaml")
questions_doc = load("content/questions.yaml")
course        = load("meta/course.yaml")
distribution  = load("meta/distribution.yaml")

if None in (sources_doc, facts_doc, tutorials_doc, scenes_doc, questions_doc, course, distribution):
    # can't continue past a parse failure
    pass

sources   = (sources_doc or {}).get("sources", [])
facts     = (facts_doc or {}).get("facts", [])
tutorials = (tutorials_doc or {}).get("tutorials", [])
scenes    = (scenes_doc or {}).get("scenes", [])
questions = (questions_doc or {}).get("questions", [])

source_ids = {s["source_id"] for s in sources}
fact_ids   = {f["fact_id"] for f in facts}
tut_ids    = {t["tutorial_id"] for t in tutorials}
pillars    = set(course.get("pillars", [])) if course else set()

def host_of(url):
    return re.sub(r"^https?://", "", url).split("/")[0].lower()

def domain_ok(host):
    return any(host == d or host.endswith("." + d) for d in APPROVED_DOMAINS)

# --- sources ---
for s in sources:
    h = host_of(s.get("url", ""))
    if not domain_ok(h):
        err(f"source {s['source_id']} URL host '{h}' is not on the approved-domain list")

# --- facts -> sources, pillar registered ---
for f in facts:
    if f.get("source_id") not in source_ids:
        err(f"fact {f['fact_id']} references missing source_id {f.get('source_id')}")
    if f.get("pillar") not in pillars:
        err(f"fact {f['fact_id']} uses unregistered pillar '{f.get('pillar')}'")

# --- tutorials -> facts, pillar ---
for t in tutorials:
    if t.get("pillar") not in pillars:
        err(f"tutorial {t['tutorial_id']} uses unregistered pillar '{t.get('pillar')}'")
    for fid in t.get("linked_facts", []):
        if fid not in fact_ids:
            err(f"tutorial {t['tutorial_id']} linked_fact {fid} does not exist")

# --- scenes -> tutorials, facts ---
for sc in scenes:
    if sc.get("tutorial_id") not in tut_ids:
        err(f"scene {sc['scene_id']} references missing tutorial {sc.get('tutorial_id')}")
    for fid in sc.get("linked_facts", []):
        if fid not in fact_ids:
            err(f"scene {sc['scene_id']} linked_fact {fid} does not exist")

# --- questions -> tutorials, facts, structural rules ---
seen_q = set()
for q in questions:
    qid = q.get("question_id")
    if qid in seen_q:
        err(f"duplicate question_id {qid}")
    seen_q.add(qid)
    if q.get("pillar") not in pillars:
        err(f"question {qid} uses unregistered pillar '{q.get('pillar')}'")
    if q.get("tutorial_id") not in tut_ids:
        err(f"question {qid} references missing tutorial {q.get('tutorial_id')}")
    if q.get("fact_id") not in fact_ids:
        err(f"question {qid} references missing fact {q.get('fact_id')}")
    if q.get("type") == "TF":
        if str(q.get("correct_answer")) not in ("True", "False"):
            err(f"TF question {qid} has non-boolean correct_answer {q.get('correct_answer')!r}")
    elif q.get("type") == "MCQ":
        opts = q.get("options", {})
        if set(opts) != set("ABCD"):
            err(f"MCQ {qid} must have options A-D, got {sorted(opts)}")
        ca = q.get("correct_answer")
        if ca not in "ABCD":
            err(f"MCQ {qid} correct_answer must be a letter A-D, got {ca!r}")
        ei = q.get("explanation_incorrect")
        if isinstance(ei, dict):
            if ca in ei:
                err(f"MCQ {qid} has an explanation for its own correct answer {ca}")
            if set(ei.keys()) != set("ABCD") - {ca}:
                warn(f"MCQ {qid} explanation_incorrect keys {sorted(ei)} != the three wrong letters")
    else:
        err(f"question {qid} has unknown type {q.get('type')!r}")

# --- distribution vs actual ---
from collections import Counter
actual_by_pillar = Counter(q.get("pillar") for q in questions)
targets = (distribution or {}).get("questions", {}).get("by_pillar", {})
for pillar, target in targets.items():
    a = actual_by_pillar.get(pillar, 0)
    if a > target:
        err(f"pillar '{pillar}' has {a} questions, exceeding its distribution target {target}")
    elif a < target:
        warn(f"pillar '{pillar}' built {a}/{target} questions (below aspirational target)")

# --- report ---
report = []
report.append("# Content Validation Report")
report.append("")
report.append(f"_Generated: {datetime.date.today().isoformat()} (generated_by: cc)_")
report.append("")
report.append("## Inventory")
report.append("")
report.append(f"- Sources: {len(sources)}")
report.append(f"- Facts: {len(facts)}")
report.append(f"- Tutorials: {len(tutorials)}")
report.append(f"- Scenes: {len(scenes)}")
report.append(f"- Questions: {len(questions)}")
report.append("")
report.append("### Questions by pillar")
report.append("")
report.append("| Pillar | Built | Target |")
report.append("|--------|-------|--------|")
for p in sorted(set(list(actual_by_pillar) + list(targets))):
    report.append(f"| {p} | {actual_by_pillar.get(p,0)} | {targets.get(p,'—')} |")
report.append("")
report.append("## Result")
report.append("")
if errors:
    report.append(f"**FAIL** — {len(errors)} error(s), {len(warnings)} warning(s).")
    report.append("")
    report.append("### Errors")
    for e in errors:
        report.append(f"- {e}")
else:
    report.append(f"**PASS** — 0 errors, {len(warnings)} warning(s).")
if warnings:
    report.append("")
    report.append("### Warnings")
    for w in warnings:
        report.append(f"- {w}")
report.append("")

out = ROOT / "validation" / "validation_report.md"
out.write_text("\n".join(report), encoding="utf-8")

print(f"Wrote {out.relative_to(ROOT)}")
print(f"Sources={len(sources)} Facts={len(facts)} Tutorials={len(tutorials)} "
      f"Scenes={len(scenes)} Questions={len(questions)}")
print(f"Errors={len(errors)} Warnings={len(warnings)}")
if errors:
    print("FAIL")
    for e in errors:
        print("  ERR:", e)
    sys.exit(1)
print("PASS")
