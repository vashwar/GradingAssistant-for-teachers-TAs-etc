# AI Grading Assistant

A multi-agent AI grading tool that uses **Claude Opus 4.6** and **Gemini 2.5 Pro** in a collaborative workflow to grade student essays against a rubric. Built with Streamlit.

## How It Works

The tool runs a 3-phase multi-agent workflow:

1. **Phase 1 — Independent Analysis:** Both models independently analyze the student essay against the assignment prompt and rubric, producing Draft 1.
2. **Phase 2 — Cross-Review:** Each model reviews the other's Draft 1, identifying missed insights and refining their analysis into Draft 2.
3. **Phase 3 — Final Synthesis:** The Chief Grader combines both Draft 2 analyses into a single authoritative report.

You choose which model acts as **Chief Grader** (final decision-maker) and which acts as **Assistant** via the sidebar.

## Final Report Format

The generated report includes:

- **Strengths and Weaknesses** — detailed breakdown of what worked and what fell short
- **Rubric Item Breakdown** — every rubric item addressed with specific evidence from the essay
- **Suggested Grading** — a score/grade recommendation tied to the rubric's scale

Reports can be downloaded as PDF.

## Setup

### Prerequisites

- Python 3.9+
- An [Anthropic API key](https://console.anthropic.com/)
- A [Google Gemini API key](https://aistudio.google.com/apikey)

### Installation

```bash
git clone https://github.com/vashwar/GradingAssistant-for-teachers-TAs-etc.git
cd GradingAssistant-for-teachers-TAs-etc
pip install -r requirements.txt
```

### Configure API Keys

Copy the example env file and add your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```
ANTHROPIC_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

### Run

```bash
streamlit run app.py
```

## Usage

1. Select the **Chief Grader** model in the sidebar (Claude Opus 4.6 or Gemini 2.5 Pro).
2. Upload three documents (.txt or .pdf):
   - Assignment Prompt
   - Grading Rubric
   - Student Essay
3. Click **Process Grading** and wait for all 3 phases to complete.
4. Review the final report and download it as a PDF.

## Tech Stack

- [Streamlit](https://streamlit.io/) — UI framework
- [Anthropic SDK](https://docs.anthropic.com/) — Claude Opus 4.6
- [Google GenAI SDK](https://ai.google.dev/) — Gemini 2.5 Pro
- [fpdf2](https://py-pdf.github.io/fpdf2/) — PDF generation
- [PyPDF2](https://pypdf2.readthedocs.io/) — PDF text extraction

## License

MIT
