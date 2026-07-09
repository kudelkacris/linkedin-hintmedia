# PROJECT_STATUS.md — Estado de Todos los Sistemas

Última actualización: 09/07/2026

---

## CRE — Commercial Reasoning Engine

**Estado: COMPLETO (v1.0)**
Ruta: `../commercial_reasoning_engine/`
Tests: 317/317 pasando
Pipeline: `run.py` → analyzer → evidence → classifier → strategy → context_builder → llm → reviewer
Principio: el LLM NO decide nada. El motor decide. El LLM solo redacta.
Pendiente: Beta — correr 100 conversaciones reales, comparar con output de Florencia.

---

## HIE — Hint Intelligence Engine

**Estado: ACTIVO**
Datos: 427 contactos analizados
Tasa dossier global: 25.1%
Mejor sector: Educación (35.7%, n=42)
Mejor seniority: Director (27.3%)
Mejor variante MSG1: Variante A (28.5% vs 19.4% Variante C)
Sectores a evitar: Retail (12.5%), Turismo (14.3%)
CEO en frío: 10% — no priorizar.

---

## Programa Web

**Estado: ACTIVO**
Archivos: `../index.html` + `../servidor.py`
Puerto: 3000
Funcionalidades: generación MSG1/MSG2/SEG1, copy-paste, historial visual, watcher .md→historial
Pendiente: SEG2, botón sync, backup automático.

---

## Viewer Cloudflare

**Estado: ACTIVO**
URL: historial.pages.dev
Repo: kudelkacris/linkedin-historial
Backend: Cloudflare KV (binding MAIL_KV) para checkbox mail enviado
Acceso: compartido con el jefe de Florencia.

---

## Analytics

**Estado: ACTIVO**
Archivo: `../analytics.html`
Contenido: métricas del funnel, costos API, conversión por stage.

---

## Watcher MD→Historial

**Estado: ACTIVO**
Implementado en servidor.py (watchdog).
Auto-sincroniza stages de .md a historial.json cuando se edita un archivo de conversación.
Regla: al guardar, actualizar historial.json directamente además del .md, no depender solo del watcher.

---

## Listas Sales Navigator

**Estado: ESPERANDO ACEPTACIONES**
TOIA 1.0: 10 personas conectadas el 08/07/26 (energía, Colombia/LATAM)
TOIA 1.2: 15 personas guardadas el 08/07/26 (energía/minería, LATAM, Director+VP+Gerente)
Cuando alguien acepte → generar MSG1 Variante A.
Clientes referencia energía: TGS, Transener.

---

## Funnel

| Stage | n | % del anterior |
|-------|---|----------------|
| Contactos totales | ~540 | — |
| MSG1 enviado | 256 | — |
| MSG2 enviado | 136 | 53% |
| Dossier enviado | 60 | 44% |
| SEG1 enviado | 72 | — |
| Reunión confirmada | 1 | 1.7% de dossiers |

**Cuello de botella crítico:** dossier → reunión.

---

## Roadmap

| Prioridad | Tarea | Estado |
|-----------|-------|--------|
| 1 | SEG2 en index.html | PENDIENTE |
| 2 | CRE Beta (5 conv reales) | PENDIENTE |
| 3 | Activar TOIA (aceptaciones MSG1) | ESPERANDO |
| 4 | dataset/reader.py (days_since) | PENDIENTE |
| 5 | docs/future_evolutions.md CRE | PENDIENTE |
