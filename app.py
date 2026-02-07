import streamlit as st
import json
import pandas as pd
from datetime import datetime

from rag.loader import load_regulatory_documents
from rag.retriever import build_vector_store, retrieve_relevant_context
from llm.generator import ReportGenerator
from core.schemas import COREPReport
from utils._init_ import validate_scenario, format_currency, create_audit_log

# Page config
st.set_page_config(
    page_title="COREP Reporting Assistant",
    page_icon="🏛️",
    layout="wide"
)

if 'report_history' not in st.session_state:
    st.session_state.report_history = []

# Title and description
st.title("🏛️ COREP Own Funds Reporting Assistant")
st.markdown("""
Generate COREP regulatory reports from natural language descriptions.
This tool extracts capital values and maps them to COREP template C 01.00.
""")

# Sidebar with examples
with st.sidebar:
    st.header("📋 Example Scenarios")
    
    examples = {
        "Simple Complete": "Our bank has CET1 capital of £150 million, AT1 capital of £50 million, and Tier 2 capital of £75 million.",
        "Partial Information": "We have Common Equity Tier 1 of €200 million. Additional Tier 1 instruments are worth 45 million euros.",
        "With Calculation": "CET1 is 120 million GBP after deductions. AT1 capital instruments total 30 million. Tier 2 is 60 million.",
        "Complex Scenario": "Post-regulation adjustments: CET1 = 180M (after 20M goodwill deduction), AT1 = 65M, Tier 2 instruments = 90M with 5-year maturity."
    }
    
    selected_example = st.selectbox("Load example:", list(examples.keys()))
    if st.button("Use This Example"):
        st.session_state.example_scenario = examples[selected_example]
    
    st.divider()
    st.markdown("""
    **How to use:**
    1. Describe your capital amounts in the scenario
    2. Ask a specific question about COREP reporting
    3. Click Generate Report
    4. Review extracted values and audit log
    
    **Expected format:**
    - "CET1 capital of 150 million"
    - "AT1 instruments worth £50M"
    - "Tier 2: 75 million GBP"
    """)

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📝 Reporting Scenario")
    
    scenario = st.text_area(
        "Describe your capital position:",
        value=st.session_state.get('example_scenario', ''),
        placeholder="Example: 'Our bank has CET1 capital of £150 million, AT1 of £50M, and Tier 2 capital of £75 million...'",
        height=150
    )

with col2:
    st.subheader("❓ Your Question")
    
    question = st.text_input(
        "What would you like to know?",
        value="Extract capital values for COREP Own Funds reporting",
        placeholder="E.g., 'What are the CET1, AT1, and Tier 2 amounts?'"
    )
    
    st.info("💡 Include specific field names (CET1, AT1, Tier 2) for better results")

st.divider()

