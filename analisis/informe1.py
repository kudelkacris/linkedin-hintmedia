# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scratchpad'))
from deck import *
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

prs = new_deck()
N = [0]
def nx():
    N[0] += 1
    return N[0]

# ============ 1 PORTADA ============
s = blank(prs)
rect(s, Inches(0), Inches(0), Inches(0.14), H, fill=ACC, radius=False)
tb(s, Inches(0.9), Inches(1.5), Inches(8), Inches(0.3), "HINT MEDIA  ·  LINKEDIN OUTREACH", size=12, color=ACC, bold=True)
tb(s, Inches(0.9), Inches(2.0), Inches(11), Inches(1.6), "Informe Septiembre 2026", size=54, bold=True)
tb(s, Inches(0.9), Inches(3.3), Inches(10.5), Inches(0.9),
   "Analisis del mes y comparativa de la evolucion junio - julio - agosto - septiembre", size=19, color=MUT)
rect(s, Inches(0.9), Inches(4.35), Inches(1.5), Pt(3), fill=ACC, radius=False)
for i, (b, l) in enumerate([("1.102", "conversaciones\nanalizadas"), ("4", "meses\ncomparados"),
                            ("108", "dossiers\nenviados"), ("8", "reuniones\nconseguidas")]):
    x = Inches(0.9) + i * Inches(2.5)
    tb(s, x, Inches(4.8), Inches(2.3), Inches(0.6), b, size=36, bold=True, color=TXT)
    tb(s, x, Inches(5.45), Inches(2.3), Inches(0.7), l, size=11, color=MUT, line=1.2)
tb(s, Inches(0.9), Inches(6.7), Inches(8), Inches(0.3), "20 de septiembre de 2026  ·  Fuente: conversaciones/*.md + historial.json", size=10, color=MUT)

# ============ 2 RESUMEN EJECUTIVO ============
s = blank(prs)
title(s, "Resumen ejecutivo", "Septiembre fue el peor mes del proyecto. Y sabemos por que.")
kpi(s, Inches(0.7), Inches(2.0), Inches(2.85), "15,9%", "Tasa de respuesta", "junio fue 75,6%  ▼ -59,7 pts", color=BAD)
kpi(s, Inches(3.75), Inches(2.0), Inches(2.85), "3,2%", "Tasa de dossier", "junio fue 15,7%  ▼ -12,5 pts", color=BAD)
kpi(s, Inches(6.8), Inches(2.0), Inches(2.85), "0", "SEG1 enviados", "en junio fueron 48", color=BAD)
kpi(s, Inches(9.85), Inches(2.0), Inches(2.85), "1", "Reunion", "sobre 315 contactos", color=WARN)
rect(s, Inches(0.7), Inches(3.75), Inches(12), Inches(1.15), fill=CARD, lineclr=BAD)
tb(s, Inches(1.0), Inches(3.95), Inches(11.4), Inches(0.9),
   "La causa no es el mercado ni la lista. Es un cambio de metodologia que se hizo el 20/08/26:\n"
   "el MSG1 paso a mencionar Hint Media y a cerrar con \"Vale la pena que te cuente...\" en vez de \"tenia una consulta\".",
   size=14.5, line=1.3)
bullets(s, Inches(0.7), Inches(5.15), Inches(5.8), [
    ('El CTA se rompio', '"Tenia una consulta" convierte 57,3%. "Vale la pena que te cuente" convierte 15,9%.'),
    ('Hint entro al primer mensaje', 'Con Hint en el MSG1: 16,0% de respuesta. Sin Hint: 59,1%.'),
], dotclr=BAD)
bullets(s, Inches(6.9), Inches(5.15), Inches(5.8), [
    ('El seguimiento desaparecio', '93,7% de los contactos de septiembre recibieron un solo mensaje. Cero SEG1.'),
    ('Se quemaron 34 respuestas', '68% de quienes contestaron en septiembre nunca recibieron un MSG2.'),
], dotclr=BAD)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 3 EVOLUCION MES A MES ============
s = blank(prs)
title(s, "Comparativa", "Evolucion mes a mes", "Los cuatro meses del proyecto, mismos criterios de medicion")
rowsd = [
    ["Junio",      "172", "130", "75,6%", "105", "27", "15,7%", "48", "3"],
    ["Julio",      "283", "126", "44,5%", "123", "35", "12,4%", "11", "3"],
    ["Agosto",     "332",  "86", "25,9%",  "59", "36", "10,8%", "11", "1"],
    ["Septiembre", "315",  "50", "15,9%",  "20", "10",  "3,2%",  "0", "1"],
]
def clr_resp(v, ri):
    return [GOOD, GOOD, WARN, BAD][ri]
