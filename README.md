# AI Study Companion

A Python desktop app that turns any PDF into an interactive quiz. Open a document, navigate to a page, and let Google Gemini generate 10 multiple-choice questions from it. Answer all questions correctly to return to the PDF.

## Features

- Browse multi-page PDFs with previous/next navigation and direct page-jump
- Generate 10 multiple-choice questions from the current page using Gemini 1.5 Flash
- Interactive quiz UI with radio-button answer selection
- Answer validation — all 10 must be correct to proceed; incorrect attempts let you retry
- Returning from the quiz restores you to the same page you were on

## Requirements

- Python 3.9+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)
- Dependencies listed in `requirements.txt`:
  - [PyMuPDF](https://pymupdf.readthedocs.io/) — PDF rendering and text extraction
  - [Pillow](https://pillow.readthedocs.io/) — image handling for the PDF canvas
  - [google-generativeai](https://pypi.org/project/google-generativeai/) — Gemini API client
  - [python-dotenv](https://pypi.org/project/python-dotenv/) — loads `.env` variables

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/ai_study_companion.git
cd ai_study_companion

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API key
cp .env.example .env
# Open .env and replace 'your_key_here' with your Gemini API key
```

`.env` contents:
```
GEMINI_API_KEY=your_actual_key_here
```

## Usage

```bash
python main.py
```

| Button | Description |
|---|---|
| **Open PDF** | Opens a file picker to load a PDF |
| **Previous Page** / **Next Page** | Navigate one page at a time |
| *(page entry field)* | Type `n/total` or just `n` and press Enter to jump to a specific page |
| **Generate MCQs** | Sends the current page to Gemini and opens the quiz view |
| **Submit Answer** | Checks all selected answers; shows result and allows retry if any are wrong |
| **Return to PDF** | Goes back to the PDF viewer (available at any time during the quiz) |

## Project Structure

```
ai_study_companion/
├── main.py                  # Entry point — creates the Tk root and launches PDFViewer
├── requirements.txt         # Python dependencies
├── .env.example             # API key template (copy to .env)
└── app/
    ├── __init__.py          # Package marker
    ├── utils.py             # Gemini client setup; upload_to_gemini and wait_for_files_active helpers
    ├── pdf_viewer.py        # PDFViewer class — PDF browsing view
    └── mcq_generator.py     # MCQGenerator class — quiz view and question parsing
```

## How It Works

1. **Text extraction** — PyMuPDF (`fitz`) extracts the text layer from the current page and writes it to a temporary single-page PDF (`temp_page.pdf`).
2. **Upload to Gemini** — The temporary PDF is uploaded via the Gemini Files API and polled until active.
3. **Question generation** — Gemini 1.5 Flash is prompted to produce 10 MCQs in a strict plain-text format.
4. **Regex parsing** — `MCQGenerator.parse_mcq()` parses the response using three patterns:
   - Questions: `**N. question text**`
   - Options: `(a) option text`
   - Answers: `**Answer: (a) answer text**`
5. **Quiz UI** — Questions and radio buttons are rendered in a scrollable tkinter canvas. The user must select an answer for every question and submit; all 10 must be correct to return to the PDF.

## Known Limitations

- **Scanned / image-based PDFs** — PyMuPDF can only extract machine-readable text. Pages that are scanned images or contain no text layer will produce empty or low-quality questions.

