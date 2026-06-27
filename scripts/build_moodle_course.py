#!/usr/bin/env python3
"""
build_moodle_course.py — Build a standalone Moodle course package from a single
hlthcr pillar. Default: the CONTRAST pillar -> "Medicare vs. Medicaid: Telling
Them Apart" (course shortname medicare-vs-medicaid).

Steps (all scoped to one pillar / its single tutorial):
  questions  -> exports/lms/{gift,csv,json}/<shortname>.*        (reuses aig-crs converter)
  scorm      -> exports/lms/scorm/<shortname>.zip                (SCORM 1.2: lesson + quiz)

Reuses aig-crs/tools/quiz_to_lms.py for question conversion (no logic duplicated).
Audio WAVs are transcoded to MP3 (ffmpeg) to keep the SCORM package small.

Usage:
  python3 scripts/build_moodle_course.py                  # questions + scorm (default)
  python3 scripts/build_moodle_course.py --step questions
  python3 scripts/build_moodle_course.py --step scorm

generated_by: cc
"""
import argparse
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
AIGCRS_TOOLS = ROOT.parent / "aig-crs" / "tools"

COURSE = {
    "pillar": "contrast",
    "shortname": "medicare-vs-medicaid",
    "fullname": "Medicare vs. Medicaid: Telling Them Apart",
    "category_label": "Medicare vs. Medicaid",
    "tutorial_id": "T-CONTRAST-01",
}

# --------------------------------------------------------------------------- #
# SCORM 1.2 scaffolding
# --------------------------------------------------------------------------- #
SCORM_API_JS = r"""// Minimal SCORM 1.2 adapter — finds the LMS API, reports score + completion.
(function(){
  function findAPI(w){var n=0;while(w&&w.API==null&&w.parent!=null&&w.parent!=w&&n<12){n++;w=w.parent;}return w?w.API:null;}
  var API=null; try{API=findAPI(window); if(!API&&window.opener)API=findAPI(window.opener);}catch(e){}
  var inited=false;
  function init(){ if(!API||inited)return; try{ API.LMSInitialize("");
    inited=true; var s=API.LMSGetValue("cmi.core.lesson_status");
    if(!s||s==="not attempted"||s==="") API.LMSSetValue("cmi.core.lesson_status","incomplete");
    API.LMSCommit(""); }catch(e){} }
  function finish(){ if(!API||!inited)return; try{API.LMSCommit("");API.LMSFinish("");inited=false;}catch(e){} }
  window.SCORM_report=function(raw,max){ if(!API)return; if(!inited)init(); try{
    if(max>0){ API.LMSSetValue("cmi.core.score.raw",String(raw));
      API.LMSSetValue("cmi.core.score.min","0"); API.LMSSetValue("cmi.core.score.max",String(max));
      API.LMSSetValue("cmi.core.lesson_status",(raw/max)>=0.8?"passed":"failed");
    } else { API.LMSSetValue("cmi.core.lesson_status","completed"); }
    API.LMSCommit(""); }catch(e){} };
  window.addEventListener("load",init);
  window.addEventListener("unload",finish);
  window.addEventListener("pagehide",finish);
})();"""

SCORM_MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="HLTHCR_{ident}" version="1.0"
  xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
  xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd
  http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd">
  <metadata><schema>ADL SCORM</schema><schemaversion>1.2</schemaversion></metadata>
  <organizations default="ORG">
    <organization identifier="ORG"><title>{title}</title>
      <item identifier="ITEM1" identifierref="RES1"><title>{title}</title>
        <adlcp:masteryscore>80</adlcp:masteryscore></item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="RES1" type="webcontent" adlcp:scormtype="sco" href="index.html">
      <file href="index.html"/><file href="scorm_api.js"/>
    </resource>
  </resources>
