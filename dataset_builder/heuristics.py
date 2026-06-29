"""
Reglas de clasificación sobre el dict crudo que devuelve extractors.parse_file().
No usan IA. Cuando una regla no puede decidir, devuelve '' (vacío) y el campo
queda candidato a needs_ai_review si está en config.NEEDS_AI_FIELDS.
"""
import re
import config


def _match_any(text, patterns):
    t = (text or '').lower()
    return any(re.search(p, t, re.IGNORECASE) for p in patterns)


def _first_match(text, rules):
    """rules: lista de (label, [patterns]). Devuelve el primer label cuyo patrón matchea."""
    t = (text or '').lower()
    for label, patterns in rules:
        if any(re.search(p, t, re.IGNORECASE) for p in patterns):
            return label
    return ''


def detect_sector(empresa_text, cargo_text, full_text=''):
    """Infiere sector desde nombre de empresa + cargo. Busca en ese orden.
    Si no matchea, devuelve '' (NEEDS_AI para completar manualmente si hace falta)."""
    combined = ' '.join([empresa_text or '', cargo_text or '', full_text[:300] or '']).lower()
    return _first_match(combined, config.SECTOR_RULES)


def detect_seniority(cargo_text):
    return _first_match(cargo_text, config.SENIORITY_RULES) or 'OTHER'


def detect_profile_type(cargo_text, full_text):
    result = _first_match(cargo_text, config.PROFILE_TYPE_RULES)
    if result:
        return result
    # fallback: buscar señales en todo el texto
    result = _first_match(full_text, config.PROFILE_TYPE_RULES)
    return result  # puede quedar vacío -> NEEDS_AI


def detect_variante_msg1(msg1_text):
    """
    Variante A (la persona): suele arrancar con observación personal ("Me llamó la atención" sin
    'lo que vienen haciendo en [empresa]'). Variante C (el trabajo): contiene
    "revisando un poco lo que vienen haciendo en" / "estuve revisando" + nombre de empresa.
    """
    t = (msg1_text or '').lower()
    if not t:
        return ''
    if re.search(r'revisando (un poco )?lo que (ven[ií]s|vienen) haciendo', t) or re.search(r'estuve revisando', t):
        return 'C'
    if re.search(r'me llam[oó] la atenci[oó]n', t):
        return 'A'
    return ''


def detect_responded(text):
    return 'SI' if (text or '').strip() else 'NO'


def detect_pidio_dossier(respuesta_msg2_or_estado):
    """Patrones con \\b (límite de palabra) en ambos extremos — bug real encontrado: sin \\b,
    'env[ií]a(lo)?' matcheaba la palabra "enviado" (de "MSG2 enviado", presente en casi todos los
    Estado), generando falsos positivos masivos. Nunca usar substring matching sin anclar bordes
    de palabra cuando el texto de control (nuestros propios Estado) puede contener la raíz."""
    return 'SI' if _match_any(respuesta_msg2_or_estado, [
        r'\bdossier\b',
        r'\bmandar(lo|melo|me)?\b', r'\bm[aá]ndalo\b', r'\bm[aá]ndamelo\b',
        r'\bpasar(lo|melo|me)?\b', r'\bp[aá]salo\b', r'\bp[aá]samelo\b',
        r'\benviar(lo|melo|me)?\b', r'\benv[ií]a(lo|melo|me)?\b',
        r'\bs[ií],?\s*claro\b', r'\bme interesa\b',
    ]) else 'NO'


def detect_dossier_enviado(estado_raw, dossier_text, pidio_dossier='NO'):
    """pidio_dossier='SI' también cuenta como enviado: aceptar el dossier se trata como enviado,
    aunque el envío operativo (Estado: 'dossier por enviar') esté pendiente de nuestro lado."""
    return 'SI' if (_match_any(estado_raw, [r'dossier enviado', r'dossier confirmado', r'dossier por mandar.*aceptado'])
                     or bool((dossier_text or '').strip())
                     or pidio_dossier == 'SI') else 'NO'


def detect_seg_enviado(estado_raw, seg_text, tag):
    return 'SI' if (_match_any(estado_raw, [tag.lower()]) or bool((seg_text or '').strip())) else 'NO'


