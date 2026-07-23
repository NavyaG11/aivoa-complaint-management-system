import ComplaintForm from "./components/ComplaintForm";
import AIAssistant from "./components/AIAssistant";
import "./App.css";

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-mark">AIVOA</span>
        <span className="app-header-title">Customer Complaint Management System</span>
      </header>
      <main className="app-main">
        <ComplaintForm />
        <AIAssistant />
      </main>
    </div>
  );
}
