# Copilot Instructions

## Project Overview

A Python desktop app that lets users open a PDF, browse pages, and generate AI-powered multiple-choice questions (MCQs) from the current page using the Google Gemini API.

## Running the App

```bash
python main.py
```

No test suite or linter is configured.

## Dependencies

Install with:
```bash
pip install -r requirements.txt
```

Key libraries: `tkinter` (stdlib), `PyMuPDF` (`fitz`), `Pillow`, `google-generativeai`, `python-dotenv`.

## Architecture

The app has two alternating views managed by `app/pdf_viewer.py` (`PDFViewer`) and `app/mcq_generator.py` (`MCQGenerator`). **View switching is destructive**: when switching views, all widgets of the current view are destroyed and the next view's class is instantiated fresh into the same `tk.Tk` root window. There is no persistent state object shared between views — `PDFViewer` passes `pdf_doc` and `current_page` directly to `MCQGenerator` at switch time.

`MCQGenerator.switch_to_pdf()` uses a **local import** (`from .pdf_viewer import PDFViewer`) to avoid a circular top-level import between the two modules.

```
main.py
  └── app.pdf_viewer.PDFViewer(root)
        └── app.mcq_generator.MCQGenerator(root, pdf_doc, current_page)
              └── app.pdf_viewer.PDFViewer(root)   # local import on back-navigation
```

## Key Conventions

### Gemini MCQ format
`MCQGenerator.generate_mcq()` uploads a single-page PDF to Gemini and expects a strict plain-text response format parsed by `parse_mcq()` using three regex patterns:

- **Question**: `^\*\*(\d+)\.\s+(.*)\*\*$`
- **Option**: `^\((a|b|c|d)\)\s+(.*)$`
- **Answer**: `^\*\*Answer:\s+\((a|b|c|d)\)\s+(.*)\*\*$`

The prompt explicitly instructs the model to use this format. Any change to parsing logic must be mirrored in the Gemini prompt string.

### Temporary file
`generate_mcq()` writes a single-page PDF to `temp_page.pdf` in the working directory, uploads it to Gemini, then deletes it in a `finally` block. Always preserve this cleanup pattern.

### Gemini setup in utils.py
`utils.py` is the single source of truth for Gemini initialisation. It uses `google-genai` (the new SDK — **not** the deprecated `google-generativeai`). It creates `client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))` and exports `client`, `upload_to_gemini`, and `wait_for_files_active`. `mcq_generator.py` imports all three from `utils`. Do not add a second `genai.Client()` call elsewhere.

### API key
Set `GEMINI_API_KEY` in a `.env` file (not committed — see `.gitignore`). A `.env.example` template is included in the repo.
