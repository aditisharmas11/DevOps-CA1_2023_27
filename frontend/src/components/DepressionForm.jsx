import { useState } from "react";

export default function DepressionForm({ onSubmit, loading }) {
  const [values, setValues] = useState({
    academic_pressure:  3,
    work_pressure:      1,
    study_satisfaction: 3,
    sleep_hours:        6,
    financial_stress:   2,
    work_study_hours:   6,
    suicidal_thoughts:  0,
    family_history:     0,
    dietary_habits:     2,
  });

  function handleChange(key, val) {
    setValues(v => ({ ...v, [key]: parseFloat(val) }));
  }

  const sliders = [
    { key: "academic_pressure",  label: "Academic pressure",       hint: "1 = none, 5 = extreme",    min: 1, max: 5, step: 1 },
    { key: "work_pressure",      label: "Work pressure",           hint: "1 = none, 5 = extreme",    min: 1, max: 5, step: 1 },
    { key: "study_satisfaction", label: "Study satisfaction",      hint: "1 = very low, 5 = high",   min: 1, max: 5, step: 1 },
    { key: "sleep_hours",        label: "Sleep hours per night",   hint: "hours",                    min: 3, max: 12, step: 0.5 },
    { key: "financial_stress",   label: "Financial stress",        hint: "1 = none, 5 = severe",     min: 1, max: 5, step: 1 },
    { key: "work_study_hours",   label: "Work/Study hours per day",hint: "hours",                    min: 1, max: 16, step: 1 },
  ];

  return (
    <div className="form-card">
      <h2>Depression Risk Screening</h2>
      <p className="subtitle">Based on academic and lifestyle factors</p>

      {sliders.map(s => (
        <div className="question" key={s.key}>
          <div className="q-header">
            <label>{s.label}</label>
            <span className="q-value">{values[s.key]}</span>
          </div>
          <p className="q-hint">{s.hint}</p>
          <input
            type="range" min={s.min} max={s.max} step={s.step}
            value={values[s.key]}
            onChange={e => handleChange(s.key, e.target.value)}
          />
        </div>
      ))}

      <div className="question">
        <label>Dietary habits</label>
        <div className="options" style={{marginTop: '8px'}}>
          {[{label: 'Unhealthy', value: 1}, {label: 'Moderate', value: 2}, {label: 'Healthy', value: 3}].map(o => (
            <label key={o.value} className={`option ${values.dietary_habits === o.value ? 'selected' : ''}`}>
              <input type="radio" name="dietary" value={o.value} checked={values.dietary_habits === o.value}
                onChange={e => handleChange('dietary_habits', e.target.value)} />
              {o.label}
            </label>
          ))}
        </div>
      </div>

      <div className="question">
        <label>Have you ever had suicidal thoughts?</label>
        <div className="options" style={{marginTop: '8px'}}>
          {[{label: 'No', value: 0}, {label: 'Yes', value: 1}].map(o => (
            <label key={o.value} className={`option ${values.suicidal_thoughts === o.value ? 'selected' : ''}`}>
              <input type="radio" name="suicidal" value={o.value} checked={values.suicidal_thoughts === o.value}
                onChange={e => handleChange('suicidal_thoughts', e.target.value)} />
              {o.label}
            </label>
          ))}
        </div>
      </div>

      <div className="question">
        <label>Family history of mental illness?</label>
        <div className="options" style={{marginTop: '8px'}}>
          {[{label: 'No', value: 0}, {label: 'Yes', value: 1}].map(o => (
            <label key={o.value} className={`option ${values.family_history === o.value ? 'selected' : ''}`}>
              <input type="radio" name="family" value={o.value} checked={values.family_history === o.value}
                onChange={e => handleChange('family_history', e.target.value)} />
              {o.label}
            </label>
          ))}
        </div>
      </div>

      <button className="submit-btn" onClick={() => onSubmit(values)} disabled={loading}>
        {loading ? "Analyzing..." : "Run Depression Screening →"}
      </button>
    </div>
  );
}