table(s, Inches(0.7), Inches(2.25), Inches(11.9),
      ["Mes", "Contactos", "Respuestas", "Tasa resp.", "MSG2", "Dossiers", "Tasa doss.", "SEG1", "Reuniones"],
      rowsd, colw=[Inches(1.9)] + [Inches(1.25)] * 8, rowh=Inches(0.46), size=13,
      colorcols={3: clr_resp, 6: clr_resp, 7: lambda v, r: [GOOD, WARN, WARN, BAD][r]})
rect(s, Inches(0.7), Inches(4.9), Inches(12), Inches(0.95), fill=CARD, lineclr=WARN)
tb(s, Inches(1.0), Inches(5.08), Inches(11.4), Inches(0.7),
   "El volumen casi se duplico (172 → 315 contactos) mientras la conversion se dividio por cinco.\n"
   "Mas contactos no compenso peor mensaje: en valor absoluto pasamos de 27 dossiers a 10.", size=13.5, line=1.3)
tb(s, Inches(0.7), Inches(6.15), Inches(12), Inches(0.5),
   "Nota de metodo: la cohorte de septiembre con 15+ dias de maduracion rinde 28,6% de respuesta, no 15,9%. "
   "Aun corrigiendo ese sesgo, la caida frente a junio (75,6%) y julio (44,5%) es real.", size=10.5, color=MUT, line=1.25)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 4 GRAFICO CAIDA ============
s = blank(prs)
title(s, "Comparativa", "La curva de la caida", "Tasa de respuesta y tasa de dossier por mes")
tb(s, Inches(0.7), Inches(2.1), Inches(5.6), Inches(0.3), "TASA DE RESPUESTA", size=11, color=ACC, bold=True)
bars(s, Inches(0.7), Inches(2.55), Inches(5.6), Inches(2.5),
     [("Junio", 75.6, GOOD), ("Julio", 44.5, GOOD), ("Agosto", 25.9, WARN), ("Septiembre", 15.9, BAD)],
     maxv=80, barh=Inches(0.42), gap=Inches(0.22), labw=Inches(1.5), valw=Inches(0.9))
tb(s, Inches(7.0), Inches(2.1), Inches(5.6), Inches(0.3), "TASA DE DOSSIER", size=11, color=ACC, bold=True)
bars(s, Inches(7.0), Inches(2.55), Inches(5.6), Inches(2.5),
     [("Junio", 15.7, GOOD), ("Julio", 12.4, GOOD), ("Agosto", 10.8, WARN), ("Septiembre", 3.2, BAD)],
     maxv=18, barh=Inches(0.42), gap=Inches(0.22), labw=Inches(1.5), valw=Inches(0.9))
tb(s, Inches(0.7), Inches(5.35), Inches(5.6), Inches(0.3), "CONTACTOS NUEVOS POR MES", size=11, color=MUT, bold=True)
bars(s, Inches(0.7), Inches(5.75), Inches(5.6), Inches(1.2),
     [("Junio", 172, MUT), ("Julio", 283, MUT), ("Agosto", 332, ACC), ("Septiembre", 315, ACC)],
     maxv=350, fmt="%.0f", barh=Inches(0.22), gap=Inches(0.07), labw=Inches(1.5), valw=Inches(0.9))
rect(s, Inches(7.0), Inches(5.35), Inches(5.6), Inches(1.6), fill=CARD, lineclr=BAD)
tb(s, Inches(7.3), Inches(5.55), Inches(5.0), Inches(1.3),
   "El dossier cayo 3,4x mas rapido que la respuesta.\n"
   "Significa que ademas de responder menos, los que responden\n"
   "avanzan menos: el MSG2 dejo de funcionar como puente.", size=12, line=1.35)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 5 CAUSA 1: EL CTA ============
s = blank(prs)
title(s, "Causa raiz  ·  1 de 4", "El CTA del MSG1 es el factor mas determinante",
      "Comparacion entre las dos formas de cerrar el primer mensaje, sobre toda la base")
bars(s, Inches(0.7), Inches(2.4), Inches(11.9), Inches(2.4), [
    ('"Tenia una consulta"', 57.3, GOOD),
    ('"Ofrece dossier directo"', 20.5, WARN),
    ('"Propone reunion"', 23.9, WARN),
    ('"Vale la pena que te cuente..."', 15.9, BAD),
], maxv=62, barh=Inches(0.44), gap=Inches(0.22), labw=Inches(3.5), valw=Inches(1.0))
tb(s, Inches(0.7), Inches(2.05), Inches(8), Inches(0.3), "TASA DE RESPUESTA SEGUN EL CIERRE DEL MSG1", size=11, color=ACC, bold=True)
y = Inches(4.75)
for i, (t, a, b, c) in enumerate([
    ('"Tenia una consulta"', "n = 342", "57,3% responden", "15,8% dossier"),
    ('"Vale la pena que te cuente"', "n = 290", "15,9% responden", "2,8% dossier")]):
    x = Inches(0.7) + i * Inches(6.2)
    col = GOOD if i == 0 else BAD
    rect(s, x, y, Inches(5.7), Inches(1.5), fill=CARD, lineclr=col)
    tb(s, x + Inches(0.25), y + Inches(0.18), Inches(5.2), Inches(0.35), t, size=15, bold=True, color=col)
    tb(s, x + Inches(0.25), y + Inches(0.62), Inches(5.2), Inches(0.7),
       a + "    ·    " + b + "    ·    " + c, size=12.5, color=TXT)
