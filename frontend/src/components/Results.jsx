const STRESS_RESOURCES = [
  "Deep breathing exercises (5 min, 3x daily)",
  "Set realistic daily goals and prioritize tasks",
  "Take 10-minute walks between study sessions",
  "Mindfulness Apps: Headspace or Calm (free for students)",
  "Crisis Text Line: Text HOME to 741741",
];

const CRISIS_RESOURCES = [
  "University Counseling Center: Free confidential appointments",
  "National Helpline: 988 (Suicide & Crisis Lifeline)",
  "Crisis Text Line: Text HOME to 741741",
];

function StressResult({ result }) {
  const colors = { "Low Stress": "#22c55e", "Moderate Stress": "#f59e0b", "High Stress": "#ef4444" };
  const color = colors[result.label] || "#f59e0b";

  return (
    <div className="result-card">
      <div className="result-header">
        <h2 style={{ color }}>{result.label}</h2>
        <div className="badges">
          <span className="badge">Confidence: {result.confidence}%</span>
          <span className="badge">Risk Score: {result.risk_score}/5</span>
        </div>
      </div>

      <div className="progress-wrap">
        <div className="progress-bar" style={{ width: `${(result.risk_score / 5) * 100}%`, background: color }} />
      </div>

      <div className="agent-box">
        <p className="agent-label">🤖 Agent reasoning</p>
        <p>Risk level detected: <strong>{result.label}</strong></p>
        <p>Decision: <code>{result.action.replace(/_/g, ' ')}</code></p>
      </div>

      {result.action === "provide_reassurance" && (
        <div className="message success">
          ✅ Your stress levels appear manageable. Keep up good sleep hygiene and time management.
        </div>
      )}
      {result.action === "recommend_resources" && (
        <div>
          <div className="message warning">⚠️ You're experiencing moderate stress. Here are some resources:</div>
          <ul className="resource-list">
            {STRESS_RESOURCES.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}
      {result.action === "escalate_to_human" && (
        <div>
          <div className="message danger">🚨 High stress detected. Please reach out for support.</div>
          <ul className="resource-list">
            {CRISIS_RESOURCES.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}

function DepressionResult({ result }) {
  const colors = { 0: "#22c55e", 1: "#f59e0b", 2: "#ef4444" };
  const color = colors[result.level] || "#f59e0b";

  return (
    <div className="result-card">
      <div className="result-header">
        <h2 style={{ color }}>{result.severity}</h2>
        <div className="badges">
          <span className="badge">Risk Score: {result.total_score}/5</span>
        </div>
      </div>

      <div className="progress-wrap">
        <div className="progress-bar" style={{ width: `${(result.total_score / 5) * 100}%`, background: color }}/>
      </div>

      {result.high_risk && (
        <div className="message danger">
          🚨 You indicated thoughts of self-harm. Please reach out immediately — you are not alone.
          <br /><strong>988</strong> | Text HOME to <strong>741741</strong>
        </div>
      )}
      {result.level <= 1 && !result.high_risk && (
        <div className="message success">✅ Minimal symptoms. Maintain healthy habits.</div>
      )}
      {result.level === 2 && !result.high_risk && (
        <div className="message warning">⚠️ Moderate symptoms. Talking to a counselor is recommended.</div>
      )}
      {result.level >= 3 && !result.high_risk && (
        <div>
          <div className="message danger">Significant symptoms detected. Please seek professional support.</div>
          <ul className="resource-list">
            {CRISIS_RESOURCES.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function Results({ result }) {
  return result.type === "stress"
    ? <StressResult result={result} />
    : <DepressionResult result={result} />;
}