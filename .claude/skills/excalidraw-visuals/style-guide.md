# Excalidraw Visuals Style Guide — Healthcare Foundations

This is the definitive visual specification for all AI-generated Excalidraw-style visuals in the hlthcr project. Every detail here exists to reduce variance between generations.

## The Golden Rule

**Pass the style reference image on EVERY generation.** This is the single biggest lever for visual consistency. The style reference lives at:

```
brand-assets/excalidraw-style-reference.png
```

Always include: `--input "brand-assets/excalidraw-style-reference.png"`

---

## Font Specification

**Target font feel:** Neat architect's handwriting. Not sloppy, not perfect. Consistent letter sizes, slightly rounded strokes, medium weight. Think: a designer sketching on a whiteboard with a thick marker -- legible, intentional, but clearly hand-drawn.

**Prompt language to use every time:**
```
All text uses neat, consistent architect-style handwriting -- legible, slightly rounded letters with medium stroke weight. Letter sizes are uniform within each label. Titles are bold and larger. Body labels are smaller but equally neat. This is NOT sloppy handwriting -- it looks like a designer wrote it with a thick marker.
```

**What to avoid in prompts:**
- Never say "Comic Sans", "Comic Neue", or "Virgil"
- Never say "messy" or "loose" handwriting
- Never say "handwritten font" without specifying the style

---

## Color System

Colors are assigned by **pillar meaning**, not randomly.

### Primary Palette (Healthcare Themed)

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Payor | Soft blue | #a5d8ff | Insurance, payors, coverage, government programs |
| Provider | Teal | #81D4C2 | Hospitals, doctors, DME, transport, care delivery |
| Patient | Warm yellow | #ffec99 | Patients, subscribers, dependents, rights |
| Data | Light purple | #d0bfff | Coding, HIPAA, PHI, EHR, security |
| Warning/attention | Coral/salmon | #ffa8a8 | Alerts, problems, pain points |
| Text | Dark charcoal | #343a40 | All text and labels |
| Lines/arrows | Dark gray | #495057 | All connector lines, arrows, borders |
| Background | White | #ffffff | Always clean white, no texture |

### Color Assignment Rules

