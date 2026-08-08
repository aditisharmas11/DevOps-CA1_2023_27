from __future__ import annotations

import time
from html import escape

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from sklearn.metrics import classification_report, confusion_matrix

from inference_pipeline import IDSPredictor, load_artifact_table



# Documentation-only note: added 2026-08-08 to mark a small, non-functional
# clarifying comment. This change does not affect runtime behavior.
st.set_page_config(
    page_title="ML-Based IDS Demo",
    page_icon="ML",
    layout="wide",
)


def inject_custom_css() -> None:
    st.markdown(
        """
<style>
    .hero-card {
        border: 1px solid #d8e2f1;
        border-radius: 18px;
        padding: 1.1rem 1.2rem;
        background: linear-gradient(120deg, #f4f8ff 0%, #eefcf8 100%);
        margin-bottom: 0.9rem;
    }
    .hero-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #163059;
        margin-bottom: 0.25rem;
    }
    .hero-sub {
        color: #314e7a;
        font-size: 0.98rem;
    }
    .metric-card {
        border: 1px solid #dde6f3;
        border-radius: 12px;
        padding: 0.7rem;
        background: #ffffff;
    }
    .stat-card {
        border: 1px solid #1f3658;
        border-radius: 14px;
        padding: 0.8rem 0.9rem;
        background: linear-gradient(135deg, rgba(26, 39, 65, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
        min-height: 112px;
        margin-bottom: 0.45rem;
    }
    .stat-title {
        color: #c0d2ee;
        font-size: 0.95rem;
        margin-bottom: 0.22rem;
    }
    .stat-value {
        color: #f1f7ff;
        font-size: 2.05rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .result-card {
        border: 1px solid #30496d;
        border-radius: 12px;
        padding: 0.7rem 0.75rem;
        background: rgba(15, 23, 42, 0.55);
        min-height: 105px;
        margin-bottom: 0.5rem;
    }
    .result-title {
        color: #b9cbe7;
        font-size: 0.9rem;
        margin-bottom: 0.25rem;
    }
    .result-value {
        color: #f4f8ff;
        font-size: 1.95rem;
        font-weight: 700;
        line-height: 1.12;
        overflow-wrap: anywhere;
        word-break: break-word;
    }
    .mini-note {
        color: #c5d6ee;
        font-size: 0.85rem;
        margin-top: 0.15rem;
    }
    .block-container {
        padding-top: 1.1rem;
    }
</style>
        """,
        unsafe_allow_html=True,
    )


