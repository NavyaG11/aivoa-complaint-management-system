from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import init_db, get_db, Complaint
from app.graph import run_complaint_pipeline

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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract-complaint")
def extract_complaint(payload: ExtractRequest):
    """
    Takes raw complaint text (pasted email, document text, etc.) and returns
    structured fields extracted by the LangGraph + Groq pipeline.
    """
    if not payload.raw_text or not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text is empty")

    try:
        extracted = run_complaint_pipeline(payload.raw_text)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"AI extraction failed: {exc}")

    return {"extracted": extracted}


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
