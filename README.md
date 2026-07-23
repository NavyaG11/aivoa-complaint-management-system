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

### 0. Database — SQLite (default) or Postgres

The project runs on SQLite out of the box, zero setup. To use real Postgres
(the assignment's mandatory stack), the fastest path is a free hosted
instance — no local Postgres install needed:

1. Create a free project at https://neon.tech
2. Copy the connection string it gives you
3. In `backend/.env`, set:
   ```
   DATABASE_URL=postgresql://user:password@ep-xxxx.neon.tech/dbname?sslmode=require
   ```
4. Restart the backend — SQLAlchemy handles the rest, no code changes needed.

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

- **Duplicate Complaint Detection** — a third LangGraph node
  (`check_duplicates`) runs after severity classification. It compares the
  new complaint's product + batch number against every complaint already in
  the database (passed in as part of the graph's starting state) and flags
  `possible_duplicate: true` if a match is found. This is plain Python
  matching, not an LLM call — exact-match lookups don't need a model, so the
  node stays fast and deterministic. The frontend shows a red banner on the
  form when this flag comes back true.
- **Complaint Q&A chat** — the "Ask me anything about this complaint" box in
  the AI panel is wired to a real endpoint (`/ask-about-complaint`). It sends
  the current form state as context to Groq and returns a short, grounded
  answer — e.g. "what's the likely risk category here?" It's a single LLM
  call, kept outside the LangGraph pipeline since it's a one-shot Q&A rather
  than a sequential extraction step.

Not implemented (time-boxed): Complaint Completeness Checker, Root Cause /
CAPA Recommendation, AI Risk Classification as a separate feature (severity
classification already covers a version of this).