def detect_objecion(signal_text):
    """signal_text = SOLO respuestas del prospecto + Estado + Notas (NUNCA nuestros propios mensajes,
    que siempre proponen reunión/dossier y generarían falsos positivos)."""
    label = _first_match(signal_text, config.OBJECTION_RULES)
    return label or ('NONE' if _has_response_signal(signal_text) else '')


def _has_response_signal(signal_text):
    return bool((signal_text or '').strip())


def detect_engagement(record):
    """
    Prioridad 1: si el texto YA dice "engagement HIGH/MEDIUM/LOW" (muchos archivos lo anotan a mano).
    Prioridad 2: heurística por longitud + preguntas + elaboración en las respuestas del prospecto.
    """
    full = record['full_text']
    m = re.search(config.ENGAGEMENT_EXPLICIT_RE, full, re.IGNORECASE)
    if m:
        return m.group(1).upper()

    respuestas = record.get('all_respuestas', [])
    if not respuestas:
        return 'N/A'  # sin ninguna respuesta del prospecto -> no aplica, no es un hueco que IA pueda llenar

    total_len = sum(len(r) for r in respuestas)
    has_question = any('?' in r for r in respuestas)
    has_emoji = any(re.search(r'[\U0001F300-\U0001FAFF☀-➿]', r) for r in respuestas)
    n_msgs = len(respuestas)

    score = 0
    if total_len > 220:
        score += 2
    elif total_len > 90:
        score += 1
    if has_question:
        score += 1
    if has_emoji:
        score += 1
    if n_msgs >= 2:
        score += 1

    if score >= 4:
        return 'HIGH'
    if score >= 2:
        return 'MEDIUM'
    return 'LOW'


def detect_call_agendada(signal_text):
    """Solo cuenta si la SEÑAL viene del prospecto (respuesta/estado/notas), no de nuestro propio
    script (que siempre propone 'coordinamos 15 minutos' como CTA, sea o no aceptado)."""
    return 'SI' if _match_any(signal_text, config.CALL_KEYWORDS) else 'NO'


def detect_cliente_cerrado(signal_text):
    return 'SI' if _match_any(signal_text, config.CLIENT_KEYWORDS) else 'NO'


def detect_resultado_final(record, call_agendada, cliente_cerrado, dossier_enviado, seg1, seg2, respondio_msg1):
    if cliente_cerrado == 'SI':
        return 'CLIENTE'
    if call_agendada == 'SI':
        return 'REUNION'
    if seg1 == 'SI' or seg2 == 'SI':
        return 'SEGUIMIENTO'
    if dossier_enviado == 'SI':
        return 'DOSSIER'
    if respondio_msg1 == 'NO':
        return 'SIN_RESPUESTA'
    return 'SIN_RESPUESTA'


def detect_motivo(full_text, resultado_final):
    """Heurística simple para motivo_exito / motivo_fracaso. Texto libre corto sacado de Notas/Estado.
    Si no hay nada claro, queda vacío -> NEEDS_AI."""
    notas = record_notas = full_text
    rechazo_patterns = [r'rechaz[oó]', r'no interesad[oa]', r'ya no (est[áa]|trabaja)', r'no aplica',
                         r'no estamos buscando', r'no es el momento']
    exito_patterns = [r'engagement high', r'dio el mail', r'pregunt[oó] directo', r'call agendada',
                       r'cliente cerrado', r'firm[oó]']
    if resultado_final in ('CLIENTE', 'REUNION') and _match_any(notas, exito_patterns):
        m = re.search('|'.join(exito_patterns), notas, re.IGNORECASE)
        return m.group(0) if m else ''
    if resultado_final == 'SIN_RESPUESTA' and _match_any(notas, rechazo_patterns):
        m = re.search('|'.join(rechazo_patterns), notas, re.IGNORECASE)
        return m.group(0) if m else ''
    return ''