- **Payor elements:** Always soft blue (#a5d8ff)
- **Provider elements:** Always teal (#81D4C2)
- **Patient elements:** Always warm yellow (#ffec99)
- **Data elements:** Always light purple (#d0bfff)
- **Cross-domain flows:** Use pillar colors in sequence (e.g., patient yellow -> provider teal -> payor blue)
- **Comparisons:** Coral (old/bad) vs Teal (new/good)
- **Hierarchies:** Blue (top) -> Teal (middle) -> Yellow (bottom)

Never let the model choose colors. Always specify: "The [element] box is filled with teal (#81D4C2)."

---

## Shape Specification

### Boxes/Containers
- Rounded rectangles with visible corner rounding
- 2-3px dark gray (#495057) stroke/outline
- Pastel fill from the color palette above
- Consistent size for elements at the same hierarchy level
- Generous internal padding around text

### Arrows/Connectors
- Hand-drawn style -- slightly curved or wobbly, not ruler-straight
- Dark gray (#495057) stroke, 2px weight
- Arrowheads are simple triangles, not ornate
- Arrows flow in clear, readable directions (left-to-right or top-to-bottom preferred)

### Circles
- Used sparingly for numbered steps or key focal points
- Same stroke and fill rules as boxes
- Keep small to medium size

---

## Healthcare Icon Vocabulary

| Concept | Icon | Notes |
|---------|------|-------|
| Payor / Insurance | Shield with $ | Represents coverage/protection |
| Medicare | Shield with cross + "M" | Government program |
| Provider / Hospital | Building with cross | Facility |
| Provider / Doctor | Stick figure + stethoscope | Individual provider |
| DME | Wheelchair or crutch outline | Equipment |
| Ambulance | Simple van with cross | Transport provider |
| Patient | Plain stick figure | Person receiving care |
| Family / Dependents | Tall + short stick figures | Subscriber + dependent |
| Medical Record / EHR | Document with folded corner | Data artifact |
| HIPAA / Security | Lock icon | Privacy/protection |
| Coding (ICD/CPT) | Document with # | Classification |
| Claim | Document with right arrow | Submission |
| Payment / EOB | Dollar sign in circle | Financial |
| Prescription | Rx symbol | Medication |

### People / Users
- Simple stick figures with round heads
- No facial features (no eyes, mouth, nose)
- Healthcare workers: add stethoscope or cross
- Patients: plain stick figure
- Family: tall + short figures together

---

## Layout Templates

### 1. Left-to-Right Flow
Best for: claims process, care delivery sequence, data flow
```
[Patient] --> [Provider] --> [Payor]
```

### 2. Hub and Spoke
Best for: HIPAA covered entities, pillar overview, provider types
```
        [Spoke 1]
           |
[Spoke 4]--[HUB]--[Spoke 2]
           |
        [Spoke 3]
```

### 3. Top-to-Bottom Hierarchy
Best for: coverage tiers, coding hierarchy, organizational structure
```
[Level 1 - widest]
    |
[Level 2 - medium]
    |
[Level 3 - narrowest]
```

### 4. Side-by-Side Comparison
Best for: Medicare A vs B, in-network vs out-of-network, subscriber vs dependent
```
[Option A]    |    [Option B]
  ...         |      ...
```

### 5. Numbered Steps List
Best for: enrollment steps, claims filing process, HIPAA compliance checklist
```
1. [Step one]
2. [Step two]
3. [Step three]
```

### 6. Cycle / Loop
Best for: care cycle, billing cycle, eligibility verification loop
```
    [Step 1]
   /         \
[Step 4]   [Step 2]
   \         /
    [Step 3]
```

---

## Text Minimization Rules

### Hard Limits
- **Titles:** Max 5 words. Prefer 3.
- **Box labels:** Max 3 words. Prefer 1-2.
- **Annotations/callouts:** Max 4 words.
- **Total text in entire image:** Aim for under 30 words. Absolute max 50.

### Strategies to Reduce Text
1. Use icons instead of words (shield icon instead of "Insurance")
2. Use abbreviations (DME, EHR, PHI, EOB, ICD, CPT)
3. Remove articles (a, the, an)
4. Remove prepositions when meaning is clear from arrows/layout
5. Use symbols: arrows instead of "leads to", checkmarks instead of "complete"

### Spelling Protection
- Flag any word over 8 characters and shorten
- Common healthcare abbreviations to prefer: DME, EHR, PHI, EOB, ICD, CPT, HCPCS, NPI, CMS, HHS

---

## Element Counting Rules

### Hard Rules
1. **State the exact count**: "EXACTLY 4 boxes in the top row. No more, no fewer."
2. **Name every position**: "Box 1 (far left)... Box 2 (second from left)..."
3. **Spell out the sequence**: "The row reads: Payor, Provider, Patient, Data — exactly these four."
4. **Add a negative constraint**: "Do NOT duplicate or repeat any box."
5. **Reduce detail when count is high**: More boxes = fewer words per box.

---

## Prompt Construction Checklist

Before sending any prompt to the API, verify:

- [ ] Style reference image is included via `--input`
- [ ] Layout template is specified (which of the 6 types?)
- [ ] Every box/element has an assigned color from the healthcare palette
- [ ] Colors match pillar meaning (blue=payor, teal=provider, yellow=patient, purple=data)
- [ ] Every text label is 3 words or fewer
- [ ] Total word count in the image is under 50
- [ ] Long words (8+ characters) are flagged and shortened if possible
- [ ] Spatial positions are explicit
- [ ] Healthcare icon vocabulary is used correctly
- [ ] Element count is stated explicitly with "EXACTLY N" language
- [ ] "Do NOT duplicate" instruction is included when 4+ elements in a row