</manifest>
"""

PLAYER_HTML = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>__TITLE__</title>
<style>
*{box-sizing:border-box}body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a2e;background:#f4f6fb}
.wrap{max-width:880px;margin:0 auto;padding:24px}
h1{font-size:1.5rem}h2{font-size:1.25rem;color:#7B2D8E}
.card{background:#fff;border-radius:14px;box-shadow:0 2px 10px rgba(0,0,0,.06);padding:24px;margin:16px 0}
img.scene{width:100%;border-radius:10px;border:1px solid #e6e8f0}
audio{width:100%;margin:14px 0}
.text{line-height:1.6;white-space:pre-wrap;margin-top:12px}
.nav{display:flex;justify-content:space-between;margin-top:18px}
button{font:inherit;padding:10px 18px;border-radius:9px;border:0;background:#7B2D8E;color:#fff;cursor:pointer}
button.sec{background:#e6e8f0;color:#1a1a2e}button:disabled{opacity:.4;cursor:not-allowed}
.prog{height:6px;background:#e6e8f0;border-radius:4px;overflow:hidden;margin:10px 0}
.prog>i{display:block;height:100%;background:#7B2D8E}
.opt{display:block;width:100%;text-align:left;background:#f4f6fb;color:#1a1a2e;border:1px solid #e6e8f0;margin:8px 0;padding:12px}
.opt.correct{background:#e7f6ec;border-color:#36b37e}.opt.wrong{background:#fceeee;border-color:#d64545}
.fb{font-size:.92rem;color:#444;margin:6px 0 0;padding-left:6px}
.q{border-bottom:1px solid #eef0f6;padding:16px 0}.q:last-child{border:0}
.score{font-size:1.3rem;font-weight:700;text-align:center;margin:10px 0}
</style><script src="scorm_api.js"></script></head>
<body><div class="wrap" id="app"></div>
<script>
const COURSE=__COURSE_JSON__;
let view={mode:"lesson",i:0};
const app=document.getElementById("app");
function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;")}
function render(){ view.mode==="lesson"?lesson():quiz(); window.scrollTo(0,0); }
function lesson(){
  const sc=COURSE.scenes[view.i], n=COURSE.scenes.length;
  const last=view.i===n-1;
  app.innerHTML=`<h1>${esc(COURSE.title)}</h1>
  <div class="prog"><i style="width:${Math.round((view.i+1)/n*100)}%"></i></div>
  <div class="card"><h2>${esc(sc.heading)}</h2>
    ${sc.image?`<img class="scene" src="images/${sc.image}" alt="">`:""}
    ${sc.audio?`<audio controls src="audio/${sc.audio}"></audio>`:""}
    <div class="text">${esc(sc.text)}</div>
    <div class="nav">
      <button class="sec" ${view.i===0?"disabled":""} onclick="view.i--;render()">&larr; Back</button>
      <button onclick="${last?'view.mode=\\'quiz\\';render()':'view.i++;render()'}">${last?"Start the quiz &rarr;":"Next &rarr;"}</button>
    </div></div>`;
}
function quiz(){
  let h=`<h1>Quiz — ${esc(COURSE.title)}</h1><div class="card"><p>${COURSE.questions.length} questions. Pick an answer to check it; your score reports to the gradebook.</p></div><div class="card">`;
  COURSE.questions.forEach((q,qi)=>{
    h+=`<div class="q" id="q${qi}"><p><b>Q${qi+1}.</b> ${esc(q.stem)}</p>`;
    if(q.type==="tf"){
      h+=`<button class="opt" onclick="ans(${qi},'True')">True</button>
          <button class="opt" onclick="ans(${qi},'False')">False</button>`;
    } else {
      q.options.forEach(o=>{ h+=`<button class="opt" onclick="ans(${qi},'${o.label}')">${o.label}. ${esc(o.text)}</button>`; });
    }
    h+=`<div class="fb" id="fb${qi}"></div></div>`;
  });
  h+=`</div><div class="card"><div class="score" id="score"></div>
      <div class="nav"><button class="sec" onclick="view.mode='lesson';render()">&larr; Lesson</button>
      <button onclick="submit()">Submit &amp; report score</button></div></div>`;
  app.innerHTML=h; window.answered={};
}
function ans(qi,choice){
  const q=COURSE.questions[qi]; if(window.answered[qi])return;
  let correct,fb="";
  if(q.type==="tf"){ correct=(String(q.correct)==="true")===(choice==="True"); fb=q.feedback; }
  else { const o=q.options.find(x=>x.label===choice); const c=q.options.find(x=>x.correct);
         correct=o&&o.correct; fb=correct?q.feedback:(o?o.feedback:"")+(c?` (Correct: ${c.label})`:""); }
  window.answered[qi]={correct};
  const box=document.getElementById("q"+qi);
  box.querySelectorAll(".opt").forEach(b=>{b.disabled=true;
    if(b.textContent.trim().startsWith(choice)||b.textContent.trim()===choice) b.classList.add(correct?"correct":"wrong");});
  document.getElementById("fb"+qi).textContent=(correct?"✓ Correct. ":"✗ ")+fb;
}
function submit(){
  let right=0; const tot=COURSE.questions.length;
  COURSE.questions.forEach((q,qi)=>{ if(window.answered[qi]&&window.answered[qi].correct)right++; });
  document.getElementById("score").textContent=`You scored ${right} / ${tot}`;
  if(window.SCORM_report){try{window.SCORM_report(right,tot);}catch(e){}}
}
render();
</script></body></html>"""


