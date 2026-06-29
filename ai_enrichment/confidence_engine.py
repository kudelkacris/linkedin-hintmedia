"""
Guardrails sobre la confianza que el modelo se auto-asigna. El modelo puede equivocarse
diciendo HIGH sin evidencia real — este módulo aplica reglas estructurales (no semánticas)
para detectar esa contradicción y forzar una confianza más baja.
"""
import config

DOWNGRADE = {'HIGH': 'MEDIUM', 'MEDIUM': 'LOW', 'LOW': 'LOW'}


def adjust_confidence(field, value, confidence, evidence, reason):
    """
    Devuelve (confidence_ajustada, motivo_ajuste o None).
    Reglas:
      1. Si no hay valor, la confianza no puede ser HIGH/MEDIUM -> forzar LOW y vaciar evidencia/reason.
      2. Si hay valor pero la evidencia está vacía, downgrade un escalón (HIGH->MEDIUM, MEDIUM->LOW).
      3. Si el campo tiene enum válido y el valor no pertenece a ese enum, descartar valor entero (LOW, vacío).
      4. Si reason supera el límite de palabras, no descalifica el dato pero se recorta.
    """
    notes = []

    if confidence not in config.CONFIDENCE_LEVELS:
        confidence = 'LOW'
        notes.append('confidence fuera de enum, forzado a LOW')

    if field in config.VALID_VALUES and value:
        if value.upper() not in config.VALID_VALUES[field]:
            notes.append(f'valor "{value}" no está en el enum válido de {field}, descartado')
            value = ''
            confidence = 'LOW'
        elif value != value.upper():
            value = value.upper()
            notes.append('valor normalizado a mayúsculas (enum)')

    if not value:
        if confidence != 'LOW':
            notes.append('valor vacío con confidence != LOW, forzado a LOW')
        confidence = 'LOW'
        evidence = ''
        reason = ''
    elif not evidence.strip():
        downgraded = DOWNGRADE[confidence]
        if downgraded != confidence:
            notes.append(f'evidencia vacía, downgrade {confidence}->{downgraded}')
        confidence = downgraded

    if reason:
        words = reason.split()
        if len(words) > config.MAX_REASON_WORDS:
            reason = ' '.join(words[:config.MAX_REASON_WORDS]) + '…'
            notes.append('reason recortado a 50 palabras')

    if field in ('MOTIVO_EXITO', 'MOTIVO_FRACASO') and value:
        words = value.split()
        if len(words) > config.MAX_MOTIVO_WORDS:
            value = ' '.join(words[:config.MAX_MOTIVO_WORDS]) + '…'
            notes.append('valor de motivo recortado')

    return value, confidence, evidence, reason, notes