rect(s, Inches(0.7), Inches(6.45), Inches(11.9), Inches(0.62), fill=CARD2)
tb(s, Inches(0.95), Inches(6.57), Inches(11.4), Inches(0.4),
   "Pedir ayuda abre la conversacion. Anunciar que vas a contar algo la cierra. 3,6x en respuesta, 5,6x en dossier.",
   size=13, bold=True, color=GOLD)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 6 CAUSA 2: HINT EN MSG1 ============
s = blank(prs)
title(s, "Causa raiz  ·  2 de 4", "Mencionar Hint en el primer mensaje corta la respuesta a la mitad",
      "El cambio de metodologia del 20/08/26 introdujo Hint Media dentro del MSG1")
hdr = ["Variante del MSG1", "n", "Respuesta", "Dossier", "Palabras"]
table(s, Inches(0.7), Inches(2.3), Inches(11.9), hdr, [
    ["SIN mencionar Hint", "462", "59,1%", "14,5%", "68"],
    ["CON Hint en el MSG1", "563", "16,0%", "5,3%", "96"],
], colw=[Inches(4.4), Inches(1.5), Inches(2.0), Inches(2.0), Inches(2.0)], rowh=Inches(0.52), size=14,
   colorcols={2: lambda v, r: [GOOD, BAD][r], 3: lambda v, r: [GOOD, BAD][r]})
tb(s, Inches(0.7), Inches(3.9), Inches(11.9), Inches(0.35),
   "Control: solo agosto y septiembre, para descartar que sea un efecto del paso del tiempo", size=11, color=ACC, bold=True)
table(s, Inches(0.7), Inches(4.3), Inches(11.9), hdr[:4], [
    ["SIN mencionar Hint", "108", "42,6%", "14,8%"],
    ["CON Hint en el MSG1", "533", "16,7%", "5,6%"],
], colw=[Inches(4.4), Inches(1.5), Inches(3.0), Inches(3.0)], rowh=Inches(0.46), size=13,
   colorcols={2: lambda v, r: [GOOD, BAD][r], 3: lambda v, r: [GOOD, BAD][r]})
rect(s, Inches(0.7), Inches(5.85), Inches(11.9), Inches(1.0), fill=CARD, lineclr=WARN)
tb(s, Inches(1.0), Inches(6.02), Inches(11.4), Inches(0.75),
   "El efecto se sostiene dentro del mismo periodo: 2,5x en respuesta y 2,6x en dossier.\n"
   "El CLAUDE.md original prohibia mencionar Hint en el MSG1. Esa regla estaba bien y se quito.",
   size=13.5, line=1.3)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 7 CAUSA 3: LONGITUD ============
s = blank(prs)
title(s, "Causa raiz  ·  3 de 4", "Los mensajes se alargaron 62% y la respuesta cayo con ellos",
      "Tasa de respuesta segun la cantidad de palabras del MSG1")
bars(s, Inches(0.7), Inches(2.4), Inches(6.4), Inches(2.3), [
    ("Menos de 60", 67.6, GOOD), ("60 a 90", 39.4, WARN),
    ("90 a 120", 20.3, BAD), ("120 o mas", 15.4, BAD),
], maxv=72, barh=Inches(0.42), gap=Inches(0.2), labw=Inches(2.0), valw=Inches(0.9))
tb(s, Inches(0.7), Inches(2.05), Inches(6), Inches(0.3), "RESPUESTA SEGUN LARGO DEL MSG1", size=11, color=ACC, bold=True)
tb(s, Inches(7.6), Inches(2.05), Inches(5), Inches(0.3), "LARGO MEDIO DEL MSG1 POR MES", size=11, color=ACC, bold=True)
bars(s, Inches(7.6), Inches(2.4), Inches(5.0), Inches(2.3), [
    ("Junio", 58.9, GOOD), ("Julio", 73.4, WARN), ("Agosto", 95.4, BAD), ("Septiembre", 86.6, BAD),
], maxv=100, fmt="%.0f", barh=Inches(0.42), gap=Inches(0.2), labw=Inches(1.5), valw=Inches(0.75))
tb(s, Inches(0.7), Inches(5.0), Inches(11.9), Inches(0.35),
   "Controlado dentro de cada mes, el efecto se mantiene", size=11, color=ACC, bold=True)
