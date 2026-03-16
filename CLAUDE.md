# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Required API keys in `.env` (see `.env.example`): `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `nvidia_api_key`. Only the keys for the two selected models are needed at runtime.

## Architecture

Single-file Streamlit app (`app.py`, ~400 lines) implementing a 3-phase multi-agent grading workflow:

1. **Phase 1 (Independent Analysis):** Both models grade the essay independently against the rubric, producing Draft 1.
2. **Phase 2 (Cross-Review):** Each model reviews the other's Draft 1 and produces a refined Draft 2.
3. **Phase 3 (Final Synthesis):** The Chief Grader combines both Draft 2s into the final report.

Three models available: `claude-opus-4-6` (Anthropic SDK), `gemini-2.5-pro` (Google GenAI SDK), `moonshotai/kimi-k2.5` (OpenAI SDK targeting NVIDIA Build API). The user picks any two as Chief and Assistant via sidebar selectboxes.

Key flow: `call_model()` dispatches to `call_claude()`, `call_gemini()`, or `call_kimi()` based on a `role_map` dict. The `MODEL_OPTIONS` dict maps display names to internal keys; `MODEL_KEY_REQUIRED` maps internal keys to their env var names for validation. The Chief Grader always produces the Phase 3 synthesis.

## Development Guidelines

- Keep all logic in `app.py` unless it exceeds ~400 lines.
- PDF generation (`markdown_to_pdf`, `_render_rich_line`) uses `fpdf2` with built-in Helvetica — **ASCII only, no Unicode symbols**. The `_sanitize_for_pdf()` function converts common Unicode chars (em-dashes, curly quotes, bullets, etc.) to ASCII before rendering; anything else is replaced via latin-1 encoding fallback.
- File parsing: `.txt` (UTF-8 decode) and `.pdf` (PyPDF2). The `extract_text()` function handles both.
- Wrap every API call and file operation in try/except; surface errors via `st.error`.
- Prompt templates (`PHASE1_*`, `PHASE2_*`, `PHASE3_*`) are module-level constants using `.format()` interpolation.
