"""
decision_log/logger.py — Serialize and persist RunResult to JSON.

Each run produces a file at:
    {log_dir}/{YYYY-MM-DD}/{prospect_slug}_{HH-MM-SS}.json

The JSON contains the full trace — every module's key outputs —
so that runs can be analyzed offline without rerunning the pipeline.
"""
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..schemas.evidence import EvidenceType
from ..schemas.run_result import RunResult


def log(result: RunResult, log_dir: Path) -> Path:
    """
    Serialize RunResult to JSON and write to log_dir.
    Returns the path of the created file.
    """
    now = datetime.now(tz=timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M-%S")
    slug = _slugify(result.prospect_name) or "unknown"

    day_dir = log_dir / date_str
    day_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{slug}_{time_str}.json"
    path = day_dir / filename

    payload = _serialize(result, now)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# ── Serialization ─────────────────────────────────────────────────────────────

def _serialize(result: RunResult, ts: datetime) -> dict[str, Any]:
    return {
        "run_id": str(uuid.uuid4()),
        "timestamp": ts.isoformat(),
        "prospect": result.prospect_name,
        "approved": result.approved,
        "blocked": result.blocked,
        "block_reason": result.block_reason,
        "action": result.action,
        "final_message": result.final_message,

        "trace": {
            "analysis": _analysis(result),
            "evidence": _evidence(result),
            "classification": _classification(result),
            "decision": _decision(result),
            "context_summary": _context_summary(result),
            "draft": result.draft,
            "review": _review(result),
        },
    }


def _analysis(r: RunResult) -> dict:
    a = r.analysis
    return {
        "stage": a.stage.value,
        "engagement": a.engagement.value,
        "sector": a.sector,
        "seniority": a.seniority.value,
        "is_decision_maker": a.is_decision_maker,
        "dossier_sent": a.dossier_sent,
        "responded_to_dossier": a.responded_to_dossier,
        "temperature": a.temperature.value,
        "last_prospect_message": a.last_prospect_message[:200] if a.last_prospect_message else None,
        "days_since_dossier": a.days_since_dossier,
    }


def _evidence(r: RunResult) -> dict:
    ev = r.evidence
    # Find the opening evidence object from its id
    opening = None
    if ev.opening_evidence_id:
        opening = next(
            (e for e in ev.all_evidence if e.id == ev.opening_evidence_id), None
        )
    return {
        "blocked": ev.blocked,
        "block_reason": ev.block_reason,
        "opening_evidence": {
            "claim": opening.claim,
            "type": opening.type.value,
            "exact_quote": opening.exact_quote,
        } if opening else None,
        "total_real": sum(1 for e in ev.all_evidence if e.type == EvidenceType.REAL),
        "total_inferred": sum(1 for e in ev.all_evidence if e.type == EvidenceType.INFERRED),
    }


def _classification(r: RunResult) -> dict:
    return {
        "action": r.action_cl.action.value,
        "action_reason": r.action_cl.reason,
        "strategy": r.strategy_cl.strategy.value,
        "strategy_reason": r.strategy_cl.reason,
    }


def _decision(r: RunResult) -> dict:
    d = r.decision
    return {
        "blocked": d.blocked,
        "block_reason": d.block_reason,
        "unique_objective": d.unique_objective,
        "mention_hint": d.mention_hint,
        "mention_dossier": d.mention_dossier,
        "propose_meeting": d.propose_meeting,
        "conversation_mode": d.conversation_mode.value,
        "rotation_applied": d.rotation_applied,
        "new_angle": d.new_angle,
        "personal_win": d.personal_win,
        "reference_client": d.reference_client,
    }


def _context_summary(r: RunResult) -> dict | None:
    if r.context is None:
        return None
    c = r.context
    return {
        "message_type": c.message_type,
        "tone": c.tone,
        "objective": c.objective,
        "allowed_topics_count": len(c.allowed_topics),
        "forbidden_topics_count": len(c.forbidden_topics),
        "allowed_claims_count": len(c.allowed_claims),
        "forbidden_claims_count": len(c.forbidden_claims),
        "bubbles": [{"id": b.id, "objective": b.objective} for b in c.bubbles],
    }


def _review(r: RunResult) -> dict | None:
    if r.review is None:
        return None
    rv = r.review
    return {
        "approved": rv.approved,
        "score": rv.score,
        "violations": [
            {
                "rule": v.rule,
                "description": v.description,
                "detected_fragment": v.detected_fragment,
            }
            for v in rv.violations
        ],
    }


def _slugify(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')[:40]
