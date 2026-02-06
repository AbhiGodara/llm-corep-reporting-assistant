def validate(report):
    errors = []
    values = {f["field_code"]: f["value"] for f in report["fields"]}

    if values.get("OF_010", 0) < 0:
        errors.append("CET1 cannot be negative")

    expected_total = (
        values.get("OF_010", 0) +
        values.get("OF_020", 0) +
        values.get("OF_030", 0)
    )

    if values.get("OF_040", 0) != expected_total:
        errors.append("Total Own Funds must equal CET1 + AT1 + Tier 2")

    return errors
