"""
Decide qué hacer con cada campo enriquecido, después de pasar por confidence_engine:
  - HIGH o MEDIUM con valor no vacío -> aplica al dataset enriquecido (enriched_dataset.csv)
  - LOW, o vacío -> va solo a suggested_values.csv, NUNCA sobrescribe el dataset original
"""
import confidence_engine


def validate_field_result(field, raw_value, raw_confidence, raw_evidence, raw_reason):
    value, confidence, evidence, reason, notes = confidence_engine.adjust_confidence(
        field, raw_value.strip(), raw_confidence.strip().upper(), raw_evidence.strip(), raw_reason.strip()
    )
    apply_to_dataset = bool(value) and confidence in ('HIGH', 'MEDIUM')
    return {
        'field': field,
        'value': value,
        'confidence': confidence,
        'evidence': evidence,
        'reason': reason,
        'apply_to_dataset': apply_to_dataset,
        'guardrail_notes': notes,
    }


def validate_record_results(field_results):
    """field_results: dict field -> validate_field_result(...) output.
    Devuelve (applied, suggested): qué va a enriched_dataset y qué va a suggested_values."""
    applied = {}
    suggested = {}
    for field, result in field_results.items():
        if result['apply_to_dataset']:
            applied[field] = result
        else:
            suggested[field] = result
    return applied, suggested
