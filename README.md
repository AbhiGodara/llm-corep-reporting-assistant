# 🏛️ COREP Regulatory Reporting Assistant

An AI-powered tool that helps banks prepare COREP regulatory reports by extracting capital values from natural language and mapping them to COREP templates.

## 🚀 Live Demo
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://abhishek-llm-corep-reporting-assistant.streamlit.app/)

## 📋 Features
- ✅ Extract CET1, AT1, Tier 2 capital values from natural language
- ✅ Map to COREP template C 01.00 (Own Funds)
- ✅ Validate against regulatory rules
- ✅ Generate audit trail with justifications
- ✅ Export to JSON and CSV formats
- ✅ User-friendly web interface
- ✅ Example scenarios for quick testing

## 🛠️ Technology Stack
- **LLM**: Groq API with llama-3.3-70b-versatile
- **Framework**: LangChain
- **Vector Store**: FAISS with sentence-transformers
- **UI**: Streamlit
- **Validation**: Pydantic schemas
- **Data Processing**: Pandas, NumPy

## 🏗️ Project Structure

## How to Run

### 1. Clone the Repository
```bash
git clone https://github.com/AbhiGodara/llm-corep-reporting-assistant.git
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Environment Variable
```bash
GROQ_API_KEY=your_groq_api_key
```

### 4. Run the App
```bash
streamlit run app.py
```
