"""
HITO 9 — Integration tests.

Tests the full CRE pipeline via run.run().
Uses ConcreteAdapter (test double) — no real LLM calls.
Uses tmp_path (pytest fixture) for decision_log file creation.
"""
import sys
import json
from io import StringIO
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from commercial_reasoning_engine.schemas.conversation import ConversationInput, Message
from commercial_reasoning_engine.schemas.run_result import RunResult
from commercial_reasoning_engine.llm.adapter import LLMAdapter
from commercial_reasoning_engine.run import run


# ── Test adapter ───────────────────────────────────────────────────────────────

class ConcreteAdapter(LLMAdapter):
    """Returns a clean draft that passes the reviewer."""
    DRAFT = (
        "Buenas Laura!\n"
        "Lo que describiste sobre el equipo tiene mucho sentido.\n"
        "Como lo resolvieron en contextos de alta presion?\n"
        "Trabajo con equipos de energia en Hint Media, con clientes como TGS.\n"
        "Te puedo mandar el dossier por aca si no es mucha molestia, "
        "o me indicarias a quien se lo puedo mandar."
    )

    def _call(self, prompt: str) -> str:
        return self.DRAFT


class FailingAdapter(LLMAdapter):
    """Returns a draft that triggers blocklist + perspective violations."""
    DRAFT = (
        "Buenas Laura!\n"
        "En Hint trabajamos con empresas como la tuya. "
        "Retomo mi mensaje anterior. Quedo atenta."
    )

    def _call(self, prompt: str) -> str:
        return self.DRAFT


ADAPTER = ConcreteAdapter()
FAILING_ADAPTER = FailingAdapter()


# ── ConversationInput factories ────────────────────────────────────────────────

def _msg2_conversation() -> tuple[ConversationInput, dict]:
    """
    MSG1 sent, prospect replied with a question → action should be MSG2.
    """
    conv = ConversationInput(
        raw_text="",
        prospect_name="Laura García",
        messages=[
            Message(speaker="hint", text="Hola Laura, vi tu publicacion y me parecio muy interesante.", index=0),
            Message(
                speaker="prospect",
                text="Hola! Me parece interesante lo que planteas. De que se trata exactamente?",
                index=1,
            ),
        ],
    )
    pd = {"stage": "1", "sector": "Tecnologia", "cargo_seniority": "MANAGER"}
    return conv, pd


def _wait_conversation() -> tuple[ConversationInput, dict]:
    """
    Stage UNKNOWN → action should be WAIT → blocked result.
    """
    conv = ConversationInput(
        raw_text="",
        prospect_name="Carlos Rodríguez",
        messages=[
            Message(speaker="hint", text="Hola Carlos.", index=0),
        ],
    )
    pd = {"stage": "0"}  # UNKNOWN
    return conv, pd


def _seg1_conversation() -> tuple[ConversationInput, dict]:
    """
    Dossier sent 5 days ago → action should be SEG1.
    """
    conv = ConversationInput(
        raw_text="",
        prospect_name="Silvia Rojas",
        messages=[
            Message(speaker="hint", text="Te puedo enviar el dossier por aca si no es mucha molestia.", index=0),
            Message(speaker="prospect", text="Claro, mandamelo!", index=1),
        ],
    )
    pd = {
        "stage": "3",
        "sector": "Retail",
        "cargo_seniority": "DIRECTOR",
        "days_since_dossier": 5,
    }
    return conv, pd


# ═══════════════════════════════════════════════════════════════════════════════
# RETURN TYPE
# ═══════════════════════════════════════════════════════════════════════════════

class TestReturnType:
    def test_returns_run_result(self):
        conv, pd = _msg2_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert isinstance(result, RunResult)

    def test_blocked_returns_run_result(self):
        conv, pd = _wait_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert isinstance(result, RunResult)


# ═══════════════════════════════════════════════════════════════════════════════
# WAIT / BLOCKED paths
# ═══════════════════════════════════════════════════════════════════════════════

