# -*- coding: utf-8 -*-
"""Valida que nada se salga de la slide y estima overflow de texto."""
import sys
from pptx import Presentation
from pptx.util import Emu, Pt

EMU_IN = 914400

def check(path):
    prs = Presentation(path)
    W, H = prs.slide_width, prs.slide_height
    print("\n" + "=" * 72)
    print(path.split('/')[-1], " %.2fx%.2f in" % (W / EMU_IN, H / EMU_IN))
    print("=" * 72)
    problems = 0
    for i, s in enumerate(prs.slides, 1):
        for sh in s.shapes:
            if sh.left is None:
                continue
            r = sh.left + (sh.width or 0)
            b = sh.top + (sh.height or 0)
            tag = ""
            if sh.left < -1000 or sh.top < -1000:
                tag = "FUERA-izq/arriba"
            elif r > W + 1000 or b > H + 1000:
                tag = "DESBORDA (%.2f,%.2f)" % (r / EMU_IN, b / EMU_IN)
            if tag:
                txt = (sh.text_frame.text[:45].replace("\n", " ") if sh.has_text_frame else "")
                print("  slide %-2d  %-26s %s" % (i, tag, txt))
                problems += 1
        # estimacion de overflow de texto en cajas
        for sh in s.shapes:
            if not sh.has_text_frame or sh.width is None:
                continue
            tf = sh.text_frame
            wpt = sh.width / EMU_IN * 72
            hpt = sh.height / EMU_IN * 72
            total = 0
            for p in tf.paragraphs:
                t = "".join(r.text for r in p.runs)
                if not t:
                    total += 10
                    continue
                sz = max([(r.font.size.pt if r.font.size else 18) for r in p.runs] or [18])
                # ~0.52*size = ancho medio de caracter en Segoe UI
                chars_per_line = max(int(wpt / (sz * 0.50)), 1)
                nlines = max(1, -(-len(t) // chars_per_line))
                total += nlines * sz * 1.25
            if total > hpt * 2.6 and total > 60:
                txt = tf.text[:42].replace("\n", " ")
                print("  slide %-2d  TEXTO LARGO  cajaH=%.0fpt  estim=%.0fpt  | %s" % (i, hpt, total, txt))
                problems += 1
    print("  -> %d avisos" % problems)
    return problems

tot = 0
for p in sys.argv[1:]:
    tot += check(p)
print("\nTOTAL avisos:", tot)