def classify_record(raw, conv_id):
    """Aplica todas las reglas heurísticas sobre un raw record de extractors.parse_file()."""
    full_text = raw['full_text']
    cargo = raw['cargo']
    # Señal real del prospecto: SUS respuestas + Estado + Notas. Nunca nuestros mensajes
    # (MSG1/MSG2/dossier/SEG), que siempre proponen CTA de reunión/dossier sea aceptado o no.
    signal_text = '\n'.join(raw.get('all_respuestas', [])) + '\n' + raw['estado_raw'] + '\n' + raw['notas_text']

    respondio_msg1 = detect_responded(raw['respuesta_msg1_text'])
    # PIDIO_DOSSIER se decide por la respuesta al CTA del dossier (que está en MSG2), no por la
    # respuesta al MSG1 — bug real encontrado en auditoría manual: Bernardo Guevara Morales respondió
    # literalmente "Sí, claro" a la oferta de dossier en MSG2, pero se evaluaba su respuesta a MSG1.
    pidio_dossier = detect_pidio_dossier(raw['respuesta_dossier_text'] + ' ' + raw['estado_raw'])
    # Regla de negocio (aclarada por el usuario): si el prospecto aceptó el dossier ("sí, claro",
    # "mándalo aquí o por mail"), se cuenta como dossier enviado aunque operativamente quede
    # pendiente de nuestro lado (Estado: "por enviar"). Aceptar = lo tratamos como enviado.
    dossier_enviado = detect_dossier_enviado(raw['estado_raw'], raw['dossier_text'], pidio_dossier)
    respondio_dossier = detect_responded(raw['respuesta_dossier_text'])
    seg1_enviado = detect_seg_enviado(raw['estado_raw'], raw['seg1_text'], 'seg1')
    seg2_enviado = detect_seg_enviado(raw['estado_raw'], raw['seg2_text'], 'seg2')
    call_agendada = detect_call_agendada(signal_text)
    cliente_cerrado = detect_cliente_cerrado(signal_text)
    objecion = detect_objecion(signal_text)
    engagement = detect_engagement(raw)
    seniority = detect_seniority(cargo)
    tipo_perfil = detect_profile_type(cargo, full_text)
    variante = detect_variante_msg1(raw['msg1_text'])
    sector = raw['sector'] or detect_sector(raw['empresa'], cargo, full_text)
    resultado_final = detect_resultado_final(
        raw, call_agendada, cliente_cerrado, dossier_enviado, seg1_enviado, seg2_enviado, respondio_msg1
    )
    motivo_exito = detect_motivo(signal_text, resultado_final) if resultado_final in ('CLIENTE', 'REUNION') else ''
    motivo_fracaso = detect_motivo(signal_text, resultado_final) if resultado_final == 'SIN_RESPUESTA' else ''

    record = {
        'ID_CONVERSACION': conv_id,
        'PROSPECTO': raw['nombre'],
        'EMPRESA': raw['empresa'],
        'PAIS': raw['pais'],
        'SECTOR': sector,
        'CARGO': raw['cargo'],
        'NIVEL_SENIORITY': seniority,
        'TIPO_PERFIL': tipo_perfil,
        'ESTADO_ACTUAL': raw['estado_raw'],
        'VARIANTE_MSG1': variante,
        'MSG1': raw['msg1_text'],
        'RESPONDIO_MSG1': respondio_msg1,
        'MSG2': raw['msg2_text'],
        'PIDIO_DOSSIER': pidio_dossier,
        'DOSSIER_ENVIADO': dossier_enviado,
        'RESPONDIO_DOSSIER': respondio_dossier,
        'SEG1_ENVIADO': seg1_enviado,
        'SEG2_ENVIADO': seg2_enviado,
        'OBJECION_PRINCIPAL': objecion,
        'ENGAGEMENT_LEVEL': engagement,
        'CALL_AGENDADA': call_agendada,
        'CLIENTE_CERRADO': cliente_cerrado,
        'RESULTADO_FINAL': resultado_final,
        'MOTIVO_EXITO': motivo_exito,
        'MOTIVO_FRACASO': motivo_fracaso,
        'OBSERVACIONES': raw['notas_text'],
        'FUENTE_ARCHIVO': raw['fuente_archivo'],
    }

    # MOTIVO_EXITO solo aplica si hubo conversión; MOTIVO_FRACASO solo si no hubo respuesta.
    # OBJECION_PRINCIPAL/ENGAGEMENT_LEVEL/TIPO_PERFIL siempre son relevantes.
    always_check = ['OBJECION_PRINCIPAL', 'ENGAGEMENT_LEVEL', 'TIPO_PERFIL']
    needs_ai = any(not record[f] for f in always_check)
    if resultado_final in ('CLIENTE', 'REUNION') and not record['MOTIVO_EXITO']:
        needs_ai = True
    if resultado_final == 'SIN_RESPUESTA' and not record['MOTIVO_FRACASO']:
        needs_ai = True
    record['NEEDS_AI'] = needs_ai
    return record
