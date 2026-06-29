"""
Construcción de prompts para el enrichment. Una sola llamada por conversación,
pidiendo SOLO los campos que están vacíos en esa fila. Formato de salida plano
(lección aprendida del generador principal: markdown/negrita rompe el parser).
"""
import config

SYSTEM = """Sos un analista de datos que completa campos faltantes de un dataset de prospección B2B.

PRINCIPIO CENTRAL — NUNCA INVENTAR:
Si la evidencia en el perfil o la conversación no alcanza para inferir un campo con razonable
certeza, DEJAR ESE CAMPO VACÍO. Es preferible un campo vacío a un campo inventado. No hay
penalización por dejar vacío. Sí hay penalización (la respuesta se descarta) por inventar.

REGLAS DURAS:
- NO inferir SECTOR si la empresa/cargo no lo deja explícito o casi explícito (ej: "VP Sales Mining" → Minería está permitido; "trabaja en consultoría" → "Finanzas" NO está permitido, eso es una invención).
- NO inferir NIVEL_SENIORITY ni TIPO_PERFIL sin evidencia textual del cargo o del trato en la conversación.
- NO asumir poder de decisión sin evidencia.
- NO asumir interés comercial sin evidencia (silencio total no es HIGH engagement).
- Para cada campo que completes, tenés que poder citar la evidencia textual concreta que lo sostiene.

FORMATO DE SALIDA — usar EXACTAMENTE este formato, una línea por clave, sin markdown, sin negrita, sin headers:

Para cada campo de la lista de "CAMPOS A COMPLETAR" que te paso, devolver 4 líneas:
<CAMPO>: <valor o vacío si no hay evidencia>
<CAMPO>_CONFIDENCE: HIGH | MEDIUM | LOW (LOW si el valor quedó vacío o es una corazonada débil)
<CAMPO>_EVIDENCE: cita textual corta o lista separada por " | " de las señales usadas (vacío si no hay)
<CAMPO>_REASON: explicación en máximo 50 palabras (vacío si el valor quedó vacío)

No agregues texto antes, entre, o después de estos bloques. No uses ningún campo que no esté en la lista pedida."""


def build_user_prompt(record, raw_conversation_text, fields_to_fill):
    fields_block = '\n'.join(
        f'- {f}' + (f' (valor DEBE ser exactamente uno de: {", ".join(sorted(config.VALID_VALUES[f]))} — '
                     f'si ninguno aplica con evidencia suficiente, dejar vacío, NO inventar otra categoría)'
                     if f in config.VALID_VALUES else ' (texto libre)')
        for f in fields_to_fill
    )
    return f"""PERFIL Y CONVERSACIÓN COMPLETA (única fuente de evidencia permitida, no usar nada externo):
{raw_conversation_text}

DATOS PARCIALES YA EXISTENTES EN EL DATASET (para contexto, no los repitas en la salida):
CARGO: {record.get('CARGO','')}
EMPRESA: {record.get('EMPRESA','')}
PAIS: {record.get('PAIS','')}
SECTOR_ACTUAL: {record.get('SECTOR','')}
ESTADO_ACTUAL: {record.get('ESTADO_ACTUAL','')}
RESULTADO_FINAL: {record.get('RESULTADO_FINAL','')}
OBJECION_PRINCIPAL_ACTUAL: {record.get('OBJECION_PRINCIPAL','')}

CAMPOS A COMPLETAR (solo estos, en este orden, 4 líneas cada uno):
{fields_block}

Recordá: si no hay evidencia suficiente para un campo, dejá el valor vacío y CONFIDENCE en LOW."""
