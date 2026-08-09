import { useState } from "react";

const questions = [
  { key: "sleep_quality",          label: "Sleep quality",              hint: "1 = very poor, 5 = excellent" },
  { key: "headaches_weekly",       label: "Headaches per week",         hint: "1 = none, 5 = daily" },
  { key: "academic_performance",   label: "Academic performance",       hint: "1 = struggling, 5 = excellent" },
  { key: "study_load",             label: "Study load",                 hint: "1 = light, 5 = overwhelming" },
  { key: "extracurricular_weekly", label: "Extracurricular activities", hint: "1 = few, 5 = many" },
];

export default function StressForm({ onSubmit, loading }) {
  const [values, setValues] = useState({
    sleep_quality: 3, headaches_weekly: 2, academic_performance: 3,
    study_load: 3, extracurricular_weekly: 2,
  });

  function handleChange(key, val) {
    setValues(v => ({ ...v, [key]: parseInt(val) }));
  }

  return (
    <div className="form-card">
      <h2>Stress Questionnaire</h2>
      <p className="subtitle">Rate each factor from 1 to 5</p>

      {questions.map(q => (
        <div className="question" key={q.key}>
          <div className="q-header">
            <label>{q.label}</label>
            <span className="q-value">{values[q.key]}</span>
          </div>
          <p className="q-hint">{q.hint}</p>
          <input
            type="range" min="1" max="5" step="1"
            value={values[q.key]}
            onChange={e => handleChange(q.key, e.target.value)}
          />
          <div className="range-labels"><span>1</span><span>2</span><span>3</span><span>4</span><span>5</span></div>
        </div>
      ))}

      <button className="submit-btn" onClick={() => onSubmit(values)} disabled={loading}>
        {loading ? "Analyzing..." : "Run Stress Screening →"}
      </button>
    </div>
  );
}