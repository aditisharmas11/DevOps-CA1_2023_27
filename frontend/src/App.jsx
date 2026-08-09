import { useState } from "react";
import StressForm from "./components/StressForm";
import DepressionForm from "./components/DepressionForm";
import Results from "./components/Results";
import "./App.css";

export default function App() {
  const [tab, setTab] = useState("stress");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const API = import.meta.env.VITE_API_URL || "http://localhost:5000";

  async function submitStress(data) {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API}/predict/stress`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const json = await res.json();
      setResult({ type: "stress", ...json });
    } catch (e) {
      alert("Could not connect to backend. Make sure Flask is running.");
    }
    setLoading(false);
  }

  async function submitDepression(data) {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API}/predict/depression`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const json = await res.json();
      setResult({ type: "depression", ...json });
    } catch (e) {
      alert("Could not connect to backend. Make sure Flask is running.");
    }
    setLoading(false);
  }

  return (
    <div className="app">
      <header>
        <h1>🧠 Mental Health Screening</h1>
        <p>Autonomous AI-powered screening for stress and depression</p>
      </header>

    <div className="tabs">
        <button className={tab === "stress" ? "active" : ""} onClick={() => { setTab("stress"); setResult(null); }}>
          Stress Screening
        </button>
        <button className={tab === "depression" ? "active" : ""} onClick={() => { setTab("depression"); setResult(null); }}>
          Depression Screening
        </button>
      </div>

      <main>
        {tab === "stress" && <StressForm onSubmit={submitStress} loading={loading} />}
        {tab === "depression" && <DepressionForm onSubmit={submitDepression} loading={loading} />}
        {result && <Results result={result} />}
      </main>
      <footer>
        <p>Built with Agentic AI — SIT Pune AI Course Project</p>
      </footer>
    </div>
  );
}