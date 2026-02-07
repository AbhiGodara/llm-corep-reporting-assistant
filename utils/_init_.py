import re

def validate_scenario(scenario: str) -> tuple[bool, str]:
    """
    Validate scenario input.
    Returns (is_valid, message)
    """
    if not scenario or len(scenario.strip()) < 10:
        return False, "Scenario description is too short. Please provide more details."
    
    # Check for financial terms
    financial_terms = ['capital', 'million', 'funds', 'CET1', 'AT1', 'tier', 'value', 'amount']
    has_financial_terms = any(term.lower() in scenario.lower() for term in financial_terms)
    
    if not has_financial_terms:
        return False, "Scenario should mention capital amounts, values, or financial terms."
    
    return True, ""

def format_currency(value: float) -> str:
    """Format currency value for display"""
    if value is None:
        return "Not specified"
    
    if value >= 1000:
        return f"£{value:,.0f} million"
    else:
        return f"£{value:,.2f} million"

def create_audit_log(report) -> str:
    """Create human-readable audit log"""
    if not report or not report.fields:
        return "No fields extracted"
    
    log_lines = ["AUDIT LOG - Field Justifications", "=" * 50]
    
    for field in report.fields:
        if field.value is not None:
            log_lines.append(f"\n{field.field_code}: {field.description}")
            log_lines.append(f"  Value: {format_currency(field.value)}")
            log_lines.append(f"  Confidence: {field.confidence:.0%}")
            log_lines.append(f"  Justification: {field.justification}")
            if field.source_rule:
                log_lines.append(f"  Source: {field.source_rule}")
    
    return "\n".join(log_lines)