def load_converter():
    if not (AIGCRS_TOOLS / "quiz_to_lms.py").exists():
        sys.exit(f"converter not found at {AIGCRS_TOOLS/'quiz_to_lms.py'}")
    sys.path.insert(0, str(AIGCRS_TOOLS))
    import quiz_to_lms as conv
    return conv


def filtered_questions(pillar):
    data = yaml.safe_load(open(ROOT / "content" / "questions.yaml", encoding="utf-8"))
    qs = [q for q in data.get("questions", []) if str(q.get("pillar", "")).lower() == pillar]
    if not qs:
        sys.exit(f"no questions for pillar '{pillar}'")
    return qs


def build_questions(conv, pillar, out_dir):
    qs = filtered_questions(pillar)
    with tempfile.TemporaryDirectory() as td:
        cdir = Path(td) / "content"; cdir.mkdir(parents=True)
        yaml.safe_dump({"questions": qs}, open(cdir / "questions.yaml", "w", encoding="utf-8"),
                       sort_keys=False, allow_unicode=True)
        questions = conv.parse_hlthcr(str(cdir / "questions.yaml"))
    for q in questions:
        q.category = COURSE["category_label"]
    for sub in ("gift", "csv", "json"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)
    short = COURSE["shortname"]
    with open(out_dir / "gift" / f"{short}.gift", "w", encoding="utf-8") as fh:
        conv.emit_gift(questions, fh)
    with open(out_dir / "csv" / f"{short}-questions.csv", "w", encoding="utf-8", newline="") as fh:
        conv.emit_csv(questions, fh)
    with open(out_dir / "json" / f"{short}-questions.json", "w", encoding="utf-8") as fh:
        conv.emit_json(questions, fh)
    counts = {"mc": 0, "tf": 0, "essay": 0}
    for q in questions:
        counts[q.qtype] += 1
    return len(questions), counts


def build_scorm(out_dir):
    """Self-contained SCORM 1.2 package: single-tutorial lesson + 40-question quiz."""
    tuts = {t["tutorial_id"]: t for t in yaml.safe_load(open(ROOT / "content" / "tutorials.yaml"))["tutorials"]}
    scenes = yaml.safe_load(open(ROOT / "scenes" / "scenes.yaml"))["scenes"]
    tut = tuts[COURSE["tutorial_id"]]
    con_scenes = sorted([s for s in scenes if s["tutorial_id"] == COURSE["tutorial_id"]
                         and s["scene_type"] != "assessment"], key=lambda s: s["order"])

    player_scenes, images, audios = [], set(), {}
    for s in con_scenes:
        if s["scene_type"] == "intro":
            heading, text = tut["title"], f"Welcome to {tut['title']}."
        else:
            sec = tut["sections"][s["order"] - 2]
            heading, text = sec["heading"], sec["text"].strip()
        img = os.path.basename(s.get("visual_asset", "")) or None
        aud = os.path.basename(s.get("audio_asset", "")) or None   # .mp3 name
        if img and (ROOT / "media" / "images" / img).exists():
            images.add(img)
        else:
            img = None
        if aud:
            wav = ROOT / "media" / "audio" / (Path(aud).stem + ".wav")
            if wav.exists():
                audios[aud] = wav
            else:
                aud = None
        player_scenes.append({"heading": heading, "text": text, "image": img, "audio": aud})

    questions = json.load(open(out_dir / "json" / f"{COURSE['shortname']}-questions.json", encoding="utf-8"))["questions"]
    course_json = json.dumps({"title": COURSE["fullname"], "scenes": player_scenes, "questions": questions},
                             ensure_ascii=False)
    index_html = (PLAYER_HTML
                  .replace("__TITLE__", html.escape(COURSE["fullname"]))
                  .replace("__COURSE_JSON__", course_json))
    manifest = SCORM_MANIFEST.format(ident=COURSE["shortname"].replace("-", "_"),
                                     title=html.escape(COURSE["fullname"]))

    (out_dir / "scorm").mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / "scorm" / f"{COURSE['shortname']}.zip"

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "audio").mkdir(); (td / "images").mkdir()
        # transcode wav -> mp3 to keep the package small
        for mp3_name, wav in audios.items():
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                            "-codec:a", "libmp3lame", "-q:a", "5", str(td / "audio" / mp3_name)], check=True)
        for img in images:
            shutil.copy(ROOT / "media" / "images" / img, td / "images" / img)
        (td / "index.html").write_text(index_html, encoding="utf-8")
        (td / "scorm_api.js").write_text(SCORM_API_JS, encoding="utf-8")
        (td / "imsmanifest.xml").write_text(manifest, encoding="utf-8")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(td.rglob("*")):
                if p.is_file():
                    z.write(p, p.relative_to(td))
    return zip_path, len(player_scenes), len(images), len(audios), zip_path.stat().st_size


