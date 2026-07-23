"""
LangGraph pipeline for the AI Complaint Intake Assistant.

Two nodes, run in sequence:
  1. extract_fields     -> reads raw complaint text, returns structured fields as JSON
  2. classify_severity  -> looks at the extracted fields, assigns severity + priority

This is intentionally simple (a straight line, not a branching graph) so it's
easy to understand and extend. Add more nodes later (e.g. duplicate_check,
capa_recommendation) by adding a function + an edge — the pattern is the same.
"""
import json
import os
import re
from typing import TypedDict, Optional

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

load_dotenv()

MODEL_NAME = os.getenv("GROQ_MODEL", "gemma2-9b-it")


class ComplaintState(TypedDict):
    raw_text: str
    extracted: Optional[dict]
    error: Optional[str]
    existing_complaints: Optional[list]  # [{"batch_number": ..., "product_name": ...}, ...]


def _get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and paste your Groq API key in."
        )
    return ChatGroq(model=MODEL_NAME, api_key=api_key, temperature=0)


def _extract_json(text: str) -> dict:
    """LLMs sometimes wrap JSON in markdown fences or add stray text — pull the
    JSON object out defensively instead of trusting raw output."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output: {text[:200]}")
    return json.loads(match.group(0))


EXTRACTION_PROMPT = """You are an assistant inside a pharmaceutical Quality \
Management System (QMS). You will be given raw text from a customer complaint \
(an email, a scanned document transcript, or free text). Extract the following \
fields and return ONLY a single JSON object, no prose, no markdown fences.

Fields to extract (use "" if a field is not present in the text):
- complaint_source (e.g. "Email", "Phone Call", "Portal")
- customer_name
- product_name
- product_strength   (e.g. dosage/grade, like "500mg")
- batch_number
- manufacturing_date (format YYYY-MM-DD if possible)
- expiry_date        (format YYYY-MM-DD if possible)
- quantity_affected  (a number, units if mentioned)
- complaint_type      (e.g. "Product Quality", "Packaging Defect", "Adverse Event", "Delivery Issue")
- complaint_date      (format YYYY-MM-DD if possible)
- description          (a clear 1-3 sentence summary of what went wrong, in your own words)

Text to extract from:
---
{raw_text}
---

Return ONLY the JSON object."""


SEVERITY_PROMPT = """You are a Quality Assurance reviewer at a pharmaceutical \
company. Based on the extracted complaint details below, assign:
- initial_severity: one of "Low", "Medium", "High", "Critical"
  (Critical = patient safety risk / adverse event; High = product quality \
  failure affecting efficacy; Medium = packaging/labeling defect; Low = \
  delivery/service issue with no product quality impact)
- priority: one of "Low", "Medium", "High", "Urgent"

Complaint details:
{fields_json}

Return ONLY a JSON object with exactly these two keys: initial_severity, priority."""


def extract_fields(state: ComplaintState) -> ComplaintState:
    try:
        llm = _get_llm()
        prompt = EXTRACTION_PROMPT.format(raw_text=state["raw_text"])
        response = llm.invoke(prompt)
        fields = _extract_json(response.content)
        return {**state, "extracted": fields, "error": None}
    except Exception as exc:  # noqa: BLE001 - surface any failure to the API layer
        return {**state, "extracted": None, "error": str(exc)}


def classify_severity(state: ComplaintState) -> ComplaintState:
    if state.get("error") or not state.get("extracted"):
        return state
    try:
        llm = _get_llm()
        prompt = SEVERITY_PROMPT.format(fields_json=json.dumps(state["extracted"]))
        response = llm.invoke(prompt)
        severity_data = _extract_json(response.content)
        merged = {**state["extracted"], **severity_data}
        return {**state, "extracted": merged, "error": None}
    except Exception as exc:  # noqa: BLE001
        # Extraction still succeeded even if severity classification fails -
        # fall back to sensible defaults instead of losing the whole result.
        merged = {**state["extracted"], "initial_severity": "Medium", "priority": "Medium"}
        return {**state, "extracted": merged, "error": None}


def check_duplicates(state: ComplaintState) -> ComplaintState:
    """Bonus feature: flag if this complaint's batch number + product already
    exists in the database, so QA can catch repeat reports of the same issue.
    Pure Python matching (not an LLM call) - fast and deterministic, which is
    the right tool for exact-match lookups like this."""
    if state.get("error") or not state.get("extracted"):
        return state

    extracted = state["extracted"]
    batch = (extracted.get("batch_number") or "").strip().lower()
    product = (extracted.get("product_name") or "").strip().lower()
    existing = state.get("existing_complaints") or []

    matches = [
        c for c in existing
        if batch and product
        and (c.get("batch_number") or "").strip().lower() == batch
        and (c.get("product_name") or "").strip().lower() == product
    ]

    merged = {
        **extracted,
        "possible_duplicate": len(matches) > 0,
        "duplicate_count": len(matches),
    }
    return {**state, "extracted": merged}


def build_graph():
    graph = StateGraph(ComplaintState)
    graph.add_node("extract_fields", extract_fields)
    graph.add_node("classify_severity", classify_severity)
    graph.add_node("check_duplicates", check_duplicates)
    graph.set_entry_point("extract_fields")
    graph.add_edge("extract_fields", "classify_severity")
    graph.add_edge("classify_severity", "check_duplicates")
    graph.add_edge("check_duplicates", END)
    return graph.compile()


_compiled_graph = None


def run_complaint_pipeline(raw_text: str, existing_complaints: list | None = None) -> dict:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()

    result = _compiled_graph.invoke({
        "raw_text": raw_text,
        "extracted": None,
        "error": None,
        "existing_complaints": existing_complaints or [],
    })

    if result.get("error"):
        raise RuntimeError(result["error"])

    return result["extracted"]


def answer_complaint_question(question: str, complaint_context: dict) -> str:
    """Bonus feature: lets the assistant chat box answer free-form questions
    about the complaint currently on screen (e.g. 'what's the risk here?')."""
    llm = _get_llm()
    prompt = (
        "You are a QA assistant helping a reviewer understand a pharmaceutical "
        "customer complaint. Answer the question in 2-4 concise sentences, "
        "using only the complaint details given - if the details don't cover "
        "the question, say so plainly instead of guessing.\n\n"
        f"Complaint details:\n{json.dumps(complaint_context)}\n\n"
        f"Question: {question}"
    )
    response = llm.invoke(prompt)
    return response.content.strip()
