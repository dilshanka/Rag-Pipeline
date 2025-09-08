import json
import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np

st.set_page_config(
    page_title="RAG Evaluation Dashboard",
    layout="wide",  # <- this makes the app use full browser width
    initial_sidebar_state="expanded"
)

st.markdown(
    "<h1 style='text-align: center; font-size: 48px;'>📊 RAG Evaluation Dashboard</h1>",
    unsafe_allow_html=True
)

# Load evaluation results (metrics)
with open("evaluation/results.json", "r") as f:
    results = json.load(f)  # results.json contains list with one dict of metrics

metrics = ["faithfulness", "context_precision", "context_recall", "answer_similarity"]
overall_scores = {metric: np.mean([q.get(metric, 0) for q in results]) for metric in metrics}

st.header("1️⃣ Overall Evaluation Metrics")
overall_df = pd.DataFrame(list(overall_scores.items()), columns=["Metric", "Overall Score"])
st.dataframe(overall_df)

# Plot interactive bar chartOverall
fig = px.bar(
    overall_df,
    x="Metric",
    y="Overall Score",
    text="Overall Score",
    title="RAG Evaluation Results",
    color="Overall Score",
    color_continuous_scale="Blues"
)
fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
fig.update_layout(yaxis=dict(range=[0, 1.1]))
st.plotly_chart(fig)

st.header("2️⃣ Per-Question Evaluation")

for i, q in enumerate(results, 1):
    st.subheader(f"Question {i}")
    st.markdown(f"**User Input:** {q['user_input']}")
    st.markdown(f"**Reference Answer:** {q['reference']}")
    st.markdown(f"**Model Response:** {q['response']}")

    # Display retrieved contexts
    if q.get("retrieved_contexts"):
        st.markdown("**Retrieved Contexts:**")
        for idx, ctx in enumerate(q["retrieved_contexts"], 1):
            st.markdown(f"{idx}. {ctx}")

    # Display metrics for this question
    q_metrics = {metric: q.get(metric, 0) for metric in metrics}
    q_df = pd.DataFrame(list(q_metrics.items()), columns=["Metric", "Score"])
    st.dataframe(q_df)

    # Small bar chart for this question
    fig_q = px.bar(
        q_df,
        x="Metric",
        y="Score",
        text="Score",
        color="Score",
        color_continuous_scale="Blues",
        title=f"Question {i} Metrics"
    )
    fig_q.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig_q.update_layout(yaxis=dict(range=[0, 1.1]))
    st.plotly_chart(fig_q)
    st.markdown("---")
