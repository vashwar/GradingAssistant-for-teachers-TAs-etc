import os
import re
import io

import streamlit as st
from dotenv import load_dotenv
import anthropic
from google import genai
from google.genai import types
from PyPDF2 import PdfReader
from fpdf import FPDF

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

CLAUDE_MODEL = "claude-opus-4-6"
GEMINI_MODEL = "gemini-2.5-pro"

# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------
PHASE1_SYSTEM = (
    "You are an expert academic grader. Analyze the student essay against the "
    "assignment prompt and grading rubric. Provide a thorough, critical Draft 1 "
    "analysis covering: strengths, weaknesses, and how the essay measures against "
    "each rubric item. Be specific with evidence from the essay."
)

PHASE1_USER = (
    "Assignment Prompt:\n{prompt_text}\n\n"
    "Grading Rubric:\n{rubric_text}\n\n"
    "Student Essay:\n{essay_text}\n\n"
    "Provide your Draft 1 analysis."
)

PHASE2_SYSTEM = (
    "You are an expert academic grader performing a cross-review. You previously "
    "wrote your own Draft 1 analysis. Now review a peer grader's Draft 1. Identify "
    "insights they caught that you may have missed, points of agreement, and any "
    "disagreements. Produce a refined Draft 2 that incorporates the best of both "
    "analyses."
)

PHASE2_USER = (
    "Your Draft 1:\n{own_draft}\n\n"
    "Peer Grader's Draft 1:\n{peer_draft}\n\n"
    "Produce your refined Draft 2."
)

PHASE3_SYSTEM = (
    "You are the Chief Grader making the final assessment. Combine both Draft 2 "
    "analyses into one authoritative, coherent final report. Resolve any "
    "discrepancies. Verify every rubric item is addressed.\n\n"
    "Format the report with exactly these sections:\n"
    "1. **Strengths and Weaknesses** — detailed breakdown\n"
    "2. **Rubric Item Breakdown** — address every single rubric item with specific "
    "evidence from the essay\n"
    "3. **Suggested Grading** — final score/grade tied to the rubric's scale\n\n"
    "Use Markdown formatting. Be thorough and fair."
)

