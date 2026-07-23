import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { extractionStarted, extractionSucceeded, extractionFailed } from "../store/complaintSlice";
import { extractComplaint } from "../api";

export default function AIAssistant() {
  const dispatch = useDispatch();
  const aiStatus = useSelector((s) => s.complaint.aiStatus);
  const aiError = useSelector((s) => s.complaint.aiError);
  const [pastedText, setPastedText] = useState("");
  const [showPaste, setShowPaste] = useState(false);
  const [fileName, setFileName] = useState(null);

  const runExtraction = async (rawText) => {
    if (!rawText || !rawText.trim()) return;
    dispatch(extractionStarted());
    try {
      const extracted = await extractComplaint(rawText);
      dispatch(extractionSucceeded(extracted));
    } catch (err) {
      console.error(err);
      dispatch(extractionFailed(err?.response?.data?.detail || "Extraction failed."));
    }
  };

  const handleFile = async (file) => {
    if (!file) return;
    setFileName(file.name);
    // Assignment says production-grade OCR/parsing isn't required — for
    // .txt files we read the text directly. For other types (pdf/docx),
    // ask the user to paste the text instead, which keeps things reliable
    // without needing a heavy parsing library.
    if (file.type === "text/plain" || file.name.endsWith(".txt")) {
      const text = await file.text();
      runExtraction(text);
    } else {
      dispatch(
        extractionFailed(
          "For PDF/DOCX files in this demo, please open the file and paste its text using 'Paste Complaint Text / Email' instead."
        )
      );
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    handleFile(e.dataTransfer.files?.[0]);
  };

  return (
    <div className="panel ai-panel">
      <div className="panel-header">
        <div className="ai-title">
          <span className="ai-dot" />
          <h2>AI Complaint Intake Assistant</h2>
        </div>
        <span className="beta-pill">BETA</span>
      </div>

      <div
        className="dropzone"
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        onClick={() => document.getElementById("file-input").click()}
      >
        <p>Drag &amp; drop complaint document here</p>
        <p className="or-browse">or <span>click to browse</span></p>
        <input
          id="file-input"
          type="file"
          accept=".txt,.pdf,.docx,.eml"
          hidden
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        {fileName && <p className="file-name">Selected: {fileName}</p>}
      </div>

      <div className="or-divider">OR</div>

      <button className="btn-secondary full-width" onClick={() => setShowPaste((v) => !v)}>
        Paste Complaint Text / Email
      </button>

      {showPaste && (
        <div className="paste-area">
          <textarea
            rows={6}
            placeholder="Paste the complaint email or document text here..."
            value={pastedText}
            onChange={(e) => setPastedText(e.target.value)}
          />
          <button className="btn-primary full-width" onClick={() => runExtraction(pastedText)}>
            Extract Details
          </button>
        </div>
      )}

      <p className="format-note">Supported formats: TXT (direct), PDF/DOCX/EML (paste text) — Max file size 10MB</p>

      {aiStatus === "loading" && (
        <div className="extraction-progress">
          <div className="progress-bar"><div className="progress-fill" /></div>
          <p>Analyzing document content and extracting key details...</p>
          <p className="muted">Please wait, this may take a few moments.</p>
        </div>
      )}

      {aiStatus === "error" && <p className="save-note error">{aiError}</p>}

      <div className="assistant-message">
        <span className="ai-dot small" />
        <p>
          {aiStatus === "success"
            ? "Done — I've populated the form with what I found. Please review before saving."
            : "Upload a complaint document or paste text above. I will automatically extract the details and populate the form for you."}
        </p>
      </div>

      <p className="disclaimer">AI responses may contain errors. Please verify information.</p>
    </div>
  );
}