table(s, Inches(0.7), Inches(5.4), Inches(11.9), ["Mes", "Corto (<75 pal.)", "Medio (75-100)", "Largo (100+)"], [
    ["Junio",  "96,8% resp",  "100,0% resp", "—"],
    ["Julio",  "46,6% resp",  "46,0% resp",  "7,7% resp"],
    ["Agosto", "45,9% resp",  "28,0% resp",  "16,2% resp"],
], colw=[Inches(2.6), Inches(3.1), Inches(3.1), Inches(3.1)], rowh=Inches(0.38), size=12.5,
   colorcols={1: lambda v, r: GOOD, 2: lambda v, r: [GOOD, GOOD, WARN][r], 3: lambda v, r: BAD})
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 8 CAUSA 4: FOLLOW UP ============
s = blank(prs)
title(s, "Causa raiz  ·  4 de 4", "El seguimiento se apago por completo",
      "Contactos que recibieron un unico mensaje y nunca un segundo toque")
bars(s, Inches(0.7), Inches(2.35), Inches(11.9), Inches(2.1), [
    ("Junio", 31.4, GOOD), ("Julio", 56.5, WARN), ("Agosto", 79.5, BAD), ("Septiembre", 93.7, BAD),
], maxv=100, barh=Inches(0.42), gap=Inches(0.2), labw=Inches(2.0), valw=Inches(0.9))
tb(s, Inches(0.7), Inches(2.0), Inches(8), Inches(0.3), "% DE CONTACTOS CON UN SOLO MENSAJE", size=11, color=ACC, bold=True)
y = Inches(4.65)
for i, (big, lab, sub, col) in enumerate([
    ("97", "Leads quemados", "respondieron y nunca\nrecibieron un MSG2", BAD),
    ("68%", "De las respuestas\nde septiembre", "quedaron sin seguimiento", BAD),
    ("75,9%", "De los dossiers", "nunca recibieron\nun SEG1 de follow-up", BAD),
    ("0,9%", "Dossier → reunion", "108 dossiers\nprodujeron 1 reunion", BAD)]):
    x = Inches(0.7) + i * Inches(3.05)
    rect(s, x, y, Inches(2.85), Inches(1.75), fill=CARD)
    tb(s, x + Inches(0.22), y + Inches(0.16), Inches(2.4), Inches(0.5), big, size=32, bold=True, color=col)
    tb(s, x + Inches(0.22), y + Inches(0.72), Inches(2.5), Inches(0.5), lab, size=11.5, bold=True, line=1.15)
    tb(s, x + Inches(0.22), y + Inches(1.18), Inches(2.5), Inches(0.5), sub, size=9.5, color=MUT, line=1.2)
rect(s, Inches(0.7), Inches(6.6), Inches(11.9), Inches(0.5), fill=CARD2)
tb(s, Inches(0.95), Inches(6.68), Inches(11.4), Inches(0.35),
   "El benchmark del sector es 6 a 12 toques para agendar una reunion B2B. Hint Media entrega 1.", size=13, bold=True, color=GOLD)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 9 GENERO ============
s = blank(prs)
title(s, "Quien responde", "Genero: las mujeres responden mas, pero les escribimos cada vez menos",
      "Mix de la base y conversion por genero, mes a mes")
table(s, Inches(0.7), Inches(2.25), Inches(11.9),
      ["Mes", "Mix mujeres", "Resp. mujeres", "Mix hombres", "Resp. hombres"], [
    ["Junio",      "44,2%", "85,5%", "40,1%", "73,9%"],
    ["Julio",      "37,1%", "43,8%", "56,2%", "43,4%"],
    ["Agosto",     "31,3%", "25,0%", "66,6%", "26,7%"],
    ["Septiembre", "27,9%", "20,5%", "70,5%", "14,4%"],
], colw=[Inches(2.5), Inches(2.35), Inches(2.35), Inches(2.35), Inches(2.35)], rowh=Inches(0.42), size=13,
   colorcols={1: lambda v, r: [GOOD, WARN, WARN, BAD][r], 3: lambda v, r: [GOOD, WARN, BAD, BAD][r]})
y = Inches(4.5)
for i, (big, lab, col) in enumerate([("41,6%", "Respuesta mujeres\n(total proyecto)", GOOD),
                                     ("31,4%", "Respuesta hombres\n(total proyecto)", WARN),
                                     ("5 de 8", "Reuniones conseguidas\nfueron con mujeres", GOOD),
                                     ("-16,3 pts", "Caida del mix femenino\nde junio a septiembre", BAD)]):
    x = Inches(0.7) + i * Inches(3.05)
    rect(s, x, y, Inches(2.85), Inches(1.5), fill=CARD)
    tb(s, x + Inches(0.22), y + Inches(0.2), Inches(2.5), Inches(0.5), big, size=28, bold=True, color=col)
    tb(s, x + Inches(0.22), y + Inches(0.82), Inches(2.5), Inches(0.6), lab, size=11, color=MUT, line=1.25)
rect(s, Inches(0.7), Inches(6.25), Inches(11.9), Inches(0.6), fill=CARD, lineclr=WARN)
tb(s, Inches(0.95), Inches(6.38), Inches(11.4), Inches(0.4),
   "Las listas de septiembre (construccion, mineria, fintech, founders) son estructuralmente masculinas. Eso solo ya costo puntos de conversion.",
   size=12.5)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 10 SENIORITY ============
