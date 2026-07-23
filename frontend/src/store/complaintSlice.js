import { createSlice } from "@reduxjs/toolkit";

const emptyForm = {
  complaint_source: "",
  customer_name: "",
  product_name: "",
  product_strength: "",
  batch_number: "",
  manufacturing_date: "",
  expiry_date: "",
  quantity_affected: "",
  complaint_type: "",
  complaint_date: "",
  description: "",
  initial_severity: "",
  priority: "",
  possible_duplicate: false,
  duplicate_count: 0,
};

const complaintSlice = createSlice({
  name: "complaint",
  initialState: {
    form: emptyForm,
    aiStatus: "idle", // idle | loading | success | error
    aiError: null,
    saveStatus: "idle", // idle | loading | success | error
  },
  reducers: {
    fieldChanged(state, action) {
      const { field, value } = action.payload;
      state.form[field] = value;
    },
    formReset(state) {
      state.form = emptyForm;
      state.aiStatus = "idle";
      state.aiError = null;
      state.saveStatus = "idle";
    },
    extractionStarted(state) {
      state.aiStatus = "loading";
      state.aiError = null;
    },
    extractionSucceeded(state, action) {
      state.aiStatus = "success";
      state.form = { ...state.form, ...action.payload };
    },
    extractionFailed(state, action) {
      state.aiStatus = "error";
      state.aiError = action.payload;
    },
    saveStarted(state) {
      state.saveStatus = "loading";
    },
    saveSucceeded(state) {
      state.saveStatus = "success";
    },
    saveFailed(state) {
      state.saveStatus = "error";
    },
  },
});

export const {
  fieldChanged,
  formReset,
  extractionStarted,
  extractionSucceeded,
  extractionFailed,
  saveStarted,
  saveSucceeded,
  saveFailed,
} = complaintSlice.actions;

export default complaintSlice.reducer;
