#!/usr/bin/env python3
"""
Construye outputs/semantic_audit_sample.csv: muestra aleatoria de 10 HIGH + 10 MEDIUM + 10 LOW
de ENGAGEMENT, sacada de semantic_enrichment.csv. NO corre el pipeline de nuevo.

A diferencia de build_audit_sample.py (que auditaba "¿la IA inventó o no?"), esta auditoría
pregunta otra cosa: "¿la etiqueta de intención/engagement tiene sentido con el texto real, o el
modelo la infló/desinfló?" — calibración, no solo invención.
"""
import csv
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

SAMPLE_PER_BUCKET = 10
RANDOM_SEED = 42


def load_semantic_rows():
    path = os.path.join(config.OUTPUT_DIR, 'semantic_enrichment.csv')
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def main():
    random.seed(RANDOM_SEED)
    rows = load_semantic_rows()

    pools = {b: [r for r in rows if r['ENGAGEMENT'] == b] for b in ('HIGH', 'MEDIUM', 'LOW')}

    sample = []
    shortfalls = {}
    for bucket, pool in pools.items():
        n = min(SAMPLE_PER_BUCKET, len(pool))
        if n < SAMPLE_PER_BUCKET:
            shortfalls[bucket] = f'pool tiene {len(pool)}, se pidieron {SAMPLE_PER_BUCKET}'
        sample.extend(random.sample(pool, n))

    cols = ['ID_CONVERSACION', 'PROSPECTO', 'CRM_pipeline_status', 'ENGAGEMENT', 'INTEREST_LEVEL',
            'RESPONSE_QUALITY', 'OBJECTIONS', 'KEY_SIGNALS', 'SUMMARY', 'CONF_INTENT', 'CONF_SIGNALS',
            'SENTIDO_CON_TEXTO', 'OBJECION_BIEN_IDENTIFICADA', 'ENGAGEMENT_CALIBRADO', 'OBSERVACIONES']

    out_rows = []
    for r in sample:
        out_rows.append({
            'ID_CONVERSACION': r['ID_CONVERSACION'],
            'PROSPECTO': r['PROSPECTO'],
            'CRM_pipeline_status': r['CRM_pipeline_status'],
            'ENGAGEMENT': r['ENGAGEMENT'],
            'INTEREST_LEVEL': r['INTEREST_LEVEL'],
            'RESPONSE_QUALITY': r['RESPONSE_QUALITY'],
            'OBJECTIONS': r['OBJECTIONS'],
            'KEY_SIGNALS': r['KEY_SIGNALS'],
            'SUMMARY': r['SUMMARY'],
            'CONF_INTENT': r['CONF_INTENT'],
            'CONF_SIGNALS': r['CONF_SIGNALS'],
            'SENTIDO_CON_TEXTO': '',          # SI/NO — ¿la etiqueta de intención tiene sentido leyendo el texto real?
            'OBJECION_BIEN_IDENTIFICADA': '',  # SI/NO/NA — NA si OBJECTIONS viene vacío
            'ENGAGEMENT_CALIBRADO': '',        # OK / INFLADO / DEFLACTADO
            'OBSERVACIONES': '',
        })

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(config.OUTPUT_DIR, 'semantic_audit_sample.csv')
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out_rows)

    print(f'Muestra escrita: {out_path} ({len(out_rows)} filas)')
    if shortfalls:
        print('ADVERTENCIA — pools insuficientes para 10/10/10:')
        for bucket, msg in shortfalls.items():
            print(f'  {bucket}: {msg}')
    print('\nCómo auditar cada fila:')
    print('  SENTIDO_CON_TEXTO: leé KEY_SIGNALS + SUMMARY. ¿INTEREST_LEVEL/ENGAGEMENT tiene sentido? SI/NO.')
    print('  OBJECION_BIEN_IDENTIFICADA: ¿la objeción listada es real, o el modelo vio un fantasma? SI/NO/NA.')
    print('  ENGAGEMENT_CALIBRADO: OK si coincide con tu lectura. INFLADO si el modelo puso más entusiasmo')
    print('  del que hay evidencia. DEFLACTADO si subestimó una señal real de interés.')


if __name__ == '__main__':
    main()