if st.button("🚀 Generate COREP Report", type="primary", use_container_width=True):
    # Validate input
    is_valid, message = validate_scenario(scenario)
    if not is_valid:
        st.error(f"⚠️ {message}")
        st.stop()
    
    with st.spinner("🔄 Processing... Retrieving regulations and extracting values"):
        
        try:
            docs = load_regulatory_documents()
            db = build_vector_store(docs)
            context = retrieve_relevant_context(db, question)
            
            # Show context in expander
            with st.expander("📚 Regulatory Context Retrieved", expanded=False):
                st.text(context[:1000] + ("..." if len(context) > 1000 else ""))
                
        except Exception as e:
            st.error(f"Failed to load regulatory documents: {str(e)}")
            st.stop()
        
        try:
            generator = ReportGenerator()
            result = generator.generate_report(context, scenario)
            
            # Handle errors
            if "error" in result:
                st.error(f"❌ {result['error']}")
                
                # Show troubleshooting tips
                with st.expander("💡 Troubleshooting Tips"):
                    st.markdown("""
                    **Common issues and solutions:**
                    1. **No values extracted**: Make sure you mention specific amounts with currency
                    2. **Format issues**: Try "150 million GBP" instead of just "150"
                    3. **Field names**: Use "CET1", "AT1", "Tier 2" explicitly
                    4. **Example format**: "CET1 capital is £150 million, AT1 is €50M"
                    """)
                st.stop()
            
            # Get the report
            report = result["report"]
            
            # Check if report is empty
            if report.is_empty:
                st.warning("⚠️ No values could be extracted from the scenario.")
                st.markdown("""
                **Possible reasons:**
                - No explicit amounts mentioned
                - Amounts mentioned without currency units
                - Values described qualitatively instead of numerically
                
                **Try being more specific:**
                - "CET1 capital of 150 million GBP"
                - "AT1 instruments worth €50,000,000"
                - "Tier 2: 75M"
                """)
                st.stop()
            
            # Step 3: Display results
            st.subheader("📋 Extracted COREP Report")
            
            # Create table
            table_data = []
            for field in report.fields:
                table_data.append({
                    "Field": field.field_code,
                    "Description": field.description,
                    "Value": format_currency(field.value) if field.value is not None else "Not specified",
                    "Confidence": f"{field.confidence:.0%}",
                    "Source": field.source_rule[:50] + "..." if len(field.source_rule) > 50 else field.source_rule
                })
            
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.subheader("✅ Validation Results")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                extracted_count = sum(1 for f in report.fields if f.value is not None)
                total_fields = len(report.fields)
                st.metric("Fields Extracted", f"{extracted_count}/{total_fields}")
            
            with col2:
                avg_confidence = report.confidence_score
                st.metric("Average Confidence", f"{avg_confidence:.0%}")
            
            with col3:
                # Basic validation
                errors = []
                field_map = {f.field_code: f for f in report.fields}
                
                # Check for negative values
                for field in report.fields:
                    if field.value is not None and field.value < 0:
                        errors.append(f"{field.field_code} cannot be negative")
                
                # Check total calculation
                cet1 = field_map.get("OF_010")
                at1 = field_map.get("OF_020")
                tier2 = field_map.get("OF_030")
                total = field_map.get("OF_040")
                
                if all(f and f.value is not None for f in [cet1, at1, tier2, total]):
                    expected = cet1.value + at1.value + tier2.value
                    if abs(total.value - expected) > 0.01:
                        errors.append(f"Total ({total.value}) doesn't match sum ({expected})")
                
                if errors:
                    st.error(f"{len(errors)} issues found")
                else:
                    st.success("All validations passed")
            
            # Show errors if any
            if errors:
                with st.expander("🔍 Validation Details", expanded=True):
                    for error in errors:
                        st.error(f"• {error}")
            
            # Step 5: Show audit log
            st.subheader("📝 Audit Trail")
            audit_log = create_audit_log(report)
            st.text_area("Field-by-field justification:", audit_log, height=300)
            
            # Step 6: Export options
            st.subheader("💾 Export")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # JSON export
                report_json = report.to_json()
                st.download_button(
                    label="Download JSON Report",
                    data=report_json,
                    file_name=f"corep_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                # CSV export
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"corep_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            # Add to history
            st.session_state.report_history.append({
                "timestamp": datetime.now().isoformat(),
                "scenario": scenario[:100] + "...",
                "question": question,
                "confidence": avg_confidence,
                "fields_extracted": extracted_count
            })
            
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {str(e)}")
            st.exception(e)

# History section
if st.session_state.report_history:
    st.divider()
    st.subheader("📜 Generation History")
    
    history_df = pd.DataFrame(st.session_state.report_history)
    st.dataframe(
        history_df.tail(5),  # Show last 5 entries
        use_container_width=True,
        hide_index=True,
        column_config={
            "timestamp": "Time",
            "scenario": "Scenario",
            "question": "Question",
            "confidence": st.column_config.NumberColumn(
                "Confidence",
                format="%.0f%%"
            ),
            "fields_extracted": "Fields"
        }
    )
    
    if st.button("Clear History"):
        st.session_state.report_history = []
        st.rerun()

# Footer
st.divider()
st.caption("""
**COREP Reporting Assistant v1.0** | This tool assists with COREP Own Funds template (C 01.00) reporting.
For official submissions, always verify with qualified regulatory reporting professionals.
""")
