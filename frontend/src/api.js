import axios from "axios";

const API_BASE = "http://localhost:8000";

export async function extractComplaint(rawText) {
  const res = await axios.post(`${API_BASE}/extract-complaint`, { raw_text: rawText });
  return res.data.extracted;
}

export async function saveComplaint(form) {
  const res = await axios.post(`${API_BASE}/complaints`, form);
  return res.data;
}

export async function askAboutComplaint(question, complaintContext) {
  const res = await axios.post(`${API_BASE}/ask-about-complaint`, {
    question,
    complaint_context: complaintContext,
  });
  return res.data.answer;
}
