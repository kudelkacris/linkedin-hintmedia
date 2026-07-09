"""
run.py — CRE pipeline entry point.

This is the only public interface. Everything else is internal.

Usage:
    from commercial_reasoning_engine.run import run
    from commercial_reasoning_engine.llm.claude_adapter import ClaudeAdapter

    result = run(conversation, adapter=ClaudeAdapter(), debug=True)
    if result.approved:
        print(result.final_message)

Pipeline:
    ConversationInput
        → analyzer          (parse + analyze)
        → evidence_engine   (tag + validate evidence)
        → classifier        (action + strategy)
        → strategy_builder  (one commercial decision)
        → context_builder   (minimal LLM context)
        → LLM adapter       (draft text)
        → reviewer          (blocklist + perspective + evidence)
        → RunResult

Early exits (blocked=True, final_message=None):
    - evidence blocked (no REAL evidence)
    - action == WAIT or NONE
    - decision blocked (strategy_builder rejected)
    - reviewer rejected (approved=False stays in RunResult but no final_message)
"""
import sys
from pathlib import Path
from typing import Optional

from .schemas.conversation import ConversationInput
from .schemas.classification import Action
from .schemas.run_result import RunResult
from .llm.adapter import LLMAdapter

from .analyzer import analyze
from .evidence_engine import run as evidence_run
from .classifier import classify_action, classify_strategy
from .strategy import build as strategy_build
from .context_builder import build as context_build
from .reviewer import review
from . import decision_log


_WAIT_ACTIONS = {Action.WAIT, Action.NONE}


def run(
    conversation: ConversationInput,
    adapter: LLMAdapter,
    prospect_data: Optional[dict] = None,
    debug: bool = False,
    log_dir: Optional[Path] = None,
) -> RunResult:
    """
    Run the full CRE pipeline.

    Args:
        conversation:   parsed conversation from LinkedIn
        adapter:        LLM backend (ClaudeAdapter or test double)
        prospect_data:  optional dict with known facts (stage, sector, seniority)
                        that override or supplement what the parser finds
        debug:          print a one-page trace to stdout
        log_dir:        if set, write decision JSON to this directory

    Returns:
        RunResult with full trace. Check result.approved and result.final_message.
    """
    prospect_name = conversation.prospect_name

    # ── Step 1: Analyze ────────────────────────────────────────────────────────
    analysis = analyze(conversation, prospect_data)

    # ── Step 2: Evidence Engine ────────────────────────────────────────────────
    evidence = evidence_run(analysis)

    if evidence.blocked:
        result = _blocked_result(
            reason=evidence.block_reason or "evidence blocked",
            action="NONE",
            prospect_name=prospect_name,
            analysis=analysis,
            evidence=evidence,
        )
        _finalize(result, debug, log_dir)
        return result

    # ── Step 3: Classify ───────────────────────────────────────────────────────
    action_cl = classify_action(analysis, evidence)
    strategy_cl = classify_strategy(analysis, action_cl)

    if action_cl.action in _WAIT_ACTIONS:
        result = _blocked_result(
            reason=f"action={action_cl.action.value} — {action_cl.reason}",
            action=action_cl.action.value,
            prospect_name=prospect_name,
            analysis=analysis,
            evidence=evidence,
            action_cl=action_cl,
            strategy_cl=strategy_cl,
        )
        _finalize(result, debug, log_dir)
        return result

    # ── Step 4: Strategy ───────────────────────────────────────────────────────
    decision = strategy_build(analysis, evidence, action_cl, strategy_cl)

    if decision.blocked:
        result = _blocked_result(
            reason=decision.block_reason or "strategy blocked",
            action=action_cl.action.value,
            prospect_name=prospect_name,
            analysis=analysis,
            evidence=evidence,
            action_cl=action_cl,
            strategy_cl=strategy_cl,
            decision=decision,
        )
        _finalize(result, debug, log_dir)
        return result

    # ── Step 5: Context Builder ────────────────────────────────────────────────
    context = context_build(
        analysis, evidence, action_cl, strategy_cl, decision, prospect_name
    )

    # ── Step 6: LLM Adapter ────────────────────────────────────────────────────
    draft = adapter.draft(context)

    # ── Step 7: Reviewer ──────────────────────────────────────────────────────
    review_result = review(draft, context)

    result = RunResult(
        approved=review_result.approved,
        final_message=review_result.final_message,
        blocked=False,
        block_reason=None,
        action=action_cl.action.value,
        prospect_name=prospect_name,
        analysis=analysis,
        evidence=evidence,
        action_cl=action_cl,
        strategy_cl=strategy_cl,
        decision=decision,
        context=context,
        draft=draft,
        review=review_result,
    )

    _finalize(result, debug, log_dir)
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

