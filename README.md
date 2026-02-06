# LLM-Assisted COREP Own Funds Reporting Assistant

This project is a prototype of an AI-assisted regulatory reporting tool for UK COREP Own Funds returns. It demonstrates how a Large Language Model (LLM) can assist in interpreting regulatory text and mapping natural-language scenarios to structured COREP template fields.

---

## What This Prototype Does
- Accepts a natural-language reporting scenario and question
- Retrieves relevant regulatory guidance from a local text source
- Generates structured COREP Own Funds output using an LLM
- Populates a human-readable COREP template extract
- Applies basic validation rules
- Provides an audit log explaining how each field was derived

---

## Scope
- COREP Template: Own Funds
- Fields Covered:
  - CET1 Capital
  - AT1 Capital
  - Tier 2 Capital
  - Total Own Funds
- Designed as a proof-of-concept, not a production system

---

## Regulatory Text
This prototype uses a simplified and representative extract of PRA Rulebook and COREP Own Funds instructions stored locally for demonstration purposes. In a real-world system, this would be replaced with a maintained regulatory document repository.

---

## Design Approach
- Retrieval-Augmented Generation (RAG) to ground the LLM in regulatory text
- Structured JSON output to reduce hallucinations
- Fail-closed behavior: incomplete or ambiguous inputs are rejected
- Basic consistency validation for reported values

---

## How to Run

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Set Environment Variable
```bash
GROQ_API_KEY=your_groq_api_key
```

### Run the App
```bash
streamlit run app.py
```