class TestWaitPath:
    def test_wait_is_blocked(self):
        conv, pd = _wait_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.blocked is True

    def test_wait_has_no_final_message(self):
        conv, pd = _wait_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.final_message is None

    def test_wait_approved_is_false(self):
        conv, pd = _wait_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.approved is False

    def test_wait_has_block_reason(self):
        conv, pd = _wait_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.block_reason is not None and result.block_reason != ""

    def test_wait_action_is_wait_or_none(self):
        conv, pd = _wait_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.action in ("WAIT", "NONE")

    def test_wait_context_is_none(self):
        conv, pd = _wait_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.context is None

    def test_wait_draft_is_none(self):
        conv, pd = _wait_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.draft is None

    def test_wait_review_is_none(self):
        conv, pd = _wait_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.review is None


# ═══════════════════════════════════════════════════════════════════════════════
# HAPPY PATH — MSG2
# ═══════════════════════════════════════════════════════════════════════════════

class TestMSG2HappyPath:
    def test_action_is_msg2(self):
        conv, pd = _msg2_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.action == "MSG2"

    def test_not_blocked(self):
        conv, pd = _msg2_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.blocked is False

    def test_context_is_set(self):
        conv, pd = _msg2_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.context is not None

    def test_draft_is_set(self):
        conv, pd = _msg2_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.draft is not None
        assert isinstance(result.draft, str)
        assert len(result.draft) > 0

    def test_review_is_set(self):
        conv, pd = _msg2_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.review is not None

    def test_approved_clean_draft(self):
        conv, pd = _msg2_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.approved is True

    def test_final_message_is_draft(self):
        conv, pd = _msg2_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.final_message == result.draft

    def test_prospect_name_preserved(self):
        conv, pd = _msg2_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.prospect_name == "Laura García"

    def test_analysis_populated(self):
        conv, pd = _msg2_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.analysis.stage.value == "1"

    def test_evidence_populated(self):
        conv, pd = _msg2_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.evidence is not None


# ═══════════════════════════════════════════════════════════════════════════════
# REVIEWER REJECTION
# ═══════════════════════════════════════════════════════════════════════════════

class TestReviewerRejection:
    def test_failing_draft_not_approved(self):
        conv, pd = _msg2_conversation()
        result = run(conv, FAILING_ADAPTER, prospect_data=pd)
        assert result.approved is False

    def test_failing_draft_no_final_message(self):
        conv, pd = _msg2_conversation()
        result = run(conv, FAILING_ADAPTER, prospect_data=pd)
        assert result.final_message is None

    def test_failing_draft_not_blocked(self):
        # Reviewer rejection ≠ pipeline blocked
        conv, pd = _msg2_conversation()
        result = run(conv, FAILING_ADAPTER, prospect_data=pd)
        assert result.blocked is False

    def test_failing_draft_has_violations(self):
        conv, pd = _msg2_conversation()
        result = run(conv, FAILING_ADAPTER, prospect_data=pd)
        assert result.review is not None
        assert len(result.review.violations) > 0

    def test_failing_draft_score_less_than_1(self):
        conv, pd = _msg2_conversation()
        result = run(conv, FAILING_ADAPTER, prospect_data=pd)
        assert result.review.score < 1.0

    def test_draft_still_captured_on_rejection(self):
        conv, pd = _msg2_conversation()
        result = run(conv, FAILING_ADAPTER, prospect_data=pd)
        assert result.draft == FailingAdapter.DRAFT


# ═══════════════════════════════════════════════════════════════════════════════
# DEBUG MODE
# ═══════════════════════════════════════════════════════════════════════════════

class TestDebugMode:
    def test_debug_does_not_crash(self):
        conv, pd = _msg2_conversation()
        result = run(conv, ADAPTER, prospect_data=pd, debug=True)
        assert isinstance(result, RunResult)

    def test_debug_wait_does_not_crash(self):
        conv, pd = _wait_conversation()
        result = run(conv, ADAPTER, prospect_data=pd, debug=True)
        assert result.blocked is True

    def test_debug_returns_same_result_as_no_debug(self):
        conv, pd = _msg2_conversation()
        r1 = run(conv, ADAPTER, prospect_data=pd, debug=False)
        r2 = run(conv, ADAPTER, prospect_data=pd, debug=True)
        assert r1.approved == r2.approved
        assert r1.action == r2.action


