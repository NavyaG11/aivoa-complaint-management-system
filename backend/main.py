from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import init_db, get_db, Complaint
from app.graph import run_complaint_pipeline, answer_complaint_question

app = FastAPI(title="AIVOA Complaint Intake API")

# Allow the React dev server (localhost:5173 for Vite) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


class ExtractRequest(BaseModel):
    raw_text: str


class AskRequest(BaseModel):
    question: str
    complaint_context: dict


class ComplaintIn(BaseModel):
    complaint_source: str = ""
    customer_name: str = ""
    product_name: str = ""
    product_strength: str = ""
    batch_number: str = ""
    manufacturing_date: str = ""
    expiry_date: str = ""
    quantity_affected: str = ""
    complaint_type: str = ""
    complaint_date: str = ""
    description: str = ""
    initial_severity: str = ""
    priority: str = ""
    possible_duplicate: str = "false"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract-complaint")
def extract_complaint(payload: ExtractRequest, db: Session = Depends(get_db)):
    """
    Takes raw complaint text (pasted email, document text, etc.) and returns
    structured fields extracted by the LangGraph + Groq pipeline. Also passes
    existing complaints in so the duplicate-check node can flag repeats.
    """
    if not payload.raw_text or not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text is empty")

    existing = [
        {"batch_number": c.batch_number, "product_name": c.product_name}
        for c in db.query(Complaint).all()
    ]

    try:
        extracted = run_complaint_pipeline(payload.raw_text, existing_complaints=existing)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"AI extraction failed: {exc}")

    return {"extracted": extracted}


@app.post("/ask-about-complaint")
def ask_about_complaint(payload: AskRequest):
    """Bonus feature: free-form Q&A about the complaint currently in the form,
    powered by the assistant chat box in the UI."""
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="question is empty")
    try:
        answer = answer_complaint_question(payload.question, payload.complaint_context)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Assistant failed: {exc}")
    return {"answer": answer}


@app.post("/complaints")
def save_complaint(payload: ComplaintIn, db: Session = Depends(get_db)):
    complaint = Complaint(**payload.model_dump())
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return {"id": complaint.id, "message": "Complaint saved"}


@app.get("/complaints")
def list_complaints(db: Session = Depends(get_db)):
    complaints = db.query(Complaint).order_by(Complaint.id.desc()).all()
    return [
        {
            "id": c.id,
            "customer_name": c.customer_name,
            "product_name": c.product_name,
            "batch_number": c.batch_number,
            "complaint_type": c.complaint_type,
            "initial_severity": c.initial_severity,
            "priority": c.priority,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in complaints
    ]