def build_manifest(out_dir):
    """Emit a schema-valid course-manifest.json (the platform contract) for this course."""
    tuts = {t["tutorial_id"]: t for t in yaml.safe_load(open(ROOT / "content" / "tutorials.yaml"))["tutorials"]}
    scenes = yaml.safe_load(open(ROOT / "scenes" / "scenes.yaml"))["scenes"]
    con = [s for s in scenes if s["tutorial_id"] == COURSE["tutorial_id"]]
    lesson_scenes = [s for s in con if s["scene_type"] != "assessment"]
    qs = filtered_questions(COURSE["pillar"])
    tf = sum(1 for q in qs if str(q.get("type")).upper() == "TF")
    mc = sum(1 for q in qs if str(q.get("type")).upper() == "MCQ")
    short = COURSE["shortname"]
    try:
        sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip() or "uncommitted"
    except Exception:
        sha = "uncommitted"

    manifest = {
        "manifestVersion": "1.0",
        "course": {
            "id": short,
            "title": COURSE["fullname"],
            "description": ("A focused contrast module that teaches the difference between Medicare and "
                            "Medicaid and their sub-parts (Parts A/B/C/D, CHIP, dual eligibility) by direct, "
                            "side-by-side comparison."),
            "space": "academy",
            "sourceRepo": "hlthcr",
            "contentVersion": sha,
            "language": "en",
            "level": "foundational",
            "estimatedHours": 0.5,
            "moduleCount": 1,
        },
        "delivery": {
            "player": {
                "type": "scorm",
                "url": f"exports/lms/scorm/{short}.zip",
                "progressHook": "window.SCORM_report(raw,max)",
            },
            "scorm": {"version": "1.2"},
            "moodle": {"gift": f"exports/lms/gift/{short}.gift"},
        },
        "modules": [{
            "id": "M1",
            "number": 1,
            "slug": short,
            "title": COURSE["fullname"],
            "summary": "Medicare vs. Medicaid told apart across six axes: who qualifies, who funds it, "
                       "what's covered, the sub-parts, cost, and dual eligibility.",
            "items": [
                {
                    "id": "M1.lesson",
                    "type": "lesson",
                    "title": f"{COURSE['fullname']} — Lesson",
                    "sceneCount": len(lesson_scenes),
                    "scormPackage": f"exports/lms/scorm/{short}.zip",
                },
                {
                    "id": "M1.quiz",
                    "type": "quiz",
                    "title": f"{COURSE['fullname']} — Quiz",
                    "graded": True,
                    "passMark": 0.8,
                    "questionCount": len(qs),
                    "autoGraded": tf + mc,
                    "manualGraded": 0,
                    "questionsFile": f"exports/lms/json/{short}-questions.json",
                    "giftFile": f"exports/lms/gift/{short}.gift",
                },
            ],
        }],
    }
    path = out_dir / f"{short}.manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path, len(lesson_scenes), len(qs)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pillar", default=COURSE["pillar"])
    ap.add_argument("--step", choices=["questions", "scorm", "manifest", "all"], default="all")
    ap.add_argument("--out", default=str(ROOT / "exports" / "lms"))
    args = ap.parse_args()
    out_dir = Path(args.out)

    print(f"Course: {COURSE['fullname']}  (shortname: {COURSE['shortname']})")
    if args.step in ("questions", "all"):
        conv = load_converter()
        total, counts = build_questions(conv, args.pillar, out_dir)
        print(f"  questions: {total} (MC={counts['mc']}, TF={counts['tf']}) -> exports/lms/{{gift,csv,json}}/")
    if args.step in ("scorm", "all"):
        zp, nsc, nimg, naud, size = build_scorm(out_dir)
        print(f"  scorm: {nsc} lesson scenes, {nimg} images, {naud} audio -> {zp.relative_to(ROOT)} ({size//1024} KB)")
    if args.step in ("manifest", "all"):
        mp, nsc, nq = build_manifest(out_dir)
        print(f"  manifest: 1 module, lesson({nsc} scenes) + quiz({nq} Q) -> {mp.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
