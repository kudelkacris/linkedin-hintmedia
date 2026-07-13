# -*- coding: utf-8 -*-
"""
cre_decide.py - CRE decision runner para uso desde Claude Code chat.

Lee la conversacion de un archivo, corre el motor determinístico (sin LLM),
y devuelve la decision como JSON.

Uso:
    python cre_decide.py --conv conv.txt --name "Laura Garcia" --stage 2
    python cre_decide.py --conv conv.txt --name "Silvia Rojas" --stage 3 --days-dossier 5 --seniority DIRECTOR --sector Retail

Opciones:
    --conv          Path al archivo con la conversacion pegada
    --name          Nombre del prospecto
    --stage         Stage actual: 1=MSG1 2=MSG2 3=dossier 4=SEG1 5=SEG2
    --sector        Sector del prospecto (opcional)
    --seniority     CEO | DIRECTOR | MANAGER | SPECIALIST | OTHER (default: OTHER)
    --days-dossier  Dias desde que se envio el dossier (activa SEG1)
"""
import sys
import io
import json
import argparse
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

from commercial_reasoning_engine.analyzer.parser import parse
from commercial_reasoning_engine.llm.adapter import LLMAdapter
from commercial_reasoning_engine.llm.context_only_adapter import ContextOnlyAdapter
from commercial_reasoning_engine.run import run


class _DryRun(LLMAdapter):
    def _call(self, prompt: str) -> str:
        return "[dry-run]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conv",         required=True)
    ap.add_argument("--name",         required=True)
    ap.add_argument("--stage",        default="1")
    ap.add_argument("--sector",       default="")
    ap.add_argument("--seniority",    default="OTHER",
                    choices=["CEO", "DIRECTOR", "MANAGER", "SPECIALIST", "OTHER"])
    ap.add_argument("--days-dossier", type=int, default=None)
    args = ap.parse_args()

    conv_text = Path(args.conv).read_text(encoding="utf-8")
    conversation = parse(conv_text, prospect_name=args.name)

    prospect_data = {
        "stage": args.stage,
        "sector": args.sector,
        "cargo_seniority": args.seniority,
    }
    if args.days_dossier is not None:
        prospect_data["days_since_dossier"] = args.days_dossier

    context_adapter = ContextOnlyAdapter()
    result = run(conversation, adapter=context_adapter, prospect_data=prospect_data)

    a = result.analysis

    out = {
        "prospect_name": result.prospect_name,
        "stage":         a.stage.value,
        "engagement":    a.engagement.value,
        "seniority":     a.seniority.value,
        "sector":        a.sector,
        "temperature":   a.temperature.value,
        "action":        result.action,
        "strategy":      result.strategy_cl.strategy.value,
        "blocked":       result.blocked,
        "block_reason":  result.block_reason,
    }

    if not result.blocked and result.decision:
        d = result.decision
        out.update({
            "objective":        d.unique_objective,
            "mention_hint":     d.mention_hint,
            "mention_dossier":  d.mention_dossier,
            "propose_meeting":  d.propose_meeting,
            "rotation_applied": d.rotation_applied,
            "previous_angle":   d.previous_angle,
            "new_angle":        d.new_angle,
            "personal_win":     d.personal_win,
            "reference_client": d.reference_client,
            "conversation_mode": d.conversation_mode.value,
        })
        if result.context:
            out["prompt"] = context_adapter.build_prompt(result.context)

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