# ═══════════════════════════════════════════════════════════════════════════════
# DECISION LOG
# ═══════════════════════════════════════════════════════════════════════════════

class TestDecisionLog:
    def test_log_file_created(self, tmp_path):
        conv, pd = _msg2_conversation()
        run(conv, ADAPTER, prospect_data=pd, log_dir=tmp_path)
        all_files = list(tmp_path.rglob("*.json"))
        assert len(all_files) == 1

    def test_log_file_is_valid_json(self, tmp_path):
        conv, pd = _msg2_conversation()
        run(conv, ADAPTER, prospect_data=pd, log_dir=tmp_path)
        log_file = next(tmp_path.rglob("*.json"))
        data = json.loads(log_file.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_log_has_prospect_name(self, tmp_path):
        conv, pd = _msg2_conversation()
        run(conv, ADAPTER, prospect_data=pd, log_dir=tmp_path)
        log_file = next(tmp_path.rglob("*.json"))
        data = json.loads(log_file.read_text(encoding="utf-8"))
        assert data["prospect"] == "Laura García"

    def test_log_has_approved_field(self, tmp_path):
        conv, pd = _msg2_conversation()
        run(conv, ADAPTER, prospect_data=pd, log_dir=tmp_path)
        log_file = next(tmp_path.rglob("*.json"))
        data = json.loads(log_file.read_text(encoding="utf-8"))
        assert "approved" in data

    def test_log_has_trace(self, tmp_path):
        conv, pd = _msg2_conversation()
        run(conv, ADAPTER, prospect_data=pd, log_dir=tmp_path)
        log_file = next(tmp_path.rglob("*.json"))
        data = json.loads(log_file.read_text(encoding="utf-8"))
        assert "trace" in data

    def test_log_trace_has_analysis(self, tmp_path):
        conv, pd = _msg2_conversation()
        run(conv, ADAPTER, prospect_data=pd, log_dir=tmp_path)
        log_file = next(tmp_path.rglob("*.json"))
        data = json.loads(log_file.read_text(encoding="utf-8"))
        assert "analysis" in data["trace"]

    def test_log_in_date_subdirectory(self, tmp_path):
        conv, pd = _msg2_conversation()
        run(conv, ADAPTER, prospect_data=pd, log_dir=tmp_path)
        subdirs = [d for d in tmp_path.iterdir() if d.is_dir()]
        assert len(subdirs) == 1
        # Dir name looks like YYYY-MM-DD
        import re
        assert re.match(r"\d{4}-\d{2}-\d{2}", subdirs[0].name)

    def test_log_prospect_slug_in_filename(self, tmp_path):
        conv, pd = _msg2_conversation()
        run(conv, ADAPTER, prospect_data=pd, log_dir=tmp_path)
        log_file = next(tmp_path.rglob("*.json"))
        assert "laura" in log_file.name.lower()

    def test_no_log_without_log_dir(self, tmp_path):
        conv, pd = _msg2_conversation()
        run(conv, ADAPTER, prospect_data=pd)  # no log_dir
        all_files = list(tmp_path.rglob("*.json"))
        assert len(all_files) == 0

    def test_blocked_run_also_logs(self, tmp_path):
        conv, pd = _wait_conversation()
        run(conv, ADAPTER, prospect_data=pd, log_dir=tmp_path)
        all_files = list(tmp_path.rglob("*.json"))
        assert len(all_files) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# DETERMINISM
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeterminism:
    def test_same_input_same_result(self):
        conv, pd = _msg2_conversation()
        r1 = run(conv, ADAPTER, prospect_data=pd)
        r2 = run(conv, ADAPTER, prospect_data=pd)
        assert r1.approved == r2.approved
        assert r1.action == r2.action
        assert r1.draft == r2.draft
        assert r1.review.score == r2.review.score

    def test_seg1_action(self):
        conv, pd = _seg1_conversation()
        result = run(conv, ADAPTER, prospect_data=pd)
        assert result.action == "SEG1"