def _blocked_result(
    reason: str,
    action: str,
    prospect_name: str,
    analysis,
    evidence,
    action_cl=None,
    strategy_cl=None,
    decision=None,
) -> RunResult:
    from .schemas.classification import (
        ActionClassification, Action,
        StrategyClassification, StrategyType,
    )
    from .schemas.strategy import StrategyDecision, CTADecision, ConversationMode

    if action_cl is None:
        action_cl = ActionClassification(action=Action.NONE, reason=reason)
    if strategy_cl is None:
        strategy_cl = StrategyClassification(
            strategy=StrategyType.EXPLORATORIA, reason=reason
        )
    if decision is None:
        decision = StrategyDecision(
            unique_objective="blocked",
            opening_angle=None,
            opening_angle_source="REAL",
            mention_hint=False,
            mention_dossier=False,
            propose_meeting=False,
            cta=CTADecision(allowed=False),
            personal_win=None,
            reference_client=None,
            rotation_applied=False,
            previous_angle=None,
            new_angle=None,
            conversation_mode=ConversationMode.NORMAL,
            blocked=True,
            block_reason=reason,
        )

    return RunResult(
        approved=False,
        final_message=None,
        blocked=True,
        block_reason=reason,
        action=action,
        prospect_name=prospect_name,
        analysis=analysis,
        evidence=evidence,
        action_cl=action_cl,
        strategy_cl=strategy_cl,
        decision=decision,
        context=None,
        draft=None,
        review=None,
    )


def _finalize(result: RunResult, debug: bool, log_dir: Optional[Path]) -> None:
    if debug:
        _print_debug(result)
    if log_dir:
        decision_log.log(result, log_dir)


def _print_debug(result: RunResult) -> None:
    a = result.analysis
    lines = [
        "",
        "═" * 50,
        "  CRE DEBUG TRACE",
        "═" * 50,
        f"  Prospecto   : {result.prospect_name}",
        f"  Stage       : {a.stage.value}",
        f"  Engagement  : {a.engagement.value}",
        f"  Seniority   : {a.seniority.value}",
        f"  Sector      : {a.sector}",
        "─" * 50,
        f"  Action      : {result.action_cl.action.value}",
        f"  Strategy    : {result.strategy_cl.strategy.value}",
        f"  Blocked     : {result.blocked}",
    ]

    if result.blocked:
        lines.append(f"  Block reason: {result.block_reason}")
    else:
        d = result.decision
        lines += [
            "─" * 50,
            f"  Objective   : {d.unique_objective}",
            f"  Mention Hint: {d.mention_hint}",
            f"  Mention Dos : {d.mention_dossier}",
            f"  Meeting     : {d.propose_meeting}",
            f"  Conv. Mode  : {d.conversation_mode.value}",
            f"  Rotation    : {d.rotation_applied}",
        ]
        if result.review:
            rv = result.review
            lines += [
                "─" * 50,
                f"  Reviewer    : {'PASS' if rv.approved else 'FAIL'}",
                f"  Score       : {rv.score}",
            ]
            for v in rv.violations:
                lines.append(f"  ✗ [{v.rule}] {v.description[:60]}")

    lines += ["═" * 50, ""]
    print("\n".join(lines), file=sys.stderr)