def render_app_header() -> None:
    st.markdown(
        """
<div class="hero-card">
    <div class="hero-title">ML-Based Intrusion Detection Demo</div>
    <div class="hero-sub">
        Offline, reproducible IDS demonstration using CNN-based multi-class traffic classification.
        This interface emphasizes signal quality, alert behavior, and explainability.
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_probability_chart(predictor: IDSPredictor, prediction_row: pd.Series) -> pd.DataFrame:
    rows = []
    for label in predictor.label_names:
        col = predictor.probability_columns[label]
        rows.append({"Label": label, "Probability": float(prediction_row[col])})

    prob_df = pd.DataFrame(rows).sort_values("Probability", ascending=False)

    fig, ax = plt.subplots(figsize=(7.4, 3.3))
    sns.barplot(data=prob_df, x="Probability", y="Label", ax=ax, hue="Label", legend=False, palette="crest")
    ax.set_xlim(0, 1)
    ax.set_title("Class Probability Distribution")
    ax.set_xlabel("Probability")
    ax.set_ylabel("Class")
    st.pyplot(fig, clear_figure=True)
    return prob_df


def render_stat_card(title: str, value: str) -> None:
    st.markdown(
        f"""
<div class="stat-card">
    <div class="stat-title">{escape(title)}</div>
    <div class="stat-value">{escape(value)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_result_card(title: str, value: str, note: str | None = None) -> None:
    safe_note = f'<div class="mini-note">{escape(note)}</div>' if note else ""
    st.markdown(
        f"""
<div class="result-card">
    <div class="result-title">{escape(title)}</div>
    <div class="result-value">{escape(value)}</div>
    {safe_note}
</div>
        """,
        unsafe_allow_html=True,
    )


def render_matrix_preview(predictor: IDSPredictor, selected_row: pd.DataFrame) -> None:
    tensor = predictor.transform_features(selected_row)
    matrix = tensor[0].reshape(predictor.grid_size, predictor.grid_size)

    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    sns.heatmap(matrix, cmap="magma", cbar=True, square=True, ax=ax)
    ax.set_title(f"Traffic Matrix ({predictor.grid_size}x{predictor.grid_size})")
    st.pyplot(fig, clear_figure=True)


@st.cache_resource
def get_predictor(assets_dir: str) -> IDSPredictor:
    return IDSPredictor(assets_dir=assets_dir)


@st.cache_data
def get_table(assets_dir: str, filename: str) -> pd.DataFrame:
    return load_artifact_table(assets_dir=assets_dir, filename=filename)


def render_overview_metrics(demo_samples: pd.DataFrame, replay_sequence: pd.DataFrame) -> None:
    attack_rows = int((demo_samples["Label"] != "BENIGN").sum())
    benign_rows = int((demo_samples["Label"] == "BENIGN").sum())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_stat_card("Demo Samples", f"{len(demo_samples):,}")
    with c2:
        render_stat_card("Known Classes", f"{demo_samples['Label'].nunique()}")
    with c3:
        render_stat_card("Attack Rows", f"{attack_rows:,}")
    with c4:
        render_stat_card("Replay Steps", f"{len(replay_sequence):,}")

    dist = demo_samples["Label"].value_counts().rename_axis("Label").reset_index(name="Count")
    dist = dist.sort_values("Count", ascending=False)

    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    sns.barplot(data=dist, y="Label", x="Count", ax=ax, hue="Label", legend=False, palette="viridis")
    ax.set_title("Demo Sample Label Distribution")
    ax.set_xlabel("Count")
    ax.set_ylabel("Traffic Label")
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    st.pyplot(fig, clear_figure=True)

    top_classes = ", ".join(dist.head(3)["Label"].tolist())

    with st.expander("Quick context for this demo", expanded=False):
        st.markdown(
            f"""
- BENIGN rows in demo subset: **{benign_rows:,}**
- Non-BENIGN rows in demo subset: **{attack_rows:,}**
- Most represented classes: **{top_classes}**
- Replay sequence starts with baseline normal traffic, then injects multiple attack classes.
- Alert policy used in UI: predicted label is not BENIGN and confidence is above threshold.
            """
        )


def run_single_sample_tab(
    predictor: IDSPredictor,
    demo_samples: pd.DataFrame,
    threshold: float,
) -> None:
    st.subheader("Single Sample Classification")

    available_labels = sorted(demo_samples["Label"].unique().tolist())
    selected_label = st.selectbox("Filter by true label", options=["All"] + available_labels)

    if selected_label == "All":
        filtered = demo_samples
    else:
        filtered = demo_samples[demo_samples["Label"] == selected_label]

    index_options = filtered.index.tolist()
    selected_index = st.selectbox("Choose sample row", options=index_options)
    selected_row = filtered.loc[[selected_index]].reset_index(drop=True)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.write("True label:", selected_row.iloc[0]["Label"])
        st.write("Feature count:", len(predictor.feature_columns))
        st.write("Alert threshold:", f"{threshold:.2f}")

        if st.button("Classify selected sample", type="primary", key="single_sample_classify"):
            result = predictor.predict(selected_row, alert_threshold=threshold).iloc[0]

            s1, s2, s3, s4 = st.columns([2.3, 2.3, 1.4, 1.3])
            with s1:
                render_result_card("True Label", str(result["Label"]))
            with s2:
                render_result_card("Predicted Label", str(result["predicted_label"]))
            with s3:
                render_result_card("Confidence", f"{result['confidence']:.2%}")
            with s4:
                render_result_card("Severity", result["severity"].upper() if result["alert"] else "NONE")

            if result["alert"]:
                st.error(
                    f"ALERT: {result['predicted_label']} detected "
                    f"(severity: {result['severity']}, confidence: {result['confidence']:.2%})"
                )
            else:
                st.success("No alert raised. Traffic considered safe or low-confidence non-benign.")

            prob_df = render_probability_chart(predictor, result)
            st.dataframe(prob_df.head(3).rename(columns={"Probability": "Top Probability"}), use_container_width=True, hide_index=True)

    with col_b:
        st.write("Model input preview")
        render_matrix_preview(predictor, selected_row)


def run_timeline_tab(
    predictor: IDSPredictor,
    replay_sequence: pd.DataFrame,
    threshold: float,
) -> None:
    st.subheader("Timeline Replay")
    st.caption("Runs a BENIGN baseline first, then attack traffic to demonstrate alerting.")

    max_steps = len(replay_sequence)
    step_count = st.slider("Replay steps", min_value=10, max_value=max_steps, value=min(50, max_steps), step=1)
    step_delay_ms = st.slider("Step delay (ms)", min_value=0, max_value=600, value=100, step=50)

    if st.button("Run replay", type="primary", key="timeline_replay"):
        subset = replay_sequence.head(step_count).copy()
        progress = st.progress(0)
        alert_box = st.empty()
        table_box = st.empty()

        events = []
        for idx in range(len(subset)):
            row = subset.iloc[[idx]].copy().reset_index(drop=True)
            result = predictor.predict(row, alert_threshold=threshold).iloc[0]

            events.append(
                {
                    "timeline_step": int(subset.iloc[idx]["timeline_step"]),
                    "true_label": row.iloc[0]["Label"],
                    "predicted_label": result["predicted_label"],
                    "confidence": float(result["confidence"]),
                    "alert": bool(result["alert"]),
                    "severity": result["severity"],
                }
            )

            recent = pd.DataFrame(events[-8:])
            table_box.dataframe(recent, use_container_width=True, hide_index=True)

            if result["alert"]:
                alert_box.error(
                    f"Attack detected at step {events[-1]['timeline_step']}: "
                    f"{result['predicted_label']} ({result['confidence']:.2%})"
                )
            else:
                alert_box.info(f"Step {events[-1]['timeline_step']}: No alert")

            progress.progress((idx + 1) / len(subset))
            if step_delay_ms > 0:
                time.sleep(step_delay_ms / 1000)

        full_results = pd.DataFrame(events)
        total_alerts = int(full_results["alert"].sum())
        st.success(f"Replay completed. Alerts raised: {total_alerts} / {len(full_results)}")

        col_1, col_2, col_3 = st.columns(3)
        col_1.metric("Total steps", len(full_results))
        col_2.metric("Alerts", total_alerts)
        col_3.metric("Attack recall in replay", f"{_attack_recall(full_results):.2%}")

        chart_data = full_results[["timeline_step", "confidence"]].set_index("timeline_step")
        st.line_chart(chart_data, height=250)

        severity_counts = full_results["severity"].value_counts().rename_axis("Severity").reset_index(name="Count")
        p1, p2 = st.columns(2)
        with p1:
            fig, ax = plt.subplots(figsize=(5.5, 3.4))
            sns.barplot(data=severity_counts, x="Severity", y="Count", ax=ax, hue="Severity", legend=False, palette="mako")
            ax.set_title("Alerts by Severity")
            st.pyplot(fig, clear_figure=True)

        with p2:
            pred_counts = full_results["predicted_label"].value_counts().rename_axis("Label").reset_index(name="Count")
            fig, ax = plt.subplots(figsize=(5.5, 3.4))
            sns.barplot(data=pred_counts, x="Label", y="Count", ax=ax, hue="Label", legend=False, palette="rocket")
            ax.set_title("Predicted Label Frequency")
            plt.xticks(rotation=35, ha="right")
            st.pyplot(fig, clear_figure=True)


def _attack_recall(df: pd.DataFrame) -> float:
    attack_mask = df["true_label"] != "BENIGN"
    if attack_mask.sum() == 0:
        return 0.0
    detected = (df.loc[attack_mask, "alert"] == True).sum()  # noqa: E712
    return float(detected / attack_mask.sum())


def run_batch_summary_tab(
    predictor: IDSPredictor,
    demo_samples: pd.DataFrame,
    threshold: float,
) -> None:
    st.subheader("Batch Summary")

    default_size = min(200, len(demo_samples))
    batch_size = st.slider(
        "Rows to evaluate",
        min_value=20,
        max_value=len(demo_samples),
        value=default_size,
        step=10,
    )

    randomize = st.checkbox("Randomize rows before evaluation", value=True)
    normalize_cm = st.checkbox("Show normalized confusion matrix", value=False)

    if st.button("Run batch evaluation", type="primary", key="batch_evaluate"):
        subset = demo_samples.sample(n=batch_size, random_state=42).reset_index(drop=True) if randomize else demo_samples.head(batch_size).copy().reset_index(drop=True)
        predictions = predictor.predict(subset, alert_threshold=threshold)

        y_true = predictions["Label"].tolist()
        y_pred = predictions["predicted_label"].tolist()

        report = classification_report(
            y_true,
            y_pred,
            labels=predictor.label_names,
            output_dict=True,
            zero_division=0,
        )

        report_df = pd.DataFrame(report).transpose().round(4)
        st.dataframe(report_df, use_container_width=True)

        macro_precision = float(report_df.loc["macro avg", "precision"])
        macro_recall = float(report_df.loc["macro avg", "recall"])
        weighted_f1 = float(report_df.loc["weighted avg", "f1-score"])
        accuracy = float(report_df.loc["accuracy", "precision"])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Accuracy", f"{accuracy:.2%}")
        m2.metric("Macro Precision", f"{macro_precision:.2%}")
        m3.metric("Macro Recall", f"{macro_recall:.2%}")
        m4.metric("Weighted F1", f"{weighted_f1:.2%}")

        cm = confusion_matrix(y_true, y_pred, labels=predictor.label_names)
        if normalize_cm:
            row_sums = cm.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1
            cm_to_plot = cm / row_sums
            fmt = ".2f"
        else:
            cm_to_plot = cm
            fmt = "d"

        fig, ax = plt.subplots(figsize=(8.5, 6.5))
        sns.heatmap(
            cm_to_plot,
            annot=True,
            fmt=fmt,
            cmap="Blues",
            xticklabels=predictor.label_names,
            yticklabels=predictor.label_names,
            ax=ax,
        )
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_title("Confusion Matrix (Normalized)" if normalize_cm else "Confusion Matrix")
        plt.xticks(rotation=30, ha="right")
        st.pyplot(fig, clear_figure=True)

        alerts = int(predictions["alert"].sum())
        attack_rows = int((predictions["Label"] != "BENIGN").sum())

        c1, c2, c3 = st.columns(3)
        c1.metric("Batch size", batch_size)
        c2.metric("Alerts raised", alerts)
        c3.metric("Attack rows", attack_rows)

        misclassified = predictions[predictions["Label"] != predictions["predicted_label"]].copy()
        if not misclassified.empty:
            st.markdown("**Top misclassified rows (sample):**")
            cols = ["Label", "predicted_label", "confidence", "alert", "severity"]
            st.dataframe(misclassified[cols].head(25), use_container_width=True, hide_index=True)
        else:
            st.success("No misclassifications in this evaluated subset.")


def run_model_insights_tab(predictor: IDSPredictor, demo_samples: pd.DataFrame, threshold: float) -> None:
    st.subheader("Model Insights")
    st.caption("Quick diagnostics computed on the current demo sample table.")

    max_rows = st.slider("Rows to use for diagnostics", min_value=200, max_value=len(demo_samples), value=min(800, len(demo_samples)), step=50)

    if st.button("Compute model insights", type="primary", key="model_insights"):
        subset = demo_samples.head(max_rows).copy().reset_index(drop=True)
        predictions = predictor.predict(subset, alert_threshold=threshold)

        per_class = (
            predictions.groupby("Label")
            .apply(lambda frame: (frame["Label"] == frame["predicted_label"]).mean())
            .reset_index(name="class_accuracy")
            .sort_values("class_accuracy", ascending=False)
        )

        fig, ax = plt.subplots(figsize=(9, 3.8))
        sns.barplot(data=per_class, x="Label", y="class_accuracy", ax=ax, hue="Label", legend=False, palette="cubehelix")
        ax.set_ylim(0, 1)
        ax.set_title("Per-Class Accuracy on Diagnostic Subset")
        ax.set_ylabel("Accuracy")
        plt.xticks(rotation=35, ha="right")
        st.pyplot(fig, clear_figure=True)

        confusions = predictions[predictions["Label"] != predictions["predicted_label"]].copy()
        if confusions.empty:
            st.success("No confusion pairs found in this diagnostic subset.")
        else:
            pair_counts = (
                confusions.groupby(["Label", "predicted_label"]).size().reset_index(name="count")
                .sort_values("count", ascending=False)
            )
            st.markdown("**Most frequent confusion pairs**")
            st.dataframe(pair_counts.head(15), use_container_width=True, hide_index=True)

        alert_rate = float(predictions["alert"].mean())
        confidence_mean = float(predictions["confidence"].mean())
        i1, i2, i3 = st.columns(3)
        i1.metric("Rows analyzed", f"{len(predictions):,}")
        i2.metric("Mean confidence", f"{confidence_mean:.2%}")
        i3.metric("Alert rate", f"{alert_rate:.2%}")


def main() -> None:
    inject_custom_css()
    render_app_header()

    with st.sidebar:
        st.header("Demo Controls")
        assets_dir = st.text_input("Assets directory", value="artifacts")
        threshold = st.slider("Alert confidence threshold", 0.50, 0.95, 0.70, 0.01)
        st.markdown("---")
        st.markdown("### Demo Notes")
        st.markdown(
            """
- Start with **Single Sample** for a quick prediction walkthrough.
- Use **Timeline Replay** to show alert behavior over time.
- Use **Batch Summary** for objective metrics.
- Use **Model Insights** for class-level diagnostics.
            """
        )

    try:
        predictor = get_predictor(assets_dir=assets_dir)
        demo_samples = get_table(assets_dir, "demo_samples.csv")
        replay_sequence = get_table(assets_dir, "replay_sequence.csv")
    except Exception as exc:  # broad to surface setup errors in UI
        st.error(f"Failed to load assets or model: {exc}")
        st.info("Run: uv run python prepare_demo_assets.py")
        return

    with st.expander("Demo Sample Overview (click to show/hide)", expanded=False):
        render_overview_metrics(demo_samples, replay_sequence)

    tabs = st.tabs(["Single Sample", "Timeline Replay", "Batch Summary", "Model Insights"])

    with tabs[0]:
        run_single_sample_tab(predictor, demo_samples, threshold)
    with tabs[1]:
        run_timeline_tab(predictor, replay_sequence, threshold)
    with tabs[2]:
        run_batch_summary_tab(predictor, demo_samples, threshold)
    with tabs[3]:
        run_model_insights_tab(predictor, demo_samples, threshold)


if __name__ == "__main__":
    main()
