import os
import json
import re
import subprocess
import uuid
import pdfplumber

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fpdf import FPDF

# ══════════════════════════════════════════════════════════════════════════════
# AI PROVIDER SETUP
# FREE  → use "groq"      → get key at https://console.groq.com
# PAID  → use "anthropic" → get key at https://console.anthropic.com
#
# After choosing, set the key in your terminal before running:
#   export GROQ_API_KEY="gsk_xxxx"        (if groq)
#   export ANTHROPIC_API_KEY="sk-ant-xx"  (if anthropic)
# ══════════════════════════════════════════════════════════════════════════════

AI_PROVIDER = "groq"   # ← change to "anthropic" if needed

if AI_PROVIDER == "groq":
    from groq import Groq
    ai_client = Groq(api_key=os.environ["GROQ_API_KEY"])
    AI_MODEL  = "llama-3.3-70b-versatile"

elif AI_PROVIDER == "anthropic":
    import anthropic
    ai_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    AI_MODEL  = "claude-opus-4-5"

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CPP_BINARY = os.path.join(BASE_DIR, "..", "cpp_engine", "analyzer")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Resume Optimizer — DAA Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Extract raw text from uploaded PDF
# ══════════════════════════════════════════════════════════════════════════════
def extract_pdf_text(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text.strip()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Pipe text into analyser.cpp (the DAA engine)
#
# Sends:   resume_text + "\n###\n" + job_description  via stdin
# Returns: parsed JSON dict from C++ stdout
#          { final_score, match_quality,
#            missing_keywords, recommended_keywords }
# ══════════════════════════════════════════════════════════════════════════════
def run_cpp_analyser(resume_text: str, job_description: str) -> dict:

    if not os.path.exists(CPP_BINARY):
        raise HTTPException(
            status_code=500,
            detail=(
                "C++ binary not found. Compile it first:\n"
                "  cd cpp_engine\n"
                "  g++ -O2 -o analyzer analyser.cpp"
            )
        )

    stdin_payload = resume_text + "\n###\n" + job_description + "\n"

    try:
        process = subprocess.Popen(
            [CPP_BINARY],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(stdin_payload, timeout=30)

        if process.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"C++ analyser error: {stderr.strip()}"
            )

        result = json.loads(stdout.strip())

        if "error" in result:
            raise HTTPException(
                status_code=500,
                detail=f"C++ returned error: {result['error']}"
            )

        return result

    except subprocess.TimeoutExpired:
        process.kill()
        raise HTTPException(status_code=500, detail="C++ analyser timed out.")
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"C++ output was not valid JSON: {stdout[:300]}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — AI rewrites resume using C++ keyword output
#
# AI does NOT score anything here.
# It only rewrites sentences to naturally include the keywords
# that analyser.cpp identified as missing/recommended via knapsack.
# ══════════════════════════════════════════════════════════════════════════════
def ai_rewrite(
    original_resume: str,
    job_description: str,
    options: dict,
    missing_keywords: list,
    recommended_keywords: list
) -> dict:

    focus_parts = []
    if options.get("ats"):     focus_parts.append("ATS keyword optimization")
    if options.get("impact"):  focus_parts.append("quantified impact metrics")
    if options.get("clarity"): focus_parts.append("clarity and professional tone")
    if options.get("format"):  focus_parts.append("section structure and formatting")
    focus_str = ", ".join(focus_parts) if focus_parts else "general improvement"

    jd_block = (
        f"\n\nJob Description:\n{job_description}"
        if job_description.strip()
        else "\n\n(No job description provided.)"
    )

    missing_block = (
        f"\n\nKeywords MISSING from resume (found by C++ cosine+jaccard analysis):\n"
        + ", ".join(missing_keywords)
    ) if missing_keywords else ""

    recommended_block = (
        f"\n\nTop keywords to ADD (selected by C++ Knapsack algorithm):\n"
        + ", ".join(recommended_keywords)
    ) if recommended_keywords else ""

    prompt = f"""You are a professional resume editor working as part of a DAA-based resume optimizer.

A C++ program has already scored this resume using cosine similarity, jaccard similarity,
and knapsack optimization. Your only job is to REWRITE the resume to naturally include
the keywords the C++ engine identified. Do NOT score the resume yourself.

Original Resume:
{original_resume}
{jd_block}
{missing_block}
{recommended_block}

Rewriting focus: {focus_str}

Instructions:
1. Rewrite the full resume incorporating ALL recommended keywords naturally.
2. Keep the same sections (SUMMARY, EXPERIENCE, SKILLS, EDUCATION, PROJECTS etc).
3. Do not fabricate experience. Only rephrase existing content and add keywords.
4. Show the 3 most impactful changes you made (before vs after).
5. Give 2 tips for the candidate to further improve their resume.

Respond ONLY with valid JSON, no markdown, no backticks:
{{
  "enhanced_text": "Full rewritten resume as plain text",
  "changes": [
    {{"section": "Section name", "old": "original text", "new": "rewritten text"}}
  ],
  "tips": [
    {{"title": "Short tip title", "body": "Explanation"}}
  ]
}}"""

    if AI_PROVIDER == "groq":
        response = ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()

    elif AI_PROVIDER == "anthropic":
        message = ai_client.messages.create(
            model=AI_MODEL,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()

    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$",     "", raw)

    return json.loads(raw)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Generate downloadable PDF from enhanced text
# ══════════════════════════════════════════════════════════════════════════════
def run_semantic_model(resume_text: str, job_description: str) -> float:
    try:
        payload = json.dumps({
            "resume": resume_text,
            "job": job_description
        })

        process = subprocess.Popen(
            ["python3", os.path.join(BASE_DIR, "semantic.py")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(payload, timeout=30)

        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Semantic model error: {stderr}")

        result = json.loads(stdout)
        return result.get("semantic_score", 0)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic error: {e}")
def clean_text(text: str) -> str:
    replacements = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "•": "-",
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text.encode("latin-1", "ignore").decode("latin-1")
def generate_pdf(enhanced_text: str, output_path: str):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    # ✅ FIX: clean text before processing
    enhanced_text = clean_text(enhanced_text)

    lines = enhanced_text.split("\n")

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            pdf.ln(3)
            continue

        is_header = (
            line.isupper()
            or (len(line) < 50 and line.endswith(":"))
            or line in [
                "SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS",
                "PROJECTS", "CERTIFICATIONS", "AWARDS", "CONTACT"
            ]
        )

        if is_header:
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 30, 30)
            pdf.ln(4)
            pdf.cell(0, 8, line, ln=True)
            pdf.set_draw_color(180, 180, 180)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 170, pdf.get_y())
            pdf.ln(2)

        elif i < 3 and len(line) < 60:
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(20, 20, 20)
            pdf.cell(0, 8, line, ln=True, align="C")

        elif line.startswith("-"):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.set_x(25)
            pdf.multi_cell(165, 6, line)

        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(0, 6, line)

    pdf.output(output_path)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def home():
    return {
        "status":      "Resume Optimizer API running",
        "core_engine": "C++ DAA — cosine similarity + jaccard + knapsack",
        "ai_role":     "rewriting only, using C++ keyword output",
        "ai_provider": AI_PROVIDER,
    }


@app.post("/api/optimize")
async def optimize_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(default=""),
    options: str = Form(
        default='{"ats":true,"impact":true,"clarity":false,"format":false}'
    ),
):
    # Validate file type
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted.")

    # Save uploaded PDF to disk
    file_id  = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(await resume.read())

    # STEP 1 — Extract text from PDF
    resume_text = extract_pdf_text(pdf_path)
    if not resume_text or len(resume_text) < 50:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text. Make sure PDF is not a scanned image."
        )
    semantic_score_old = run_semantic_model(resume_text, job_description)
    # Parse options from frontend
    try:
        opts = json.loads(options)
    except Exception:
        opts = {"ats": True, "impact": True, "clarity": False, "format": False}

    # STEP 2 — Run C++ DAA engine on original resume → get score + keywords
    cpp_original       = run_cpp_analyser(resume_text, job_description)
    cpp_old_score = cpp_original.get("final_score", 0)
    old_score = round(0.6 * cpp_old_score + 0.4 * (semantic_score_old * 100), 1)
    match_quality      = cpp_original.get("match_quality", "")
    missing_kw         = cpp_original.get("missing_keywords", [])
    recommended_kw     = cpp_original.get("recommended_keywords", [])

    # STEP 3 — AI rewrites resume using C++ keyword output
    try:
        ai_result = ai_rewrite(
            original_resume      = resume_text,
            job_description      = job_description,
            options              = opts,
            missing_keywords     = missing_kw,
            recommended_keywords = recommended_kw,
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI returned invalid JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI rewrite error: {e}")

    enhanced_text = ai_result.get("enhanced_text", "")
    semantic_score_new = run_semantic_model(enhanced_text, job_description)
    # STEP 2 again — Re-run C++ DAA engine on enhanced resume → new score
    cpp_enhanced = run_cpp_analyser(enhanced_text, job_description)
    cpp_new_score = cpp_enhanced.get("final_score", 0)
    new_score = round(0.6 * cpp_new_score + 0.4 * (semantic_score_new * 100), 1)
    new_quality  = cpp_enhanced.get("match_quality", "")

    # STEP 4 — Generate PDF
    output_pdf = os.path.join(OUTPUT_DIR, f"{file_id}_optimized.pdf")
    generate_pdf(enhanced_text, output_pdf)

    # Return full result to frontend
    return {
        "file_id":             file_id,
        "old_score":           old_score,
        "score":               new_score,
        "semantic_old": round(semantic_score_old * 100, 1),
        "semantic_new": round(semantic_score_new * 100, 1),
        "match_quality":       match_quality,
        "new_match_quality":   new_quality,
        "missing_keywords":    missing_kw,
        "recommended_keywords":recommended_kw,
        "changes":             ai_result.get("changes", []),
        "tips":                ai_result.get("tips", []),
        "full_text":           enhanced_text,
    }


@app.get("/api/download/{file_id}")
def download_resume(file_id: str):
    if not re.match(r"^[a-f0-9\-]{36}$", file_id):
        raise HTTPException(status_code=400, detail="Invalid file ID.")

    pdf_path = os.path.join(OUTPUT_DIR, f"{file_id}_optimized.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="File not found or expired.")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="optimized_resume.pdf",
    )