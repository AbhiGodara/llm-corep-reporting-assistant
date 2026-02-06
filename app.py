import streamlit as st
import json
import re

from rag.loader import load_documents
from rag.index import build_index
from rag.retriever import retrieve_context
from llm.generator import generate_report
from validation.rules import validate

st.title("LLM-Assisted COREP Own Funds Reporting Assistant")

scenario = st.text_area("Describe the reporting scenario", placeholder="E.g., A bank has issued 1 million GBP of AT1, 1 million GBP of Tier 2 and 2 million of CET1 capital instruments...")

question = st.text_input("Question", placeholder="E.g., What are the CET1, AT1, and Tier 2 values?")

def contains_numeric(value):
    return bool(re.search(r'\d', value))

if st.button("Generate Report"):
    if not scenario.strip() or not question.strip():
        st.warning("Please provide both scenario and question fields.")
        st.stop()
    if len(scenario.split()) < 5:
        st.warning("Scenario description is too short.")
        st.stop()
    if not contains_numeric(scenario):
        st.warning("Scenario must numeric financial value.")
        st.stop()

    docs = load_documents()
    db = build_index(docs)
    context = retrieve_context(db, question)

    raw_output = generate_report(context, scenario)
    report = json.loads(raw_output)

    if "error" in report:
        st.error(report["error"])
        st.stop()

    if "fields" not in report or not isinstance(report["fields"], list):
        st.error("Invalid report format received from LLM.")
        st.stop()

    all_zero=all(f["value"]==0 for f in report["fields"])
    if all_zero:
        st.error("All extracted values are zero, indicating possible extraction failure, scenario likely invalid or incomplete.")
        st.stop()

    st.subheader("COREP Template Extract")
    st.table(report["fields"])

    errors = validate(report)
    if errors:
        st.error(errors)
    else:
        st.success("Validation passed")

    st.subheader("Audit Log")
    for f in report["fields"]:
        st.write(f"**{f['field_code']}** → {f['justification']}")
