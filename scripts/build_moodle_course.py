#!/usr/bin/env python3
"""
build_moodle_course.py — Build Moodle course packages from hlthcr content.

A course is a list of modules (each module = one tutorial + its pillar's questions).
Two courses are defined:
  hlthcr-foundations   — the full course, 6 modules (payor, provider, patient, data,
                         cross_domain, contrast).
  medicare-vs-medicaid — the standalone contrast course, 1 module.

Per course it emits, scoped to that course's pillars:
  questions -> exports/lms/{gift,csv,json}/<id>.*            (reuses aig-crs converter)
  scorm     -> exports/lms/scorm/<id>[-MNN-<slug>].zip       (SCORM 1.2: lesson + quiz, per module)
  manifest  -> exports/lms/<id>.manifest.json                (schema: course-manifest 1.0)

Audio WAVs are transcoded to MP3 (ffmpeg) to keep SCORM packages small.

Usage:
  python3 scripts/build_moodle_course.py                          # both courses, all steps
  python3 scripts/build_moodle_course.py --course hlthcr-foundations
  python3 scripts/build_moodle_course.py --course medicare-vs-medicaid --step questions

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

# Moodle question-bank category each pillar lands in (matches quiz_to_lms.py _PILLARS).
PILLAR_CAT = {
    "payor": "HLTHCR: Payor", "provider": "HLTHCR: Provider", "patient": "HLTHCR: Patient",
    "data": "HLTHCR: Healthcare Data", "cross_domain": "HLTHCR: Cross-Domain",
    "contrast": "HLTHCR: Contrast",
}

COURSES = {
    "hlthcr-foundations": {
        "title": "Healthcare Foundations",
        "description": ("A foundational tour of how the U.S. healthcare system works — who pays, "
                        "who provides, who receives, what data is exchanged, how it all connects, "
                        "and how Medicare and Medicaid differ."),
        "level": "foundational",
        "relabel": None,  # keep per-pillar HLTHCR categories
        "modules": [
            ("T-PAYOR-01", "payor"), ("T-PROVIDER-01", "provider"), ("T-PATIENT-01", "patient"),
            ("T-DATA-01", "data"), ("T-CROSS-01", "cross_domain"), ("T-CONTRAST-01", "contrast"),
        ],
    },
    "medicare-vs-medicaid": {
        "title": "Medicare vs. Medicaid: Telling Them Apart",
        "description": ("A focused contrast module that teaches the difference between Medicare and "
                        "Medicaid and their sub-parts (Parts A/B/C/D, CHIP, dual eligibility) by direct, "
                        "side-by-side comparison."),
        "level": "foundational",
        "relabel": "Medicare vs. Medicaid",
        "modules": [("T-CONTRAST-01", "contrast")],
    },
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


def _git_sha():
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True).stdout.strip() or "uncommitted"
    except Exception:
        return "uncommitted"


def category_map(course):
    """pillar -> Moodle question-bank category name.

    Full course: "<n>. <tutorial title>" so moodle-infra/import-course.php maps each
    module's quiz to the right category (its heuristic scores number-in-name + title
    similarity; this makes the correct category the unique strict winner).
    Single-pillar course: the uniform relabel (its quiz uses all questions anyway).
    """
    tuts = {t["tutorial_id"]: t for t in yaml.safe_load(open(ROOT / "content" / "tutorials.yaml"))["tutorials"]}
    if course["relabel"]:
        return {pillar: course["relabel"] for _, pillar in course["modules"]}
    return {pillar: f"{i}. {tuts[tid]['title']}" for i, (tid, pillar) in enumerate(course["modules"], 1)}


def build_questions(conv, course, out_dir):
    """Emit GIFT/CSV/JSON for all pillars in this course (reuses the converter verbatim)."""
    pillars = {p for _, p in course["modules"]}
    data = yaml.safe_load(open(ROOT / "content" / "questions.yaml", encoding="utf-8"))
    qs = [q for q in data["questions"] if str(q.get("pillar", "")).lower() in pillars]
    with tempfile.TemporaryDirectory() as td:
        cdir = Path(td) / "content"; cdir.mkdir(parents=True)
        yaml.safe_dump({"questions": qs}, open(cdir / "questions.yaml", "w", encoding="utf-8"),
                       sort_keys=False, allow_unicode=True)
        questions = conv.parse_hlthcr(str(cdir / "questions.yaml"))
    catmap = category_map(course)
    for q_obj, q_src in zip(questions, qs):
        q_obj.category = catmap[str(q_src["pillar"]).lower()]
    # Stable-sort by category so each Moodle category is declared once in the GIFT
    # (source questions are batched, not contiguous by pillar). Order within a category
    # is preserved, so per-module quiz order is unaffected.
    questions.sort(key=lambda q: q.category)
    for sub in ("gift", "csv", "json"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)
    cid = course["id"]
    with open(out_dir / "gift" / f"{cid}.gift", "w", encoding="utf-8") as fh:
        conv.emit_gift(questions, fh)
    with open(out_dir / "csv" / f"{cid}-questions.csv", "w", encoding="utf-8", newline="") as fh:
        conv.emit_csv(questions, fh)
    with open(out_dir / "json" / f"{cid}-questions.json", "w", encoding="utf-8") as fh:
        conv.emit_json(questions, fh)
    counts = {"mc": 0, "tf": 0, "essay": 0}
    for q in questions:
        counts[q.qtype] += 1
    return len(questions), counts


def _module_questions(catmap, all_json, pillar):
    """Rich-JSON questions for one module's quiz (filter the course JSON by category)."""
    cat = catmap[pillar]
    return [q for q in all_json if q.get("category") == cat]


