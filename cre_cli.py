# -*- coding: utf-8 -*-
"""
cre_cli.py - CLI del CRE (Commercial Reasoning Engine)

Uso basico (sin LLM, solo decision del motor):
    python cre_cli.py --name "Laura Garcia" --stage 1

Con sector y seniority:
    python cre_cli.py --name "Laura Garcia" --stage 1 --sector Tecnologia --seniority MANAGER

Con dossier enviado hace N dias (para SEG1):
    python cre_cli.py --name "Silvia Rojas" --stage 3 --days-dossier 5 --seniority DIRECTOR

Con LLM real (requiere ANTHROPIC_API_KEY en el entorno):
    python cre_cli.py --name "Laura Garcia" --stage 1 --llm

Guardar decision log:
    python cre_cli.py --name "Laura Garcia" --stage 1 --log
"""
import sys
import os
import io
import argparse
from pathlib import Path

# Forzar UTF-8 en Windows para que los acentos no rompan el output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

from commercial_reasoning_engine.analyzer.parser import parse
from commercial_reasoning_engine.llm.adapter import LLMAdapter
from commercial_reasoning_engine.run import run


# ── Adapter sin LLM ───────────────────────────────────────────────────────────

class DryRunAdapter(LLMAdapter):
    def _call(self, prompt: str) -> str:
        return "[DRY RUN - sin LLM. Usar --llm para generar el mensaje.]"


# ── Input ─────────────────────────────────────────────────────────────────────

def _read_conversation() -> str:
    print()
    print("Pega la conversacion de LinkedIn.")
    print("Presiona Enter dos veces cuando termines.")
    print("-" * 50)
    lines = []
    blank_count = 0
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "":
            blank_count += 1
            if blank_count >= 2:
                break
            lines.append("")
        else:
            blank_count = 0
            lines.append(line)
    return "\n".join(lines).strip()


# ── Output ────────────────────────────────────────────────────────────────────

def _print_decision(result) -> None:
    a = result.analysis
    d = result.decision

    print()
    print("=" * 52)
    print("  DECISION DEL MOTOR")
    print("=" * 52)
    print(f"  Prospecto    : {result.prospect_name}")
    print(f"  Stage        : {a.stage.value}")
    print(f"  Engagement   : {a.engagement.value}")
    print(f"  Seniority    : {a.seniority.value}")
    print(f"  Sector       : {a.sector or '(no especificado)'}")
    print(f"  Temperatura  : {a.temperature.value}")
    print("-" * 52)
    print(f"  Accion       : {result.action}")
    print(f"  Estrategia   : {result.strategy_cl.strategy.value}")

    if result.blocked:
        print(f"  BLOQUEADO    : {result.block_reason}")
    else:
        print(f"  Objetivo     : {d.unique_objective}")
        print(f"  Hint         : {'Si' if d.mention_hint else 'No'}")
        print(f"  Dossier      : {'Si' if d.mention_dossier else 'No'}")
        print(f"  Reunion      : {'Si' if d.propose_meeting else 'No'}")
        print(f"  Rotacion     : {'Si' if d.rotation_applied else 'No'}")
        if d.new_angle:
            print(f"  Angulo       : {d.new_angle}")
        if d.personal_win:
            print(f"  Win personal : {d.personal_win}")
        if d.reference_client:
            print(f"  Cliente ref  : {d.reference_client}")

    if result.review:
        rv = result.review
        print("-" * 52)
        estado = "APROBADO" if rv.approved else "RECHAZADO"
        print(f"  Reviewer     : {estado} (score {rv.score})")
        for v in rv.violations:
            print(f"  ! [{v.rule}] {v.description[:60]}")

    print("=" * 52)


def _print_message(result) -> None:
    if result.final_message and "[DRY RUN" not in result.final_message:
        print()
        print("-" * 52)
        print("  MENSAJE")
        print("-" * 52)
        print()
        print(result.final_message)
        print()
    elif result.draft and "[DRY RUN" in result.draft:
        print()
        print("  Modo dry-run: el motor decidio pero no llamo al LLM.")
        print("  Usa --llm para generar el mensaje.")
        print()
    elif not result.approved and result.draft:
        print()
        print("  DRAFT RECHAZADO por Reviewer:")
        print()
        print(result.draft)
        print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="CRE CLI - Motor de Razonamiento Comercial")
    ap.add_argument("--name",     required=True,  help="Nombre del prospecto")
    ap.add_argument("--stage",    default="0",    help="Stage: 0=desconocido 1=MSG1 2=MSG2 3=dossier 4=SEG1")
    ap.add_argument("--sector",   default="",     help="Sector del prospecto")
    ap.add_argument("--seniority", default="OTHER",
                    choices=["CEO", "DIRECTOR", "MANAGER", "SPECIALIST", "OTHER"])
    ap.add_argument("--days-dossier", type=int, default=None,
                    help="Dias desde que se envio el dossier (activa SEG1)")
    ap.add_argument("--llm",  action="store_true", help="Llamar al LLM real (requiere ANTHROPIC_API_KEY)")
    ap.add_argument("--log",  action="store_true", help="Guardar decision log en decision_logs/")
    args = ap.parse_args()

    raw_text = _read_conversation()
    if not raw_text:
        print("Error: conversacion vacia.")
        sys.exit(1)

    conversation = parse(raw_text, prospect_name=args.name)

    prospect_data = {
        "stage": args.stage,
        "sector": args.sector,
        "cargo_seniority": args.seniority,
    }
    if args.days_dossier is not None:
        prospect_data["days_since_dossier"] = args.days_dossier

    if args.llm:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: falta ANTHROPIC_API_KEY en el entorno.")
            sys.exit(1)
        try:
            from commercial_reasoning_engine.llm.claude_adapter import ClaudeAdapter
            adapter = ClaudeAdapter(api_key=api_key)
        except ImportError:
            print("Error: ejecutar 'pip install anthropic' primero.")
            sys.exit(1)
    else:
        adapter = DryRunAdapter()

    log_dir = Path("decision_logs") if args.log else None

    result = run(conversation, adapter=adapter, prospect_data=prospect_data, log_dir=log_dir)

    _print_decision(result)
    _print_message(result)

    if args.log:
        print(f"  Log en: decision_logs/")


if __name__ == "__main__":
    main()
