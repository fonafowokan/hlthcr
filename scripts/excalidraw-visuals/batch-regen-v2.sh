#!/usr/bin/env bash
# Batch regeneration of 18 spelling-failed images with _v2 suffix
# Runs one at a time to avoid API rate limits

set -euo pipefail

PROJECT_ROOT="/home/femi/projects/hlthcr"
SCRIPT="$PROJECT_ROOT/scripts/excalidraw-visuals/generate-visual.js"
IMG_DIR="$PROJECT_ROOT/media/images"
PROMPT_DIR="$IMG_DIR/prompts"
SHARED_DIR="/home/femi/projects/shared/HLTHCR/images"
STYLE_REF="$PROJECT_ROOT/brand-assets/excalidraw-style-reference.png"

mkdir -p "$PROMPT_DIR" "$SHARED_DIR"

STYLE_PREFIX='Excalidraw-style hand-drawn diagram on a clean white background. All text uses neat, consistent architect-style handwriting -- legible, slightly rounded letters with medium stroke weight. Letter sizes are uniform within each label. Titles are bold and larger. Body labels are smaller but equally neat. This is NOT sloppy handwriting -- it looks like a designer wrote it carefully with a thick marker.

Shapes are rounded rectangles with a 2-3px dark gray (#495057) hand-drawn outline and soft pastel fills. Lines and arrows are slightly wobbly and hand-drawn, not ruler-straight. Arrowheads are simple triangles. Nothing is pixel-perfect -- everything has a natural, sketched feel with visible stroke texture.

Color palette: teal (#81D4C2), soft blue (#a5d8ff), warm yellow (#ffec99), coral (#ffa8a8), light purple (#d0bfff). All text is dark charcoal (#343a40). All lines and arrows are dark gray (#495057). Background is always clean white.

Do NOT include: realistic photos, gradients, drop shadows, 3D effects, corporate clip art, stock imagery, dark backgrounds, heavy borders.'

SUCCESS=0
FAIL=0

generate_one() {
  local NAME="$1"
  local PROMPT_BODY="$2"
  local OUTPUT="$IMG_DIR/${NAME}_v2.png"
  local FULL_PROMPT="${STYLE_PREFIX}

${PROMPT_BODY}"

  echo ""
  echo "============================================"
  echo "Generating: ${NAME}_v2.png"
  echo "============================================"

  # Save prompt JSON
  local PROMPT_JSON="$PROMPT_DIR/${NAME}_v2.json"
  local TIMESTAMP
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.%6NZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")

  # Use python to create JSON safely
  python3 -c "
import json, sys
data = {
    'image_file': '${NAME}_v2.png',
    'visual_type': 'excalidraw',
    'prompt': sys.stdin.read(),
    'generated_at': '${TIMESTAMP}',
    'aspect_ratio': '16:9',
    'version': 'v2',
    'reason': 'spelling review regen - shorter labels'
}
with open('${PROMPT_JSON}', 'w') as f:
    json.dump(data, f, indent=2)
" <<< "$FULL_PROMPT"

  echo "  Prompt JSON saved: $PROMPT_JSON"

  # Generate image
  if node "$SCRIPT" "$FULL_PROMPT" "$OUTPUT" "16:9" --input "$STYLE_REF"; then
    if [ -f "$OUTPUT" ]; then
      local SIZE
      SIZE=$(stat -c%s "$OUTPUT" 2>/dev/null || stat -f%z "$OUTPUT")
      echo "  SUCCESS: ${NAME}_v2.png (${SIZE} bytes)"

      # Copy to shared
      cp "$OUTPUT" "$SHARED_DIR/${NAME}_v2.png"
      echo "  Copied to shared: $SHARED_DIR/${NAME}_v2.png"
      SUCCESS=$((SUCCESS + 1))
    else
      echo "  FAILED: Output file not created"
      FAIL=$((FAIL + 1))
    fi
  else
    echo "  FAILED: Generation error"
    FAIL=$((FAIL + 1))
  fi
}

# 1. payor-medicaid
generate_one "payor-medicaid" 'Title: "Medicare vs Medicaid" in bold at top.

Two side-by-side rounded boxes. Left box in soft blue fill labeled "MEDICARE" with three bullet items: "Federal", "Age 65+", "Parts A & B". Right box in teal fill labeled "MEDICAID" with three bullet items: "Fed + State", "Low income", "Varies by state". A vertical dashed line separates the two boxes.'

# 2. payor-commercial
generate_one "payor-commercial" 'Title: "Plan Types" in bold at top.

Two rounded boxes at top row: "Employer Plan" in soft blue, "Marketplace" in teal. Both have arrows pointing down to a label "Plan Types". Below that, four small boxes in a row: "HMO" (coral, "Network only"), "PPO" (soft blue, "Any doctor"), "EPO" (warm yellow, "No referral"), "POS" (light purple, "Hybrid plan"). Each box has the 2-word description below the abbreviation.'

# 3. payor-selfpay
generate_one "payor-selfpay" 'Title: "Self-Pay Process" in bold at top.

Three rounded boxes in a horizontal flow connected by arrows: Box 1 teal fill "Schedule", arrow pointing right, Box 2 soft blue fill "Get Estimate", arrow pointing right, Box 3 warm yellow fill "Know Cost". Arrows are hand-drawn with simple triangle arrowheads.'

# 4. payor-hipaa
generate_one "payor-hipaa" 'Title: "HIPAA Health Plans" in bold at top.

A vertical list of 5 items, each in its own rounded box with pastel fills alternating colors: "Insurers" (teal), "HMOs" (soft blue), "Employer Plans" (warm yellow), "Medicare" (coral), "Medicaid" (light purple). Small callout box to the side with dashed border: "Exempt: <50 people".'

# 5. provider-definition
generate_one "provider-definition" 'Title: "Providers vs Suppliers" in bold at top.

Two rounded boxes side by side. Left box in teal fill labeled "Providers" with three items listed: "Hospitals", "Hospice", "Nursing". Right box in warm yellow fill labeled "Suppliers" with three items: "DME", "Labs", "Diagnostics". A "vs" label between them.'

# 6. provider-types
generate_one "provider-types" 'Title: "Provider Types" in bold at top.

Hub-and-spoke diagram. Center circle or rounded box labeled "Provider Types" in soft blue. Exactly 5 spokes radiating outward to 5 labeled boxes: "Doctors" (teal), "Hospitals" (warm yellow), "DME" (coral), "Ambulance" (light purple), "Labs" (soft blue). No sub-labels on the spokes. Each spoke is a hand-drawn line with no arrowhead. Exactly 5 spokes, no duplicates.'

# 7. provider-billing
generate_one "provider-billing" 'Title: "Claim Forms" in bold at top.

Two parallel horizontal flows. Top flow: "Doctor" (teal box) arrow right to "CMS-1500" (soft blue box) arrow right to "Payor" (warm yellow box). Bottom flow: "Hospital" (coral box) arrow right to "UB-04" (light purple box) arrow right to "Payor" (warm yellow box). Arrows are hand-drawn.'

# 8. provider-medicare-enrollment
generate_one "provider-medicare-enrollment" 'Title: "Medicare Enrollment" in bold at top.

Three-step horizontal flow at top: "1. Get NPI" (teal box) arrow to "2. Apply (PECOS)" (soft blue box) arrow to "3. Work with MAC" (warm yellow box).

Below, three smaller boxes in a row showing form types: "855I Doctors" (coral), "855A Hospitals" (light purple), "855S DME" (teal). A label above them says "Forms".'

# 9. provider-medicaid-enrollment
generate_one "provider-medicaid-enrollment" 'Title: "Medicaid Enrollment" in bold at top.

Layered diagram with two stacked rounded boxes. Bottom/base layer is a wider teal box labeled "Federal Minimum" with sub-label "License check". Top layer is a slightly smaller soft blue box overlapping on top, labeled "State Additions" with sub-label "Extra rules". An upward arrow from base to top layer.'

# 10. provider-hipaa
generate_one "provider-hipaa" 'Title: "HIPAA for Providers" in bold at top.

Four items in a vertical checklist, each with a checkbox icon (hand-drawn square with checkmark): "Privacy Rules" (teal fill box), "Security Rules" (soft blue fill box), "Staff Training" (warm yellow fill box), "BA Contracts" (coral fill box). Each item is a rounded rectangle with the checkbox to its left.'

# 11. patient-costs
generate_one "patient-costs" 'Title: "Your Costs" in bold at top.

Four stacked boxes forming a vertical funnel or stack, from top to bottom: "Premium" with sub-label "Monthly fee" (teal), "Then pay..." with sub-label "Per-year amount" (soft blue), "Per visit..." with sub-label "Fixed fee" (warm yellow), "Cap..." with sub-label "Max per year" (coral). Arrows or flow lines connect each step downward.'

# 12. patient-consent
generate_one "patient-consent" 'Title: "Privacy & Consent" in bold at top.

Two panels side by side. Left panel in teal: "Privacy Notice" with a small document icon and sub-label "How data is used". Right panel in soft blue: "Consent" with three steps listed: "Explain risks", "Patient decides", "Emergency OK". A vertical dashed line separates the panels.'

# 13. data-phi
generate_one "data-phi" 'Title: "What is PHI?" in bold at top.

A shield or lock shape in teal with items listed inside: "Name", "DOB", "SSN", "Records". Below the shield, three small boxes in a row: "Digital" (soft blue), "Paper" (warm yellow), "Spoken" (coral). A label between shield and boxes says "Forms of PHI".'

# 14. cross-eligibility
generate_one "cross-eligibility" 'Title: "Coverage Check" in bold at top.

Request-response flow. Left box "Provider" (teal) sends an arrow labeled "270 Check" to right box "Health Plan" (soft blue). Health Plan sends a return arrow back labeled "Coverage Info" with small note "(copay, limits)". Arrows are hand-drawn and slightly curved.'

# 15. cross-clearinghouse
generate_one "cross-clearinghouse" 'Title: "Claims Routing" in bold at top.

Three-node horizontal flow: "Provider" (teal box) arrow right to "Clearinghouse" (soft blue box with sub-label "Translator") arrow right to "Payor" (warm yellow box). The output arrow is labeled "Standard format". Arrows are hand-drawn.'

# 16. cross-npi
generate_one "cross-npi" 'Title: "National Provider ID" in bold at top.

Central rounded box labeled "NPI" with sub-label "10-digit ID" in teal. Four spokes radiating outward to four boxes: "Claims" (soft blue), "Eligibility" (warm yellow), "Billing" (coral), "Records" (light purple). Spokes are hand-drawn lines.'

# 17. cross-hipaa-unified
generate_one "cross-hipaa-unified" 'Title: "HIPAA System" in bold at top.

Triangle layout. "Payors" box (teal) at top. "Providers" box (soft blue) at bottom-left. "Clearinghouses" box (warm yellow) at bottom-right. "HIPAA" label in the center of the triangle. Three edges connecting the triangle vertices with labels: "Claims" on left edge, "Payment" on right edge, "Eligibility" on bottom edge. Edges are hand-drawn lines.'

# 18. patient-eob
generate_one "patient-eob" 'Title: "Your EOB" in bold at top.

Three boxes in a horizontal flow: "Billed: $1,500" (teal box) arrow to "Plan Paid: $1,000" (soft blue box) arrow to "You Owe: $300" (coral box). A small callout box below with dashed border says "NOT a bill" in bold. Arrows are hand-drawn.'

echo ""
echo "============================================"
echo "BATCH COMPLETE"
echo "  Success: $SUCCESS / 18"
echo "  Failed:  $FAIL / 18"
echo "============================================"