def _build_scorm_zip(out_dir, slug, title, tut, lesson_scenes, questions_subset):
    """Write one self-contained SCORM 1.2 zip (lesson + quiz) and return (path, n_img, n_aud, size)."""
    player_scenes, images, audios = [], set(), {}
    for s in lesson_scenes:
        if s["scene_type"] == "intro":
            heading, text = tut["title"], f"Welcome to {tut['title']}."
        else:
            sec = tut["sections"][s["order"] - 2]
            heading, text = sec["heading"], sec["text"].strip()
        img = os.path.basename(s.get("visual_asset", "")) or None
        aud = os.path.basename(s.get("audio_asset", "")) or None
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

    course_json = json.dumps({"title": title, "scenes": player_scenes, "questions": questions_subset},
                             ensure_ascii=False)
    index_html = (PLAYER_HTML.replace("__TITLE__", html.escape(title))
                  .replace("__COURSE_JSON__", course_json))
    manifest = SCORM_MANIFEST.format(ident=slug.replace("-", "_"), title=html.escape(title))

    (out_dir / "scorm").mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / "scorm" / f"{slug}.zip"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "audio").mkdir(); (td / "images").mkdir()
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
    return zip_path, len(images), len(audios), zip_path.stat().st_size


def build_scorm(course, out_dir):
    """One SCORM zip per module. Single-module courses keep the bare <id>.zip name."""
    tuts = {t["tutorial_id"]: t for t in yaml.safe_load(open(ROOT / "content" / "tutorials.yaml"))["tutorials"]}
    scenes = yaml.safe_load(open(ROOT / "scenes" / "scenes.yaml"))["scenes"]
    all_json = json.load(open(out_dir / "json" / f"{course['id']}-questions.json", encoding="utf-8"))["questions"]
    catmap = category_map(course)
    multi = len(course["modules"]) > 1
    results = []
    for i, (tid, pillar) in enumerate(course["modules"], 1):
        tut = tuts[tid]
        lesson_scenes = sorted([s for s in scenes if s["tutorial_id"] == tid
                                and s["scene_type"] != "assessment"], key=lambda s: s["order"])
        qsub = _module_questions(catmap, all_json, pillar)
        slug = f"{course['id']}-M{i:02d}-{pillar.replace('_','-')}" if multi else course["id"]
        zp, nimg, naud, size = _build_scorm_zip(out_dir, slug, tut["title"], tut, lesson_scenes, qsub)
        results.append((tid, slug, len(lesson_scenes), len(qsub), size))
    return results


