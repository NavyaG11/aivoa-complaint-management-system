import { useDispatch, useSelector } from "react-redux";
import {
  fieldChanged,
  formReset,
  saveStarted,
  saveSucceeded,
  saveFailed,
} from "../store/complaintSlice";
import { saveComplaint } from "../api";

const SEVERITY_OPTIONS = ["", "Low", "Medium", "High", "Critical"];
const PRIORITY_OPTIONS = ["", "Low", "Medium", "High", "Urgent"];

function Field({ label, field, value, onChange, type = "text", monospace = false }) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      <input
        className={`field-input ${monospace ? "mono" : ""}`}
        type={type}
        value={value}
        placeholder="Awaiting AI extraction..."
        onChange={(e) => onChange(field, e.target.value)}
      />
    </label>
  );
}

export default function ComplaintForm() {
  const dispatch = useDispatch();
  const form = useSelector((s) => s.complaint.form);
  const saveStatus = useSelector((s) => s.complaint.saveStatus);

  const onChange = (field, value) => {
    dispatch(fieldChanged({ field, value }));
  };

  const handleSave = async () => {
    dispatch(saveStarted());
    try {
      const payload = { ...form, possible_duplicate: form.possible_duplicate ? "true" : "false" };
      await saveComplaint(payload);
      dispatch(saveSucceeded());
    } catch (err) {
      console.error(err);
      dispatch(saveFailed());
    }
  };

  return (
    <div className="panel form-panel">
      <div className="panel-header">
        <div>
          <h2>Log Customer Complaint</h2>
          <p className="subtitle">API &amp; FDF Quality Assurance Module</p>
        </div>
        <span className="status-pill">Pending Triage</span>
      </div>

      {form.possible_duplicate && (
        <div className="duplicate-banner">
          Possible duplicate — {form.duplicate_count} existing complaint(s) already
          logged for this product + batch number. Please review before saving.
        </div>
      )}

      <div className="section">
        <h3>1. Origin &amp; Customer Details</h3>
        <div className="grid-2">
          <Field label="Complaint Source" field="complaint_source" value={form.complaint_source} onChange={onChange} />
          <Field label="Customer Name" field="customer_name" value={form.customer_name} onChange={onChange} />
        </div>
      </div>

      <div className="section">
        <h3>2. Product &amp; Batch Identification</h3>
        <div className="grid-2">
          <Field label="Product Name" field="product_name" value={form.product_name} onChange={onChange} />
          <Field label="Product Strength / Grade" field="product_strength" value={form.product_strength} onChange={onChange} />
          <Field label="Batch / Lot Number" field="batch_number" value={form.batch_number} onChange={onChange} monospace />
          <Field label="Manufacturing Date" field="manufacturing_date" value={form.manufacturing_date} onChange={onChange} />
          <Field label="Expiry Date" field="expiry_date" value={form.expiry_date} onChange={onChange} />
          <Field label="Quantity Affected" field="quantity_affected" value={form.quantity_affected} onChange={onChange} />
        </div>
      </div>

      <div className="section">
        <h3>3. Complaint Details</h3>
        <div className="grid-2">
          <Field label="Complaint Type" field="complaint_type" value={form.complaint_type} onChange={onChange} />
          <Field label="Complaint Date" field="complaint_date" value={form.complaint_date} onChange={onChange} />
        </div>
        <label className="field">
          <span className="field-label">Detailed Complaint Description</span>
          <textarea
            className="field-input"
            rows={4}
            placeholder="Awaiting AI extraction..."
            value={form.description}
            onChange={(e) => onChange("description", e.target.value)}
          />
        </label>
      </div>

      <div className="section">
        <h3>4. Initial Assessment &amp; Priority</h3>
        <div className="grid-2">
          <label className="field">
            <span className="field-label">Initial Severity</span>
            <select
              className="field-input"
              value={form.initial_severity}
              onChange={(e) => onChange("initial_severity", e.target.value)}
            >
              {SEVERITY_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>{opt || "Awaiting AI extraction..."}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">Priority</span>
            <select
              className="field-input"
              value={form.priority}
              onChange={(e) => onChange("priority", e.target.value)}
            >
              {PRIORITY_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>{opt || "Awaiting AI extraction..."}</option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="form-actions">
        <button className="btn-secondary" onClick={() => dispatch(formReset())}>
          Reset Form
        </button>
        <button className="btn-primary" onClick={handleSave} disabled={saveStatus === "loading"}>
          {saveStatus === "loading" ? "Saving..." : "Save Complaint"}
        </button>
      </div>
      {saveStatus === "success" && <p className="save-note success">Complaint saved.</p>}
      {saveStatus === "error" && <p className="save-note error">Could not save — check the backend is running.</p>}
    </div>
  );
}