PHASE3_USER = (
    "Assignment Prompt:\n{prompt_text}\n\n"
    "Grading Rubric:\n{rubric_text}\n\n"
    "Chief Grader's Draft 2:\n{chief_draft2}\n\n"
    "Assistant's Draft 2:\n{assistant_draft2}\n\n"
    "Produce the final grading report."
)

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def extract_text(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> str:
    """Extract text content from an uploaded .txt or .pdf file."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".txt"):
            return uploaded_file.read().decode("utf-8")
        elif name.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(uploaded_file.read()))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages)
            if not text.strip():
                raise ValueError(f"No extractable text found in PDF: {uploaded_file.name}")
            return text
        else:
            raise ValueError(f"Unsupported file type for '{uploaded_file.name}'. Please upload a .txt or .pdf file.")
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to read '{uploaded_file.name}': {e}") from e


def call_claude(system_prompt: str, user_prompt: str) -> str:
    """Send a request to Claude and return the response text."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text


def call_gemini(system_prompt: str, user_prompt: str) -> str:
    """Send a request to Gemini and return the response text."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return response.text


def call_model(role: str, system_prompt: str, user_prompt: str, role_map: dict) -> str:
    """Dispatch to the correct model based on role assignment."""
    model_name = role_map[role]
    if model_name == "Claude":
        return call_claude(system_prompt, user_prompt)
    else:
        return call_gemini(system_prompt, user_prompt)


def markdown_to_pdf(markdown_text: str) -> bytes:
    """Convert a Markdown string into PDF bytes using fpdf2."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Use built-in fonts only (Helvetica supports bold/italic natively in fpdf2)
    base_font = "Helvetica"

    for line in markdown_text.split("\n"):
        stripped = line.strip()

        # Headers
        if stripped.startswith("### "):
            pdf.set_font(base_font, "B", 13)
            pdf.multi_cell(0, 7, stripped[4:])
            pdf.ln(2)
        elif stripped.startswith("## "):
            pdf.set_font(base_font, "B", 15)
            pdf.multi_cell(0, 8, stripped[3:])
            pdf.ln(3)
        elif stripped.startswith("# "):
            pdf.set_font(base_font, "B", 18)
            pdf.multi_cell(0, 10, stripped[2:])
            pdf.ln(4)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            pdf.set_font(base_font, "", 11)
            # Render bold fragments within bullet points
            _render_rich_line(pdf, base_font, 11, "  - " + stripped[2:])
            pdf.ln(1)
        elif stripped == "":
            pdf.ln(4)
        else:
            pdf.set_font(base_font, "", 11)
            _render_rich_line(pdf, base_font, 11, stripped)
            pdf.ln(1)

    return bytes(pdf.output())


def _render_rich_line(pdf: FPDF, base_font: str, size: int, text: str):
    """Render a single line with **bold** spans into the PDF."""
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            pdf.set_font(base_font, "B", size)
            pdf.write(6, part[2:-2])
        else:
            pdf.set_font(base_font, "", size)
            pdf.write(6, part)
    pdf.ln(5)


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

st.set_page_config(page_title="AI Grading Assistant", page_icon="\U0001f4dd", layout="wide")
st.title("AI Grading Assistant")
st.caption("Multi-agent grading powered by Claude Opus & Gemini Pro")

# --- Validate API keys ---
keys_ok = True
if not ANTHROPIC_API_KEY:
    st.error("Missing `ANTHROPIC_API_KEY`. Add it to your `.env` file.")
    keys_ok = False
if not GEMINI_API_KEY:
    st.error("Missing `GEMINI_API_KEY`. Add it to your `.env` file.")
    keys_ok = False

# --- Sidebar: role selection ---
with st.sidebar:
    st.header("Role Assignment")
    chief_choice = st.radio(
        "Select Chief Grader",
        options=["Claude Opus 4.6", "Gemini 2.5 Pro"],
        index=0,
    )

    if chief_choice == "Claude Opus 4.6":
        role_map = {"chief": "Claude", "assistant": "Gemini"}
        assistant_label = "Gemini 2.5 Pro"
    else:
        role_map = {"chief": "Gemini", "assistant": "Claude"}
        assistant_label = "Claude Opus 4.6"

    st.info(
        f"**Chief Grader:** {chief_choice}\n\n"
        f"**Assistant:** {assistant_label}"
    )

# --- File uploaders ---
st.subheader("Upload Documents")
col1, col2, col3 = st.columns(3)

with col1:
    prompt_file = st.file_uploader("Assignment Prompt", type=["txt", "pdf"], key="prompt")
with col2:
    rubric_file = st.file_uploader("Grading Rubric", type=["txt", "pdf"], key="rubric")
with col3:
    essay_file = st.file_uploader("Student Essay", type=["txt", "pdf"], key="essay")

all_uploaded = prompt_file is not None and rubric_file is not None and essay_file is not None

# --- Process button ---
if st.button("Process Grading", disabled=(not all_uploaded or not keys_ok)):
    # Extract text from uploads
    try:
        prompt_text = extract_text(prompt_file)
        rubric_text = extract_text(rubric_file)
        essay_text = extract_text(essay_file)
    except Exception as e:
        st.error(f"File reading error: {e}")
        st.stop()

    # Validate non-empty
    if not prompt_text.strip():
        st.error("The Assignment Prompt file appears to be empty.")
        st.stop()
    if not rubric_text.strip():
        st.error("The Grading Rubric file appears to be empty.")
        st.stop()
    if not essay_text.strip():
        st.error("The Student Essay file appears to be empty.")
        st.stop()

    phase1_user = PHASE1_USER.format(
        prompt_text=prompt_text, rubric_text=rubric_text, essay_text=essay_text
    )

    chief_label = chief_choice
    asst_label = assistant_label

    with st.status("Grading in progress...", expanded=True) as status:
        # ------ Phase 1 ------
        st.write(f"**Phase 1 — Independent Analysis**")

        st.write(f"  {chief_label} (Chief) analyzing...")
        try:
            chief_draft1 = call_model("chief", PHASE1_SYSTEM, phase1_user, role_map)
        except Exception as e:
            st.error(f"Phase 1 failed — Chief Grader ({chief_label}): {e}")
            st.stop()

        st.write(f"  {asst_label} (Assistant) analyzing...")
        try:
            assistant_draft1 = call_model("assistant", PHASE1_SYSTEM, phase1_user, role_map)
        except Exception as e:
            st.error(f"Phase 1 failed — Assistant ({asst_label}): {e}")
            st.stop()

        # ------ Phase 2 ------
        st.write(f"**Phase 2 — Cross-Review**")

        phase2_chief_user = PHASE2_USER.format(
            own_draft=chief_draft1, peer_draft=assistant_draft1
        )
        phase2_asst_user = PHASE2_USER.format(
            own_draft=assistant_draft1, peer_draft=chief_draft1
        )

        st.write(f"  {chief_label} (Chief) cross-reviewing...")
        try:
            chief_draft2 = call_model("chief", PHASE2_SYSTEM, phase2_chief_user, role_map)
        except Exception as e:
            st.error(f"Phase 2 failed — Chief Grader ({chief_label}): {e}")
            st.stop()

        st.write(f"  {asst_label} (Assistant) cross-reviewing...")
        try:
            assistant_draft2 = call_model("assistant", PHASE2_SYSTEM, phase2_asst_user, role_map)
        except Exception as e:
            st.error(f"Phase 2 failed — Assistant ({asst_label}): {e}")
            st.stop()

        # ------ Phase 3 ------
        st.write(f"**Phase 3 — Final Synthesis**")

        phase3_user = PHASE3_USER.format(
            prompt_text=prompt_text,
            rubric_text=rubric_text,
            chief_draft2=chief_draft2,
            assistant_draft2=assistant_draft2,
        )

        st.write(f"  {chief_label} (Chief) synthesizing final report...")
        try:
            final_report = call_model("chief", PHASE3_SYSTEM, phase3_user, role_map)
        except Exception as e:
            st.error(f"Phase 3 failed — Chief Grader ({chief_label}): {e}")
            st.stop()

        status.update(label="Grading complete!", state="complete", expanded=False)

    # --- Display results ---
    st.subheader("Final Grading Report")
    st.markdown(final_report)

    # --- PDF download ---
    try:
        pdf_bytes = markdown_to_pdf(final_report)
        st.download_button(
            label="Download Report as PDF",
            data=pdf_bytes,
            file_name="grading_report.pdf",
            mime="application/pdf",
        )
    except Exception as e:
        st.error(f"PDF generation failed: {e}")