def build_manifest(course, out_dir):
    tuts = {t["tutorial_id"]: t for t in yaml.safe_load(open(ROOT / "content" / "tutorials.yaml"))["tutorials"]}
    scenes = yaml.safe_load(open(ROOT / "scenes" / "scenes.yaml"))["scenes"]
    all_json = json.load(open(out_dir / "json" / f"{course['id']}-questions.json", encoding="utf-8"))["questions"]
    cid = course["id"]
    catmap = category_map(course)
    multi = len(course["modules"]) > 1

    modules = []
    total_q = 0
    for i, (tid, pillar) in enumerate(course["modules"], 1):
        tut = tuts[tid]
        lesson_scenes = [s for s in scenes if s["tutorial_id"] == tid and s["scene_type"] != "assessment"]
        qsub = _module_questions(catmap, all_json, pillar)
        total_q += len(qsub)
        slug = f"{cid}-M{i:02d}-{pillar.replace('_','-')}" if multi else cid
        modules.append({
            "id": f"M{i}", "number": i, "slug": pillar.replace("_", "-"), "title": tut["title"],
            "summary": (tut.get("learning_objectives") or [""])[0],
            "items": [
                {"id": f"M{i}.lesson", "type": "lesson", "title": f"{tut['title']} — Lesson",
                 "sceneCount": len(lesson_scenes), "scormPackage": f"exports/lms/scorm/{slug}.zip"},
                {"id": f"M{i}.quiz", "type": "quiz", "title": f"{tut['title']} — Quiz",
                 "graded": True, "passMark": 0.8, "questionCount": len(qsub),
                 "autoGraded": len(qsub), "manualGraded": 0,
                 "questionsFile": f"exports/lms/json/{cid}-questions.json",
                 "giftFile": f"exports/lms/gift/{cid}.gift"},
            ],
        })

    manifest = {
        "manifestVersion": "1.0",
        "course": {
            "id": cid, "title": course["title"], "description": course["description"],
            "space": "academy", "sourceRepo": "hlthcr", "contentVersion": _git_sha(),
            "language": "en", "level": course["level"], "moduleCount": len(modules),
        },
        "delivery": {
            "player": {"type": "html" if multi else "scorm",
                       "url": "index.html" if multi else f"exports/lms/scorm/{cid}.zip",
                       "progressHook": "window.SCORM_report(raw,max)"},
            "scorm": {"version": "1.2"},
            "moodle": {"gift": f"exports/lms/gift/{cid}.gift"},
        },
        "modules": modules,
    }
    path = out_dir / f"{cid}.manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path, len(modules), total_q


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--course", choices=list(COURSES) + ["all"], default="all")
    ap.add_argument("--step", choices=["questions", "scorm", "manifest", "all"], default="all")
    ap.add_argument("--out", default=str(ROOT / "exports" / "lms"))
    args = ap.parse_args()
    out_dir = Path(args.out)
    keys = list(COURSES) if args.course == "all" else [args.course]
    conv = load_converter()

    for key in keys:
        course = dict(COURSES[key]); course["id"] = key
        print(f"\nCourse: {course['title']}  ({key})")
        if args.step in ("questions", "all"):
            total, c = build_questions(conv, course, out_dir)
            print(f"  questions: {total} (MC={c['mc']}, TF={c['tf']}) -> exports/lms/{{gift,csv,json}}/{key}*")
        if args.step in ("scorm", "all"):
            res = build_scorm(course, out_dir)
            tot = sum(r[4] for r in res)
            print(f"  scorm: {len(res)} package(s), {tot//1024} KB total")
            for tid, slug, nsc, nq, size in res:
                print(f"    {slug}.zip — {nsc} scenes, {nq} Q ({size//1024} KB)")
        if args.step in ("manifest", "all"):
            mp, nmod, nq = build_manifest(course, out_dir)
            print(f"  manifest: {nmod} module(s), {nq} questions -> {mp.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
