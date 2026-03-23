#!/usr/bin/env python3
"""Fix questions.yaml: flatten explanation_incorrect keys -> nested dict, replace duplicate Q-CRS-057."""

import yaml
import sys
import copy
from collections import Counter

# Preserve YAML formatting
class QuotedStr(str):
    pass

def quoted_str_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")

yaml.add_representer(QuotedStr, quoted_str_representer)

INPUT = 'content/questions.yaml'

with open(INPUT) as f:
    raw = f.read()

data = yaml.safe_load(raw)
questions = data['questions']

# --- Issue 1: Fix flat explanation_incorrect_X keys ---
flat_keys_fixed = 0
for q in questions:
    flat = {}
    for letter in ['A', 'B', 'C', 'D']:
        key = f'explanation_incorrect_{letter}'
        if key in q:
            flat[letter] = q.pop(key)

    if flat:
        flat_keys_fixed += 1
        existing = q.get('explanation_incorrect')
        if existing and isinstance(existing, dict):
            # Merge: flat keys take precedence
            existing.update(flat)
        else:
            q['explanation_incorrect'] = flat

print(f"Fixed flat explanation_incorrect keys on {flat_keys_fixed} questions")

# --- Issue 2: Replace duplicate Q-CRS-057 ---
for i, q in enumerate(questions):
    if q['question_id'] == 'Q-CRS-057':
        questions[i] = {
            'question_id': 'Q-CRS-057',
            'type': 'MCQ',
            'pillar': 'cross_domain',
            'tutorial_id': 'T-CROSS-01',
            'fact_id': 'FACT-CRS-015',
            'question': 'What role does a healthcare clearinghouse play in the claims process?',
            'options': {
                'A': 'It directly pays providers for services rendered',
                'B': 'It converts non-standard claim data into standard HIPAA formats for submission to payors',
                'C': 'It determines whether a patient is eligible for coverage',
                'D': 'It assigns diagnosis and procedure codes to patient encounters',
            },
            'correct_answer': 'B',
            'explanation_correct': (
                'A healthcare clearinghouse receives claims and other transactions from providers, '
                'converts them from non-standard formats into the standardized electronic formats '
                'required by HIPAA, and forwards them to the appropriate payor.'
            ),
            'explanation_incorrect': {
                'A': 'Clearinghouses do not pay providers; payors (health plans) are responsible for reimbursement.',
                'C': 'Eligibility determination is performed by the health plan, not the clearinghouse.',
                'D': 'Coding is performed by the provider or medical coder, not by the clearinghouse.',
            },
            'regulatory_tags': ['HIPAA'],
            'difficulty': 'basic',
        }
        print("Replaced Q-CRS-057 with new clearinghouse question (FACT-CRS-015)")
        break

# --- Write back ---
with open(INPUT, 'w') as f:
    f.write("# Healthcare Foundations — Question Bank\n")
    f.write("# 400 questions: 120 TF + 280 MCQ\n\n")
    yaml.dump(
        data, f,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )

print(f"Wrote {INPUT}")

# --- Validation ---
print("\n=== VALIDATION ===")
with open(INPUT) as f:
    data2 = yaml.safe_load(f)

qs = data2['questions']
print(f"Total questions: {len(qs)}")

# Check flat keys
flat_remaining = sum(1 for q in qs for k in q if k.startswith('explanation_incorrect_'))
print(f"Questions with flat explanation_incorrect_X keys: {flat_remaining}")

# Check nested explanation_incorrect
missing_nested = sum(1 for q in qs if not isinstance(q.get('explanation_incorrect'), (dict, str)))
# TF questions have string explanation_incorrect, MCQ have dict
no_explanation = sum(1 for q in qs if 'explanation_incorrect' not in q or q['explanation_incorrect'] is None)
print(f"Questions missing explanation_incorrect: {no_explanation}")

# Duplicate question texts
texts = [q['question'] for q in qs]
text_counts = Counter(texts)
dupes = {t: c for t, c in text_counts.items() if c > 1}
print(f"Duplicate question texts: {len(dupes)}")
for t, c in dupes.items():
    ids = [q['question_id'] for q in qs if q['question'] == t]
    print(f"  [{c}x] {ids}: {t[:80]}")

# Distribution
pillar_counts = Counter(q['pillar'] for q in qs)
print(f"\nPillar distribution:")
for p, c in sorted(pillar_counts.items()):
    print(f"  {p}: {c}")

type_counts = Counter(q['type'] for q in qs)
print(f"\nType distribution:")
for t, c in sorted(type_counts.items()):
    print(f"  {t}: {c}")

# Summary checks
all_pass = True
if len(qs) != 400:
    print(f"\nFAIL: Expected 400 questions, got {len(qs)}")
    all_pass = False
if flat_remaining != 0:
    print(f"\nFAIL: {flat_remaining} flat keys remain")
    all_pass = False
if no_explanation != 0:
    print(f"\nFAIL: {no_explanation} missing explanation_incorrect")
    all_pass = False
if dupes:
    print(f"\nFAIL: {len(dupes)} duplicate question texts")
    all_pass = False
if not all(c == 80 for c in pillar_counts.values()):
    print(f"\nFAIL: Pillar distribution not 80 each")
    all_pass = False
if type_counts.get('MCQ', 0) != 280 or type_counts.get('TF', 0) != 120:
    print(f"\nFAIL: Type distribution not 280 MCQ + 120 TF")
    all_pass = False

if all_pass:
    print("\nALL CHECKS PASSED")
