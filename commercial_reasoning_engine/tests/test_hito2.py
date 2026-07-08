"""
Tests for HITO 2 — Parser, Analyzer, Dataset Reader.
Each test is independent. No LLM calls. No external dependencies.
Run: python -m pytest commercial_reasoning_engine/tests/test_hito2.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from commercial_reasoning_engine.analyzer.parser import parse
from commercial_reasoning_engine.analyzer.analyzer import analyze
from commercial_reasoning_engine.dataset.reader import find_and_read
from commercial_reasoning_engine.schemas.analysis import (
    Stage, Engagement, Seniority, Temperature
)


# ─────────────────────────────────────────────────────────────────────────────
# PARSER TESTS
# ─────────────────────────────────────────────────────────────────────────────

CONV_MSG1_ONLY = """Carla, gracias por conectar. Estuve revisando lo que venís haciendo en Novartis. Me llamó la atención que estés compartiendo contenido sobre IA y omnicanalidad."""

CONV_MSG1_RESPONSE = """Carla, gracias por conectar. Estuve revisando lo que venís haciendo en Novartis.

Hola Florencia. Si, decime."""

CONV_FULL_WITH_DOSSIER = """Carla, gracias por conectar. Estuve revisando lo que venís haciendo en Novartis.

Hola Florencia. Si, decime.

Buenas Carla! Me quedé pensando en esa frase del Summit de Yoizen. Trabajamos en Hint Media con empresas del sector. Tenemos un dossier breve con casos concretos. Te puedo enviar por acá si no es mucha molestia, o me indicarías a quién se lo puedo mandar?

Si claro podés enviármelo!

😉🤗😄👍"""

CONV_EMOJI_RESPONSE = """Buenas Silvia! Gracias por conectar.