s = blank(prs)
title(s, "Quien responde", "Seniority: el CEO en frio es el peor interlocutor",
      "Tasa de respuesta y de dossier por nivel jerarquico, base completa")
bars(s, Inches(0.7), Inches(2.3), Inches(6.2), Inches(3.6), [
    ("C-Level (CTO/CFO/CMO)", 57.1, GOOD), ("Coordinador", 66.7, GOOD),
    ("Gerente / Manager", 39.7, GOOD), ("Especialista / Consultor", 35.5, WARN),
    ("Director", 31.7, WARN), ("Founder / Socio", 31.7, WARN),
    ("CEO / Presidente", 25.2, BAD), ("Profesional tecnico", 25.0, BAD),
], maxv=72, barh=Inches(0.31), gap=Inches(0.14), labw=Inches(2.9), valw=Inches(0.85))
tb(s, Inches(0.7), Inches(1.98), Inches(6), Inches(0.3), "TASA DE RESPUESTA", size=11, color=ACC, bold=True)
tb(s, Inches(7.4), Inches(1.98), Inches(5.2), Inches(0.3), "TASA DE DOSSIER", size=11, color=ACC, bold=True)
bars(s, Inches(7.4), Inches(2.3), Inches(5.2), Inches(3.6), [
    ("C-Level", 14.3, GOOD), ("Coordinador", 0.0, BAD), ("Gerente", 10.9, GOOD),
    ("Especialista", 6.5, WARN), ("Director", 9.1, WARN), ("Founder", 11.5, GOOD),
    ("CEO", 5.4, BAD), ("Tecnico", 14.3, GOOD),
], maxv=16, barh=Inches(0.31), gap=Inches(0.14), labw=Inches(1.8), valw=Inches(0.85))
rect(s, Inches(0.7), Inches(6.1), Inches(11.9), Inches(0.75), fill=CARD, lineclr=GOLD)
tb(s, Inches(0.95), Inches(6.22), Inches(11.4), Inches(0.55),
   "Curiosidad: el Coordinador responde mas que nadie (66,7%) y pide dossier en 0% de los casos. Conversa, pero no decide.\n"
   "El C-Level funcional (CTO, CFO, CMO) es el mejor blanco real: 57,1% responde y 14,3% pide dossier.", size=12.5, line=1.3)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 11 SECTOR ============
s = blank(prs)
title(s, "Quien responde", "Sector: estamos invirtiendo el volumen en los peores mercados",
      "Tamano de la base vs. tasa de dossier, base completa")
table(s, Inches(0.7), Inches(2.2), Inches(11.9),
      ["Sector", "Contactos", "Respuesta", "Dossier", "Veredicto"], [
    ["Agencia / Marketing",      "23",  "82,6%", "26,1%", "Mejor ratio, base chica"],
    ["Consultoria / RRHH",       "34",  "50,0%", "20,6%", "Escalar"],
    ["Energia / Oil & Gas",      "159", "24,5%", "13,8%", "Solido, mantener"],
    ["Salud / Farma",            "38",  "47,4%", "13,2%", "Escalar"],
    ["Educacion",                "69",  "36,2%", "10,1%", "Bueno pero fuera de scope"],
    ["Retail / Consumo",         "60",  "45,0%", "8,3%",  "Responde, no compra"],
    ["Construccion / Real Est.", "121", "23,1%", "6,6%",  "Caro para lo que rinde"],
    ["Tecnologia / SaaS",        "257", "26,1%", "6,2%",  "Mayor volumen, peor retorno"],
    ["Mineria",                  "85",  "27,1%", "3,5%",  "Revisar o abandonar"],
    ["Finanzas / Seguros",       "38",  "31,6%", "2,6%",  "Revisar o abandonar"],
], colw=[Inches(3.2), Inches(1.5), Inches(1.7), Inches(1.6), Inches(3.9)], rowh=Inches(0.375), size=12,
   colorcols={3: lambda v, r: GOOD if r < 4 else (WARN if r < 7 else BAD)})
rect(s, Inches(0.7), Inches(6.35), Inches(11.9), Inches(0.55), fill=CARD2)
tb(s, Inches(0.95), Inches(6.46), Inches(11.4), Inches(0.35),
   "Tecnologia + Mineria + Construccion = 463 contactos (42% de la base) y solo 27 dossiers. Consultoria + Salud = 72 contactos y 12 dossiers.",
   size=12.5, bold=True, color=GOLD)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 12 PAIS ============
s = blank(prs)
title(s, "Quien responde", "Geografia: Argentina es el 40% de la base y esta por debajo del promedio",
      "Tasa de respuesta y dossier por pais, base completa")
