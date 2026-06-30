"""
conversation_engine.py — Fase 2b del HIE.

Analiza el texto de las conversaciones reales para encontrar señales
lingüísticas que predicen conversión. Sin API. Puro regex + frecuencias.

Fuentes:
  - dataset_builder/outputs/dataset.json (labels: DOSSIER_ENVIADO, ENGAGEMENT_LEVEL)
  - conversaciones/*.md (texto real de respuestas del prospecto)

Pregunta central:
  ¿Qué dice el prospecto en su respuesta al MSG1 cuando luego acepta el dossier
  vs cuando no lo acepta?
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date

_HIE_DIR = os.path.dirname(os.path.abspath(__file__))
_DS_DIR  = os.path.join(os.path.dirname(_HIE_DIR), 'dataset_builder')
sys.path.insert(0, _HIE_DIR)
sys.path.insert(0, _DS_DIR)

import config as hie_config
import extractors

# Alias para claridad
config = hie_config
CONV_DIR    = os.path.join(os.path.dirname(_HIE_DIR), 'conversaciones')


# ── Helpers ───────────────────────────────────────────────────────────────────

def pct(n, total):
    return round(100 * n / total, 1) if total else 0.0


def load_dataset():
    with open(config.DATASET_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_raw_responses(dataset):
    """
    Para cada registro del dataset que tiene respuesta, lee el .md original
    y extrae el texto real de lo que dijo el prospecto.
    """
    conv_dir = CONV_DIR
    enriched = []

    for record in dataset:
        if record.get('RESPONDIO_MSG1') != 'SI':
            continue

        fuente = record.get('FUENTE_ARCHIVO', '')
        path = os.path.join(conv_dir, fuente)
        if not os.path.exists(path):
            continue

        raw = extractors.parse_file(path)
        respuesta_text = raw.get('respuesta_msg1_text', '').strip()
        todas_respuestas = raw.get('all_respuestas', [])

        dossier_val = record.get('DOSSIER_ENVIADO', 'NO')

        enriched.append({
            'prospecto': record.get('PROSPECTO', ''),
            'sector': record.get('SECTOR', ''),
            'seniority': record.get('NIVEL_SENIORITY', ''),
            'variante': record.get('VARIANTE_MSG1', ''),
            'engagement': record.get('ENGAGEMENT_LEVEL', ''),
            'objecion': record.get('OBJECION_PRINCIPAL', ''),
            'dossier': dossier_val,
            'resultado': record.get('RESULTADO_FINAL', ''),
            'respuesta_msg1': respuesta_text,
            'todas_respuestas': todas_respuestas,
            'respuesta_combinada': ' '.join(todas_respuestas),
            'msg1_text': record.get('MSG1') or '',
        })

    return enriched


# ── Análisis de señales lingüísticas ─────────────────────────────────────────

STOPWORDS = {
    'de', 'la', 'el', 'en', 'y', 'a', 'que', 'es', 'se', 'un', 'una',
    'los', 'las', 'con', 'por', 'para', 'del', 'al', 'lo', 'como', 'más',
    'pero', 'su', 'me', 'si', 'te', 'ya', 'mi', 'está', 'le', 'no',
    'muy', 'bien', 'hay', 'ser', 'han', 'son', 'fue', 'era', 'this',
    'the', 'and', 'for', 'are', 'that', 'have', 'it', 'with', 'to',
    'of', 'in', 'is', 'you', 'not', 'we', 'our', 'has',
}

def tokenize(text):
    words = re.findall(r'\b[a-záéíóúüñA-ZÁÉÍÓÚÜÑA-Za-z]{3,}\b', text.lower())
    return [w for w in words if w not in STOPWORDS]


def analyze_signals(records):
    """
    Compara frecuencias de palabras en respuestas de prospectos que
    convirtieron (dossier=SI) vs los que no convirtieron (dossier=NO).
    """
    conv   = [r for r in records if r.get('dossier', 'NO') == 'SI' and r['respuesta_msg1']]
    no_conv = [r for r in records if r.get('dossier', 'NO') == 'NO' and r['respuesta_msg1']]

    words_conv    = Counter()
    words_no_conv = Counter()

    for r in conv:
        words_conv.update(tokenize(r['respuesta_combinada']))
    for r in no_conv:
        words_no_conv.update(tokenize(r['respuesta_combinada']))

    n_conv    = len(conv)
    n_no_conv = len(no_conv)

    # Frecuencia relativa: palabras que aparecen más en convertidos
    signals_positive = []
    signals_negative = []
    all_words = set(words_conv.keys()) | set(words_no_conv.keys())

    for word in all_words:
        freq_conv    = words_conv.get(word, 0) / n_conv if n_conv else 0
        freq_no_conv = words_no_conv.get(word, 0) / n_no_conv if n_no_conv else 0

        n_apariciones = words_conv.get(word, 0) + words_no_conv.get(word, 0)
        if n_apariciones < 3:
            continue

        ratio = freq_conv / (freq_no_conv + 0.001)
        diff  = freq_conv - freq_no_conv

        if ratio >= 1.5 and diff >= 0.05 and words_conv.get(word, 0) >= 2:
            signals_positive.append({
                'palabra': word,
                'freq_conv': round(freq_conv * 100, 1),
                'freq_no_conv': round(freq_no_conv * 100, 1),
                'ratio': round(ratio, 2),
                'n_conv': words_conv.get(word, 0),
                'n_no_conv': words_no_conv.get(word, 0),
            })

        if ratio <= 0.6 and freq_no_conv - freq_conv >= 0.05 and words_no_conv.get(word, 0) >= 2:
            signals_negative.append({
                'palabra': word,
                'freq_conv': round(freq_conv * 100, 1),
                'freq_no_conv': round(freq_no_conv * 100, 1),
                'ratio': round(ratio, 2),
                'n_conv': words_conv.get(word, 0),
                'n_no_conv': words_no_conv.get(word, 0),
            })

    signals_positive.sort(key=lambda x: -x['ratio'])
    signals_negative.sort(key=lambda x: x['ratio'])

    return {
        'n_conv': n_conv,
        'n_no_conv': n_no_conv,
        'signals_positive': signals_positive[:20],
        'signals_negative': signals_negative[:20],
    }


def analyze_length(records):
    """Longitud de respuesta como predictor de conversión."""
    conv    = [r for r in records if r.get('dossier', 'NO') == 'SI' and r['respuesta_msg1']]
    no_conv = [r for r in records if r.get('dossier', 'NO') == 'NO' and r['respuesta_msg1']]

    def avg_len(recs):
        lens = [len(r['respuesta_combinada']) for r in recs if r['respuesta_combinada']]
        return round(sum(lens) / len(lens)) if lens else 0

    def has_question_pct(recs):
        n = len(recs)
        if not n: return 0
        q = sum(1 for r in recs if '?' in r['respuesta_combinada'])
        return pct(q, n)

    def has_emoji_pct(recs):
        n = len(recs)
        if not n: return 0
        e = sum(1 for r in recs if re.search(r'[\U0001F300-\U0001FAFF]', r['respuesta_combinada']))
        return pct(e, n)

    return {
        'conv_avg_chars': avg_len(conv),
        'no_conv_avg_chars': avg_len(no_conv),
        'conv_question_pct': has_question_pct(conv),
        'no_conv_question_pct': has_question_pct(no_conv),
        'conv_emoji_pct': has_emoji_pct(conv),
        'no_conv_emoji_pct': has_emoji_pct(no_conv),
        'n_conv': len(conv),
        'n_no_conv': len(no_conv),
    }


def analyze_msg1_patterns(records):
    """
    Qué patrones en NUESTRO MSG1 se asocian con mayor conversión.
    Analiza longitud y palabras en el texto que enviamos.
    """
    conv    = [r for r in records if r.get('dossier', 'NO') == 'SI' and r['msg1_text']]
    no_conv = [r for r in records if r.get('dossier', 'NO') == 'NO' and r['msg1_text']]

    def avg_len(recs):
        lens = [len(r['msg1_text']) for r in recs if r['msg1_text']]
        return round(sum(lens) / len(lens)) if lens else 0

    words_conv    = Counter()
    words_no_conv = Counter()
    for r in conv:
        words_conv.update(tokenize(r['msg1_text']))
    for r in no_conv:
        words_no_conv.update(tokenize(r['msg1_text']))

    return {
        'conv_avg_msg1_chars': avg_len(conv),
        'no_conv_avg_msg1_chars': avg_len(no_conv),
        'n_conv': len(conv),
        'n_no_conv': len(no_conv),
    }


def analyze_engagement_prediction(records):
    """ENGAGEMENT_LEVEL como predictor de conversión."""
    result = {}
    for eng in ['HIGH', 'MEDIUM', 'LOW', 'N/A']:
        subset = [r for r in records if r['engagement'] == eng]
        if not subset:
            continue
        conv = sum(1 for r in subset if r.get('dossier', 'NO') == 'SI')
        result[eng] = {
            'n': len(subset),
            'dossier_pct': pct(conv, len(subset)),
            'dossier_n': conv,
        }
    return result


# ── Run principal ─────────────────────────────────────────────────────────────

def run():
    today = str(date.today())

    dataset = load_dataset()
    records = load_raw_responses(dataset)

    n_con_respuesta = len(records)
    n_conv    = sum(1 for r in records if r.get('dossier', 'NO') == 'SI')
    n_no_conv = sum(1 for r in records if r.get('dossier', 'NO') == 'NO')

    signals   = analyze_signals(records)
    lengths   = analyze_length(records)
    # Adaptar dataset al formato que espera analyze_msg1_patterns
    dataset_adapted = [{'msg1_text': r.get('MSG1') or '', 'dossier': r.get('DOSSIER_ENVIADO','NO')} for r in dataset]
    msg1_pat  = analyze_msg1_patterns(dataset_adapted)
    eng_pred  = analyze_engagement_prediction(records)

    result = {
        'metadata': {
            'generado': today,
            'n_total_con_respuesta': n_con_respuesta,
            'n_convertidos': n_conv,
            'n_no_convertidos': n_no_conv,
            'version': 1,
        },
        'señales_en_respuesta_prospecto': signals,
        'longitud_como_predictor': lengths,
        'msg1_patterns': msg1_pat,
        'engagement_como_predictor': eng_pred,
    }

    # Guardar en KB
    os.makedirs(config.KB_DIR, exist_ok=True)
    signals_path = config.KB_SIGNALS
    with open(signals_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result, signals_path