😊👍"""


def test_parser_extracts_name():
    result = parse(CONV_MSG1_ONLY)
    assert result.prospect_name == "Carla", f"Expected 'Carla', got '{result.prospect_name}'"


def test_parser_single_message():
    result = parse(CONV_MSG1_ONLY)
    assert len(result.messages) == 1
    assert result.messages[0].speaker == "hint"


def test_parser_two_messages():
    result = parse(CONV_MSG1_RESPONSE)
    assert len(result.messages) == 2
    assert result.messages[0].speaker == "hint"
    assert result.messages[1].speaker == "prospect"


def test_parser_full_conversation():
    result = parse(CONV_FULL_WITH_DOSSIER)
    speakers = [m.speaker for m in result.messages]
    assert speakers[0] == "hint"
    assert speakers[-1] == "prospect"   # emoji block = prospect
    assert "hint" in speakers
    assert "prospect" in speakers


def test_parser_emoji_only_is_prospect():
    result = parse(CONV_EMOJI_RESPONSE)
    emoji_msg = result.messages[-1]
    assert emoji_msg.speaker == "prospect"


def test_parser_preserves_raw_text():
    result = parse(CONV_MSG1_ONLY)
    assert result.raw_text == CONV_MSG1_ONLY


def test_parser_name_override():
    result = parse(CONV_MSG1_ONLY, prospect_name="Override")
    assert result.prospect_name == "Override"


def test_parser_message_indices_sequential():
    result = parse(CONV_FULL_WITH_DOSSIER)
    for i, m in enumerate(result.messages):
        assert m.index == i


# ─────────────────────────────────────────────────────────────────────────────
# ANALYZER TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_analyzer_no_response_is_stage1():
    conv = parse(CONV_MSG1_ONLY)
    result = analyze(conv)
    assert result.stage == Stage.MSG1_SENT


def test_analyzer_dossier_detected_from_hint_text():
    conv = parse(CONV_FULL_WITH_DOSSIER)
    result = analyze(conv)
    assert result.dossier_sent is True


def test_analyzer_emojis_score_high_engagement():
    conv = parse(CONV_FULL_WITH_DOSSIER)
    result = analyze(conv)
    assert result.engagement == Engagement.HIGH


def test_analyzer_no_response_is_low_engagement():
    conv = parse(CONV_MSG1_ONLY)
    result = analyze(conv)
    assert result.engagement == Engagement.LOW


def test_analyzer_last_prospect_message():
    conv = parse(CONV_MSG1_RESPONSE)
    result = analyze(conv)
    assert "Hola Florencia" in result.last_prospect_message


def test_analyzer_exact_words_extracted():
    conv = parse(CONV_MSG1_RESPONSE)
    result = analyze(conv)
    assert len(result.prospect_exact_words) > 0


def test_analyzer_stage_from_prospect_data():
    conv = parse(CONV_MSG1_ONLY)
    result = analyze(conv, prospect_data={"stage": "3"})
    assert result.stage == Stage.DOSSIER_SENT


def test_analyzer_seniority_from_prospect_data():
    conv = parse(CONV_MSG1_ONLY)
    result = analyze(conv, prospect_data={"cargo_seniority": "DIRECTOR"})
    assert result.seniority == Seniority.DIRECTOR
    assert result.is_decision_maker is True


def test_analyzer_specialist_not_decision_maker():
    conv = parse(CONV_MSG1_ONLY)
    result = analyze(conv, prospect_data={"cargo_seniority": "SPECIALIST"})
    assert result.is_decision_maker is False


def test_analyzer_temperature_hot_on_high_engagement():
    conv = parse(CONV_FULL_WITH_DOSSIER)
    result = analyze(conv)
    assert result.temperature == Temperature.HOT


def test_analyzer_temperature_cold_no_response():
    conv = parse(CONV_MSG1_ONLY)
    result = analyze(conv)
    assert result.temperature == Temperature.COLD


def test_analyzer_sector_from_prospect_data():
    conv = parse(CONV_MSG1_ONLY)
    result = analyze(conv, prospect_data={"sector": "Farmacéutico"})
    assert result.sector == "Farmacéutico"


def test_analyzer_days_since_dossier_from_prospect_data():
    conv = parse(CONV_MSG1_ONLY)
    result = analyze(conv, prospect_data={"days_since_dossier": 9})
    assert result.days_since_dossier == 9


def test_analyzer_no_hint_msgs_stage_unknown():
    """Edge case: empty conversation."""
    conv = parse("")
    result = analyze(conv)
    assert result.stage == Stage.MSG1_SENT  # no messages → treated as MSG1 sent


# ─────────────────────────────────────────────────────────────────────────────
# DATASET READER TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_reader_carla_bertossi():
    """Carla Bertossi .md exists in conversaciones/junio/."""
    result = find_and_read("Carla Bertossi")
    assert result is not None, "Expected to find carla-bertossi.md"
    assert result["cargo"] is not None
    assert result["empresa"] is not None
    assert result["sector"] is not None


def test_reader_seniority_normalization():
    """Marketing Associate should map to SPECIALIST."""
    result = find_and_read("Carla Bertossi")
    if result:
        assert result["cargo_seniority"] == "SPECIALIST", (
            f"Expected SPECIALIST for 'Marketing Associate', got {result['cargo_seniority']}"
        )


def test_reader_sector_normalization():
    """Farmacéutico/Salud should normalize to Farmacéutico."""
    result = find_and_read("Carla Bertossi")
    if result:
        assert result["sector"] == "Farmacéutico", (
            f"Expected 'Farmacéutico', got {result['sector']}"
        )


def test_reader_unknown_prospect_returns_none():
    result = find_and_read("Prospecto Inexistente XYZ123")
    assert result is None


def test_reader_file_path_returned():
    result = find_and_read("Carla Bertossi")
    if result:
        assert "file_path" in result
        assert result["file_path"].endswith(".md")


def test_reader_stage_from_estado():
    result = find_and_read("Carla Bertossi")
    if result:
        # Carla's estado in .md should map to stage "4" (SEG1 enviado)
        assert result["stage"] in ("3", "4"), f"Unexpected stage: {result['stage']}"


def test_reader_days_since_dossier_is_int_or_none():
    result = find_and_read("Carla Bertossi")
    if result:
        val = result["days_since_dossier"]
        assert val is None or isinstance(val, int)


def test_reader_prospect_responses_list():
    result = find_and_read("Carla Bertossi")
    if result:
        assert isinstance(result["prospect_responses"], list)


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION: PARSER + READER → ANALYZER
# ─────────────────────────────────────────────────────────────────────────────

def test_integration_carla_full_pipeline():
    """
    Full HITO 2 pipeline: reader → parser → analyzer.
    Validates that all three modules produce coherent output.
    """
    prospect_data = find_and_read("Carla Bertossi")
    conv = parse(CONV_FULL_WITH_DOSSIER, prospect_name="Carla")
    result = analyze(conv, prospect_data=prospect_data)

    assert result.dossier_sent is True
    assert result.engagement == Engagement.HIGH
    assert result.sector == "Farmacéutico"
    assert result.seniority == Seniority.SPECIALIST
    assert result.temperature == Temperature.HOT
    assert len(result.prospect_exact_words) > 0