bars(s, Inches(0.7), Inches(2.35), Inches(6.2), Inches(3.3), [
    ("Costa Rica", 61.5, GOOD), ("Panama", 60.4, GOOD), ("Chile", 41.6, GOOD),
    ("Colombia", 32.0, WARN), ("Espana", 31.7, WARN), ("Mexico", 26.7, WARN),
    ("Argentina", 25.5, BAD), ("Peru", 16.7, BAD),
], maxv=68, barh=Inches(0.31), gap=Inches(0.13), labw=Inches(2.0), valw=Inches(0.85))
tb(s, Inches(0.7), Inches(2.02), Inches(6), Inches(0.3), "TASA DE RESPUESTA", size=11, color=ACC, bold=True)
tb(s, Inches(7.4), Inches(2.02), Inches(5.2), Inches(0.3), "TASA DE DOSSIER", size=11, color=ACC, bold=True)
bars(s, Inches(7.4), Inches(2.35), Inches(5.2), Inches(3.3), [
    ("Panama", 17.0, GOOD), ("Colombia", 12.8, GOOD), ("Chile", 11.2, GOOD),
    ("Argentina", 9.5, WARN), ("Costa Rica", 8.8, WARN), ("Espana", 4.8, BAD),
    ("Mexico", 3.3, BAD), ("Peru", 2.8, BAD),
], maxv=19, barh=Inches(0.31), gap=Inches(0.13), labw=Inches(1.8), valw=Inches(0.85))
rect(s, Inches(0.7), Inches(5.95), Inches(11.9), Inches(0.9), fill=CARD, lineclr=GOLD)
tb(s, Inches(0.95), Inches(6.08), Inches(11.4), Inches(0.7),
   "Panama (n=53) rinde 17,0% de dossier: casi el doble que Argentina (n=440, 9,5%). Centroamerica y Caribe contestan mucho mas.\n"
   "Peru y Mexico, con 96 contactos combinados, produjeron 3 dossiers. Son los candidatos mas claros a recortar.", size=12.5, line=1.3)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 13 QUE CONTESTARON ============
s = blank(prs)
title(s, "Que nos dijeron", "Anatomia de las 368 respuestas con texto",
      "Clasificacion automatica de lo que contesto el prospecto y su conversion posterior")
table(s, Inches(0.7), Inches(2.2), Inches(11.9), ["Tipo de respuesta", "Casos", "Dossier", "Tasa"], [
    ["Da mail o telefono directo",          "29",  "16", "55,2%"],
    ["Pide el dossier o material",          "57",  "26", "45,6%"],
    ["Interes explicito (\"contame\", \"dale\")", "189", "64", "33,9%"],
    ["Respuesta larga y elaborada (>400 ch)", "63",  "19", "30,2%"],
    ["Deriva a otra persona del equipo",    "20",  "6",  "30,0%"],
    ["Pregunta que hacemos / que vendemos", "12",  "3",  "25,0%"],
    ["Solo cortesia (\"gracias\", \"suerte\")",  "68",  "14", "20,6%"],
    ["Propone reunion o llamada",           "15",  "3",  "20,0%"],
    ["Objecion de timing (\"mas adelante\")",  "21",  "2",  "9,5%"],
    ["Rechazo directo",                     "11",  "1",  "9,1%"],
], colw=[Inches(5.6), Inches(1.7), Inches(1.9), Inches(2.7)], rowh=Inches(0.375), size=12.5,
   colorcols={3: lambda v, r: GOOD if r < 5 else (WARN if r < 8 else BAD)})
rect(s, Inches(0.7), Inches(6.35), Inches(11.9), Inches(0.55), fill=CARD2)
tb(s, Inches(0.95), Inches(6.46), Inches(11.4), Inches(0.35),
   "La senal mas fuerte de compra es que den un mail: 55,2% termina en dossier. Es el unico momento donde hay que dejar todo y responder.",
   size=12.5, bold=True, color=GOLD)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 14 EVOLUCION DE OBJECIONES ============
s = blank(prs)
title(s, "Que nos dijeron", "Como cambiaron las respuestas mes a mes",
      "Porcentaje sobre el total de respuestas de cada mes")
table(s, Inches(0.7), Inches(2.25), Inches(11.9),
      ["Tipo de respuesta", "Junio", "Julio", "Agosto", "Septiembre", "Tendencia"], [
    ["Interes explicito",            "51,9%", "49,2%", "51,2%", "56,0%", "estable ✓"],
    ["Propone reunion o llamada",    "0,0%",  "4,0%",  "4,7%",  "12,0%", "sube ✓"],
    ["Deriva a otra persona",        "1,9%",  "4,0%",  "8,1%",  "12,0%", "sube ✓"],
    ["Pregunta que hacemos",         "0,9%",  "1,6%",  "4,7%",  "10,0%", "sube ✗"],
    ["Objecion de timing",           "5,6%",  "3,2%",  "4,7%",  "14,0%", "sube ✗"],
    ["Rechazo directo",              "2,8%",  "0,8%",  "3,5%",  "8,0%",  "sube ✗"],
    ["Solo cortesia / brush-off",    "28,7%", "14,5%", "11,6%", "18,0%", "vuelve a subir ✗"],
], colw=[Inches(3.9), Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.7), Inches(1.8)], rowh=Inches(0.4), size=12,
   colorcols={5: lambda v, r: GOOD if "✓" in str(v) else BAD})
