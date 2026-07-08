# Roadmap de HITOS — Commercial Reasoning Engine

Cada hito requiere aprobación explícita antes de iniciar el siguiente.

---

## HITO 1 — Schemas + Config
**Estado:** COMPLETADO
**Módulos:** `schemas/`, `config/`
**Qué hay:** Todos los contratos de datos + conocimiento comercial como JSON
**Test:** `python -c "from commercial_reasoning_engine.schemas import *; print('OK')`

---

## HITO 2 — Parser + Analyzer + Dataset Reader
**Estado:** pendiente aprobación HITO 1
**Módulos:** `analyzer/parser.py`, `analyzer/analyzer.py`, `dataset/reader.py`
**Input:** texto crudo pegado
**Output:** `ConversationInput` → `AnalysisResult`
**Testeable solo:** sí, no requiere LLM ni internet

---

## HITO 3 — Evidence Engine
**Estado:** pendiente
**Módulos:** `evidence_engine/tagger.py`, `evidence_engine/validator.py`, `evidence_engine/engine.py`
**Input:** `ConversationInput` + `AnalysisResult`
**Output:** `EvidenceInventory`
**Test clave:** con solo sector como fuente → blocked=True, opening_available=False

---

## HITO 4 — Classifiers
**Estado:** pendiente
**Módulos:** `classifier/action_classifier.py`, `classifier/strategy_classifier.py`
**Input:** `AnalysisResult`
**Output:** `ActionClassification`, `StrategyClassification`
**Depende de:** HITO 1

---

## HITO 5 — Strategy Layer
**Estado:** pendiente
**Módulos:** `strategy/strategy_builder.py`, `strategy/rotation_engine.py`, `strategy/win_selector.py`
**Input:** `AnalysisResult` + `EvidenceInventory` + clasificaciones
**Output:** `StrategyDecision`
**Regla clave:** solo consume evidence.usable == True

---

## HITO 6 — Context Builder
**Estado:** pendiente
**Módulos:** `context_builder/builder.py`
**Input:** `StrategyDecision` + `EvidenceInventory`
**Output:** `LLMContext` con allowed_topics / forbidden_topics
**Regla clave:** LLM nunca ve conversación completa, solo este JSON

---

## HITO 7 — LLM Adapter + Prompts
**Estado:** pendiente
**Módulos:** `llm/adapter.py`, `llm/claude_adapter.py`, `llm/prompts/`
**Input:** `LLMContext` + tipo_mensaje
**Output:** string (único string en todo el pipeline)
**Regla clave:** adapter es interfaz abstracta — swap de modelo sin tocar nada más

---

## HITO 8 — Reviewer
**Estado:** pendiente
**Módulos:** `reviewer/reviewer.py`, `reviewer/blocklist_checker.py`, `reviewer/perspective_checker.py`, `reviewer/evidence_checker.py`
**Input:** draft + `StrategyDecision` + `EvidenceInventory`
**Output:** `ReviewResult`
**Test clave:** draft con claim INFERRED → approved=False con violation "evidence_leak"

---

## HITO 9 — Decision Log + run.py + Integración
**Estado:** pendiente
**Módulos:** `decision_log/logger.py`, `decision_log/trace.py`, `run.py`
**Test clave:** corrida completa end-to-end genera mensaje + JSON en logs/decisions/
