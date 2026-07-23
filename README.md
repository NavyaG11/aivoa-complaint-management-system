# AIVOA — AI-Powered Customer Complaint Management System

A Round 1 assignment project: a customer complaint intake tool for a
pharmaceutical manufacturing QMS. A user pastes or uploads a complaint
document, and an AI assistant (LangGraph + Groq) extracts structured
fields and auto-fills the complaint form.

## Architecture

```
frontend/   React + Redux Toolkit UI (form panel + AI assistant panel)
backend/    FastAPI service exposing /extract-complaint and /complaints
  app/graph.py   LangGraph pipeline (2 nodes): extract_fields -> classify_severity
  app/db.py      SQLAlchemy models + SQLite (swap to Postgres/MySQL via .env)
```

**Flow:** user pastes complaint text on the right → frontend calls
`POST /extract-complaint` → FastAPI runs the LangGraph pipeline, which
calls Groq (`gemma2-9b-it`) once to extract fields, then again to assign
severity/priority → structured JSON comes back → Redux merges it into the
form state → user reviews/edits → "Save Complaint" posts to `/complaints`
and stores it in the database.

## Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- A free Groq API key: https://console.groq.com

## Setup

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# open .env and paste your GROQ_API_KEY

uvicorn main:app --reload --port 8000
```

Backend now runs at `http://localhost:8000` (docs at `/docs`).

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Using it

1. Open `http://localhost:5173`.
2. On the right panel, click **"Paste Complaint Text / Email"**, paste in
   a sample complaint (see `sample-complaints/` for examples), and click
   **Extract Details**.
3. Watch the left form populate automatically.
4. Review/edit fields, then click **Save Complaint** to persist it.

You can also drag & drop a `.txt` file onto the dropzone. For PDF/DOCX,
paste the text instead — production-grade document parsing was explicitly
marked as not required for this assignment.

## Key design decisions

- **LangGraph kept to 2 sequential nodes** (`extract_fields` →
  `classify_severity`) rather than a single call, so severity/priority
  assessment is a distinct reasoning step the AI does *after* seeing the
  structured extraction — closer to how a real QA reviewer would work.
  This is also the easiest place to add more nodes later (e.g. a
  `duplicate_check` node) without restructuring anything else.
- **SQLite by default** so the project runs with zero external services;
  swapping to Postgres/MySQL is a one-line `.env` change since SQLAlchemy
  is already abstracting the database layer.
- **Redux Toolkit slice** holds both the form values and the AI
  request status (`idle/loading/success/error`), so the UI can show a
  live "Analyzing..." state without prop-drilling.
- **No OCR/document parsing library** was added, per the assignment note
  that this isn't required — text extraction from PDFs/DOCX is left as a
  "paste the text" step to keep the AI extraction step reliable within
  the time available.

## Bonus features

Not yet implemented — the current build focuses on the core required
loop (extract → review → save). If time allows, the next additions would
be a `duplicate_check` LangGraph node (compare new complaints against
existing ones by product + batch number) and a `complaint_summary` node
for the assistant chat box.