rect(s, Inches(0.7), Inches(5.65), Inches(5.8), Inches(1.25), fill=CARD, lineclr=GOOD)
tb(s, Inches(0.95), Inches(5.8), Inches(5.3), Inches(1.0),
   "LO BUENO\nQuien contesta ahora propone reunion (12%) y deriva a la\npersona correcta (12%). Las respuestas son de mejor calidad\ncomercial que en junio.", size=11.5, line=1.3)
rect(s, Inches(6.8), Inches(5.65), Inches(5.8), Inches(1.25), fill=CARD, lineclr=BAD)
tb(s, Inches(7.05), Inches(5.8), Inches(5.3), Inches(1.0),
   "LO MALO\n10% pregunta que hacemos: el MSG1 menciona Hint pero no se\nentiende. Y la objecion de timing se triplico, senal de que el\nmensaje llega como pitch y no como consulta.", size=11.5, line=1.3)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 15 REUNIONES ============
s = blank(prs)
title(s, "Resultado final", "Las 8 reuniones del proyecto", "Siete de las ocho NO pasaron por el dossier: salieron de conversaciones sostenidas")
table(s, Inches(0.7), Inches(2.2), Inches(11.9), ["Prospecto", "Mes", "Sector", "Pais", "Genero"], [
    ["Giovanna Troncoso",     "Junio",      "Agencia / Marketing",  "—",          "Mujer"],
    ["Keylin Smith",          "Junio",      "Turismo / Eventos",    "Costa Rica", "Mujer"],
    ["Luis Perez (Foamtec)",  "Junio",      "Industria",            "Mexico",     "Hombre"],
    ["Alejandra Salas Petit", "Julio",      "Comunicacion",         "Espana",     "Mujer"],
    ["Ana Beatriz Estrada",   "Julio",      "Servicios",            "Panama",     "Mujer"],
    ["Silvia Rojas",          "Julio",      "Retail / E-commerce",  "Costa Rica", "Mujer"],
    ["Luis A. Baquero Franco","Agosto",     "Tecnologia / SaaS",    "Colombia",   "Hombre"],
    ["Analia Angulo Rodriguez","Septiembre","Consultoria Marketing","Argentina",  "Mujer"],
], colw=[Inches(3.6), Inches(1.9), Inches(3.1), Inches(1.9), Inches(1.4)], rowh=Inches(0.4), size=12.5)
y = Inches(5.75)
for i, (big, lab, col) in enumerate([("7 de 8", "NO pasaron por dossier", BAD), ("6 de 8", "Fueron mujeres", GOOD),
                                     ("5 de 8", "Salieron de conversar", GOOD), ("0,73%", "Contacto → reunion", WARN)]):
    x = Inches(0.7) + i * Inches(3.05)
    rect(s, x, y, Inches(2.85), Inches(1.1), fill=CARD)
    tb(s, x + Inches(0.22), y + Inches(0.14), Inches(2.5), Inches(0.45), big, size=26, bold=True, color=col)
    tb(s, x + Inches(0.22), y + Inches(0.68), Inches(2.5), Inches(0.35), lab, size=10.5, color=MUT)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 16 BENCHMARK ============
s = blank(prs)
title(s, "Contexto de mercado", "Como estamos contra el benchmark del sector",
      "Datos publicos 2026 de Belkins, Expandi y Overloop sobre outreach B2B en LinkedIn")
table(s, Inches(0.7), Inches(2.25), Inches(11.9),
      ["Metrica", "Benchmark mercado", "Hint junio", "Hint septiembre", "Lectura"], [
    ["Respuesta post-conexion", "7,2% - 10,4%", "75,6%", "15,9%", "Seguimos arriba"],
    ["Mensaje personalizado",   "9,4%",         "75,6%", "15,9%", "Seguimos arriba"],
    ["Reunion (cold 1:muchos)", "0,8% - 2,5%",  "1,74%", "0,32%", "Caimos al piso"],
    ["Reunion (1:1 tipo ABM)",  "4% - 8%",      "1,74%", "0,32%", "Muy por debajo"],
    ["Toques hasta la reunion", "6 a 12",       "~3",    "~1",    "Critico"],
], colw=[Inches(3.3), Inches(2.6), Inches(1.9), Inches(2.2), Inches(1.9)], rowh=Inches(0.45), size=12.5,
   colorcols={4: lambda v, r: GOOD if r < 2 else BAD})
rect(s, Inches(0.7), Inches(4.85), Inches(5.8), Inches(1.9), fill=CARD, lineclr=GOOD)
tb(s, Inches(0.95), Inches(5.02), Inches(5.3), Inches(1.6),
   "LA BUENA NOTICIA\n\nIncluso en su peor mes, Hint Media responde 15,9%: entre\n1,5x y 2x el benchmark del mercado (7,2% - 10,4%).\n\nEl metodo de analisis previo funciona. El problema no es\nla calidad del research, es como se convierte en mensaje.",
   size=12, line=1.35)
rect(s, Inches(6.8), Inches(4.85), Inches(5.8), Inches(1.9), fill=CARD, lineclr=BAD)
tb(s, Inches(7.05), Inches(5.02), Inches(5.3), Inches(1.6),
   "LA MALA NOTICIA\n\nHint hace trabajo de calidad ABM (analisis individual,\nsenal humana, hipotesis) y cobra resultado de spray-and-pray.\n\nLa razon es unica: un solo toque. El mercado necesita entre\n6 y 12 para agendar. Ahi se pierde todo el esfuerzo previo.",
   size=12, line=1.35)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 17 CURIOSIDADES ============
s = blank(prs)
title(s, "Hallazgos", "Curiosidades del trimestre", "Cosas que los datos dicen y no se ven en el dia a dia")
items = [
    ("El analisis previo predice el resultado",
     "Los contactos con Confidence HIGH en el .md convierten 11,0% a dossier. Los MEDIUM, 4,2%. Los LOW, 0%. "
     "Cuando el analisis duda, el mensaje no funciona: conviene descartar el contacto antes que escribirlo."),
    ("Las mejores charlas no dejaron plata",
     "Las 8 respuestas mas largas del proyecto (hasta 3.042 caracteres) terminaron todas SIN dossier. "
     "Conversaciones excelentes que nunca se pidieron avanzar."),
    ("El angulo del mensaje casi no importa",
     "Publicacion, frase textual, logro o trayectoria rinden todos entre 37% y 41%. Lo que cambia el resultado "
     "es el CTA y si mencionas Hint, no de donde sacaste la senal."),
    ("Coordinadores: el espejismo",
     "66,7% de respuesta, la mas alta de todas las jerarquias, y 0% de dossier sobre 18 casos. Conversan encantados y no deciden nada."),
    ("Septiembre produjo cero SEG1",
     "Primera vez en el proyecto. En junio se mandaron 48. El follow-up no se degrado: se apago."),
]
bullets(s, Inches(0.7), Inches(2.25), Inches(11.9), items, size=14, gap=Inches(0.62), dotclr=GOLD, sub_size=11.5)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

# ============ 18 CONCLUSION ============
s = blank(prs)
title(s, "Conclusion", "Que dice septiembre")
rect(s, Inches(0.7), Inches(2.0), Inches(11.9), Inches(1.2), fill=CARD, lineclr=ACC)
tb(s, Inches(1.0), Inches(2.2), Inches(11.4), Inches(0.9),
   "El motor de investigacion de Hint Media funciona y esta muy por encima del mercado.\n"
   "Lo que se rompio en agosto y septiembre fue la capa de conversion: el mensaje y el seguimiento.",
   size=16, bold=True, line=1.35)
left = [("1. El CTA", "Volver a \"tenia una consulta\". 57,3% vs 15,9%."),
        ("2. Hint fuera del MSG1", "59,1% vs 16,0% de respuesta."),
        ("3. Mensajes de 60 palabras", "67,6% vs 15,4% en los de 120+."),
        ("4. Seguimiento obligatorio", "De 1 toque a 6. Es el unico camino a la reunion.")]
right = [("5. Menos volumen, mejor lista", "42% de la base esta en los 3 peores sectores."),
         ("6. Recuperar el mix femenino", "41,6% vs 31,4% de respuesta. 6 de 8 reuniones."),
         ("7. Apuntar al C-Level funcional", "57,1% responde. El CEO en frio, 25,2%."),
         ("8. Rescatar los 97 leads quemados", "Ya respondieron. Estan sin tocar.")]
tb(s, Inches(0.7), Inches(3.5), Inches(5.8), Inches(0.3), "LAS OCHO CORRECCIONES", size=11, color=ACC, bold=True)
bullets(s, Inches(0.7), Inches(3.9), Inches(5.7), left, size=13, gap=Inches(0.55), dotclr=GOOD, sub_size=11)
bullets(s, Inches(6.9), Inches(3.9), Inches(5.7), right, size=13, gap=Inches(0.55), dotclr=GOOD, sub_size=11)
footer(s, "Hint Media · Informe Septiembre 2026", nx() + 1)

out = r"C:/Users/neces/Desktop/CLAUDE/Linkedin/SEPTIEMBRE INFORME/Informe_Septiembre_2026_Analisis.pptx"
os.makedirs(os.path.dirname(out), exist_ok=True)
prs.save(out)
print("OK ->", out, "| slides:", len(prs.slides.__iter__.__self__._sldIdLst))
