# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scratchpad'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import *
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

prs = new_deck()
N = [0]
def nx():
    N[0] += 1
    return N[0]

def pill(slide, x, y, txt, color=ACC, w=Inches(1.5)):
    sh = rect(slide, x, y, w, Inches(0.3), fill=color)
    tb(slide, x, y + Inches(0.03), w, Inches(0.25), txt, size=9.5, bold=True, color=BG, align=PP_ALIGN.CENTER)
    return sh

# ============ 1 PORTADA ============
s = blank(prs)
rect(s, Inches(0), Inches(0), Inches(0.14), H, fill=GOLD, radius=False)
tb(s, Inches(0.9), Inches(1.4), Inches(8), Inches(0.3), "HINT MEDIA  ·  PLAN DE ACCION", size=12, color=GOLD, bold=True)
tb(s, Inches(0.9), Inches(1.9), Inches(11.5), Inches(2.0), "Como conseguir\nmas reuniones", size=52, bold=True, line=1.05)
tb(s, Inches(0.9), Inches(3.9), Inches(10.5), Inches(0.9),
   "Diagnostico, correcciones inmediatas, ideas nuevas y herramientas\npara pasar de 1 reunion por mes a 8-12", size=19, color=MUT, line=1.35)
rect(s, Inches(0.9), Inches(5.1), Inches(1.5), Pt(3), fill=GOLD, radius=False)
tb(s, Inches(0.9), Inches(5.5), Inches(11), Inches(0.9),
   "\"No tenemos un problema de generacion de leads.\nTenemos un problema de conversion de leads que ya tenemos.\"", size=17, color=TXT, italic=True, line=1.35)
tb(s, Inches(0.9), Inches(6.8), Inches(8), Inches(0.3), "20 de septiembre de 2026", size=10, color=MUT)

# ============ 2 LA TESIS ============
s = blank(prs)
title(s, "El diagnostico", "El dinero ya esta sobre la mesa. No lo estamos levantando.")
y = Inches(2.1)
for i, (big, lab, sub, col) in enumerate([
    ("97", "leads que respondieron", "y nunca recibieron\nun segundo mensaje", BAD),
    ("82", "dossiers enviados", "que nunca recibieron\nun follow-up", BAD),
    ("773", "contactos", "que recibieron un solo\nmensaje en toda su vida", WARN),
    ("952", "personas", "ya contactadas y\nsin agotar", GOLD)]):
    x = Inches(0.7) + i * Inches(3.05)
    rect(s, x, y, Inches(2.85), Inches(1.85), fill=CARD, lineclr=col)
    tb(s, x + Inches(0.22), y + Inches(0.18), Inches(2.5), Inches(0.55), big, size=38, bold=True, color=col)
    tb(s, x + Inches(0.22), y + Inches(0.82), Inches(2.5), Inches(0.35), lab, size=12, bold=True)
    tb(s, x + Inches(0.22), y + Inches(1.18), Inches(2.5), Inches(0.6), sub, size=10, color=MUT, line=1.25)
rect(s, Inches(0.7), Inches(4.25), Inches(11.9), Inches(1.0), fill=CARD2)
tb(s, Inches(1.0), Inches(4.42), Inches(11.4), Inches(0.75),
   "Antes de contactar a una sola persona nueva, hay 179 conversaciones tibias sin cerrar.\n"
   "A la tasa historica de dossier-a-reunion mejorada, ese stock solo ya vale entre 6 y 10 reuniones.",
   size=14.5, bold=True, color=GOLD, line=1.3)
bullets(s, Inches(0.7), Inches(5.5), Inches(11.9), [
    ("El error de septiembre fue optimizar la parte equivocada",
     "Se duplico el volumen de entrada (172 → 315 contactos) mientras se abandonaba la salida. Es llenar un balde agujereado mas rapido."),
], size=14, dotclr=BAD, sub_size=12)
footer(s, "Hint Media · Plan de accion", nx() + 1)

# ============ 3 FIX 1: EL MENSAJE ============
s = blank(prs)
title(s, "Correccion inmediata  ·  1", "Rollback del MSG1: volver a lo que funcionaba",
      "Cuatro cambios concretos con impacto medido sobre 1.102 casos")
hdrs = ["", "Como esta hoy", "Como debe ser", "Impacto medido"]
table(s, Inches(0.7), Inches(2.25), Inches(11.9), hdrs, [
    ["Saludo de apertura", "\"Buenas [nombre]!\"", "\"[Nombre], gracias por conectar!\"", "18,2% → 66,2%"],
    ["Segunda linea", "Interpretacion del perfil", "\"Me llamo la atencion\" + cita textual", "27% → 54%"],
    ["Mencion de Hint", "Hint aparece en el MSG1", "Hint recien en el MSG2", "16,0% → 59,1%"],
    ["Cierre", "\"Vale la pena que te cuente...\"", "Oferta concreta de un caso", "0,34% → 0,85% reunion"],
], colw=[Inches(2.5), Inches(3.4), Inches(3.5), Inches(2.5)], rowh=Inches(0.52), size=12.5,
   colorcols={3: lambda v, r: GOOD})
rect(s, Inches(0.7), Inches(4.65), Inches(5.8), Inches(2.2), fill=CARD, lineclr=BAD)
tb(s, Inches(0.95), Inches(4.8), Inches(5.3), Inches(0.3), "HOY  ·  18% responde", size=10.5, color=BAD, bold=True)
tb(s, Inches(0.95), Inches(5.2), Inches(5.3), Inches(1.5),
   "Buenas Maleka, tu enfoque en la transicion energetica me\nquedo dando vueltas. No es lo que tipicamente escucha un\nejecutivo de comercializacion.\n\n"
   "En Hint Media trabajamos con lideres comerciales en energia\ncomo TGS y Transener en hacer legible esa innovacion...\n\n"
   "Vale la pena que te cuente como lo trabajamos?", size=9.5, color=MUT, line=1.3)
rect(s, Inches(6.8), Inches(4.65), Inches(5.8), Inches(2.2), fill=CARD, lineclr=GOOD)
tb(s, Inches(7.05), Inches(4.8), Inches(5.3), Inches(0.3), "PROPUESTO  ·  66% responde", size=10.5, color=GOOD, bold=True)
tb(s, Inches(7.05), Inches(5.2), Inches(5.3), Inches(1.5),
   "Maleka, gracias por conectar!\nMe llamo la atencion que te presentes desde la transicion\nenergetica y no desde la cartera, estando en comercializacion.\n\n"
   "En Hint Media hacemos la comunicacion de TGS y Transener.\nCon Transener trabajamos la voceria de su gerencia.\n\n"
   "Es el caso mas parecido a lo que haces vos. Te lo comparto?", size=9.5, color=TXT, line=1.3)
footer(s, "Hint Media · Plan de accion", nx() + 1)

# ============ 4 FIX 2: SECUENCIA ============
s = blank(prs)
title(s, "Correccion inmediata  ·  2", "Tres toques en LinkedIn, no uno. Y no mas de tres.",
      "Medido sobre 13,2 millones de mensajes de LinkedIn (Expandi, 2026)")
table(s, Inches(0.7), Inches(2.3), Inches(11.9), ["Cantidad de toques", "Efecto sobre la respuesta", "Lectura"], [
    ["1 mensaje (lo que hacemos hoy)", "base", "93,7% de septiembre quedo aca"],
    ["+ primer follow-up", "-0,6%", "Rinde peor que no mandar nada"],
    ["+ segundo follow-up", "+4,05%", "Aca esta todo el valor"],
    ["3 mensajes en total", "9,8% de respuesta", "El optimo"],
    ["5 o mas", "5,0%", "Peor que un solo mensaje"],
], colw=[Inches(4.3), Inches(3.6), Inches(4.0)], rowh=Inches(0.5), size=13,
   colorcols={1: lambda v, r: [MUT, BAD, GOOD, GOOD, BAD][r]})
rect(s, Inches(0.7), Inches(5.1), Inches(5.8), Inches(1.75), fill=CARD, lineclr=BAD)
tb(s, Inches(0.95), Inches(5.28), Inches(5.3), Inches(1.5),
   "CORRECCION DE ESTE INFORME\n\nLa version anterior recomendaba 7 toques citando el\nbenchmark de 6 a 12. Ese numero es MULTICANAL:\nLinkedIn mas mail mas telefono.\n\nDentro de LinkedIn solo, pasar de 3 destruye.", size=12, line=1.35)
rect(s, Inches(6.8), Inches(5.1), Inches(5.8), Inches(1.75), fill=CARD, lineclr=GOOD)
tb(s, Inches(7.05), Inches(5.28), Inches(5.3), Inches(1.5),
   "LA SECUENCIA\n\nT1  dia 0     Primer mensaje, sin pitch\nT2  dia 3-4   Angulo nuevo, nunca repetir el valor\nT3  dia 10    Propuesta de conversacion\n\nDespues del tercero: mail, no mas LinkedIn.", size=12, line=1.35)
footer(s, "Hint Media · Plan de accion", nx() + 1)

# ============ 5 FIX 3: EL DOSSIER ES UNA TRAMPA ============
s = blank(prs)
title(s, "Correccion inmediata  ·  3", "El dossier es un callejon sin salida",
      "108 dossiers enviados produjeron 1 reunion. Es el paso donde muere el embudo.")
bars(s, Inches(0.7), Inches(2.4), Inches(11.9), Inches(1.5), [
    ("Contactados", 1102, MUT), ("Respondieron", 366, ACC),
    ("Dossier enviado", 108, WARN), ("Reunion", 8, BAD),
], maxv=1150, fmt="%.0f", barh=Inches(0.32), gap=Inches(0.12), labw=Inches(2.3), valw=Inches(1.0))
rect(s, Inches(0.7), Inches(4.2), Inches(5.8), Inches(1.5), fill=CARD, lineclr=BAD)
tb(s, Inches(0.95), Inches(4.38), Inches(5.3), Inches(1.2),
   "EL PROBLEMA\n\nEl dossier le da al prospecto una excusa perfecta para\ndecir \"lo reviso y te aviso\". Y ahi termina la conversacion.\nNadie vuelve por su cuenta.", size=12, line=1.35)
rect(s, Inches(6.8), Inches(4.2), Inches(5.8), Inches(1.5), fill=CARD, lineclr=GOOD)
tb(s, Inches(7.05), Inches(4.38), Inches(5.3), Inches(1.2),
   "LA CORRECCION\n\nEl dossier nunca viaja solo. Siempre acompanado de una\npregunta que exige respuesta, o directamente reemplazado\npor la propuesta de 15 minutos.", size=12, line=1.35)
rect(s, Inches(0.7), Inches(5.95), Inches(11.9), Inches(0.95), fill=CARD2)
tb(s, Inches(0.95), Inches(6.1), Inches(11.4), Inches(0.7),
   "Nuevo cierre propuesto:  \"Te mando el dossier, pero te soy honesta: en 15 minutos te lo explico mejor de lo que lo lee cualquiera.\n"
   "Martes 10h o jueves 16h, que te sirve mas?\"   →   opcion concreta, no pregunta abierta.", size=13, bold=True, color=GOLD, line=1.3)
footer(s, "Hint Media · Plan de accion", nx() + 1)

# ============ 6 IDEAS NUEVAS 1 ============
s = blank(prs)
title(s, "Ideas nuevas  ·  1 de 2", "Cosas que no estamos haciendo y mueven la aguja")
items = [
    ("Multicanal: LinkedIn + mail  ·  impacto 3-4x",
     "Las secuencias coordinadas multicanal rinden 3-4x mas que un solo canal (287% mas engagement). Ya tenemos 14 mails capturados en historial.json que no se usan sistematicamente. Cada vez que alguien da su mail, debe entrar a una secuencia paralela."),
    ("Warm-up antes del MSG1  ·  impacto en aceptacion",
     "El targeting por senal rinde 40-60% de aceptacion vs 10-20% de lista fria. Comentar dos posts del prospecto en los 5 dias previos al MSG1 convierte la lista fria en lista tibia. Cero costo, solo orden."),
    ("Invertir dossier y reunion",
     "Hoy: dossier → (silencio) → reunion. Propuesto: reunion de 15 min → dossier como material de la reunion. El dossier deja de ser la meta y pasa a ser la excusa para el encuentro."),
    ("Sistematizar el referido  ·  ya pasa solo el 12%",
     "12% de las respuestas de septiembre derivan a otra persona sin que se lo pidamos. Si se pide explicitamente en el toque 6, ese numero sube. Es el canal mas barato que tenemos y esta sin explotar."),
]
bullets(s, Inches(0.7), Inches(2.2), Inches(11.9), items, size=14.5, gap=Inches(0.72), dotclr=GOLD, sub_size=11.5)
footer(s, "Hint Media · Plan de accion", nx() + 1)

# ============ 7 IDEAS NUEVAS 2 ============
s = blank(prs)
title(s, "Ideas nuevas  ·  2 de 2", "Las que nadie propuso todavia")
items = [
    ("El saludo vale 3 veces mas que cualquier otra correccion",
     "Abrir con el nombre y gracias por conectar rinde 66,2 por ciento de respuesta; abrir con Buenas rinde entre 10 y 18. El efecto se confirma mes por mes. Es un cambio de cuatro palabras."),
    ("Campana de resurreccion sobre 773 contactos",
     "Los contactos de un solo toque no estan muertos, estan sin trabajar. Un mensaje de reactivacion con angulo nuevo sobre esa base, sin gastar una sola conexion nueva, es la accion de mayor retorno disponible hoy."),
    ("Dejar de escribirle a CEOs en frio",
     "25,2% de respuesta y 5,4% de dossier, el peor de todos los niveles. El C-Level funcional (CTO, CFO, CMO) responde 57,1% y pide dossier 14,3%. Mismo esfuerzo, mas del doble de retorno."),
    ("Matar tres sectores y doblar apuesta en dos",
     "Tecnologia, Mineria y Construccion son 463 contactos (42% de la base) y 27 dossiers. Consultoria/RRHH y Salud son 72 contactos y 12 dossiers. Reasignar ese volumen vale mas que cualquier mejora de copy."),
    ("Un solo numero en el tablero: reuniones agendadas",
     "Hoy el sistema celebra dossiers enviados. Es una metrica de actividad, no de resultado, y explica por que 82 se quedaron sin follow-up: ya habian cumplido su funcion en el tablero."),
]
bullets(s, Inches(0.7), Inches(2.15), Inches(11.9), items, size=14, gap=Inches(0.6), dotclr=ACC, sub_size=11)
footer(s, "Hint Media · Plan de accion", nx() + 1)

# ============ 8 MEJORAS AL PROGRAMA ============
s = blank(prs)
title(s, "El sistema", "Mejoras al programa que usamos",
      "Cambios concretos en servidor.py, index.html, historial.json y el watcher")
col1 = [
    ("Alertas de vencimiento automaticas",
     "El watcher ya detecta cambios de stage. Debe ademas marcar en rojo todo contacto con dossier enviado hace mas de 3 dias sin SEG1. Hoy no avisa nada y por eso se perdieron 82."),
    ("Secuencia obligatoria, no opcional",
     "El programa deberia negarse a generar un MSG1 nuevo si hay mas de N contactos con follow-up vencido. Forzar el orden correcto por diseno, no por disciplina."),
    ("Campo de proxima accion + fecha",
     "historial.json tiene stage pero no tiene 'proximo toque'. Sin ese campo el sistema no puede recordarnos nada."),
]
col2 = [
    ("Validador de mensaje antes de enviar",
     "Chequeo automatico: cuenta palabras (rechaza +65), detecta 'Hint' en MSG1, detecta frases de la blocklist y verifica que el cliente citado corresponda al sector. Los errores de cliente-fuera-de-sector se repitieron todo el trimestre."),
    ("Dashboard con embudo real",
     "Hoy el tablero muestra contactos y dossiers. Debe mostrar: respuestas sin MSG2, dossiers sin SEG1 y reuniones. Las tres cosas que importan."),
    ("Registro del toque, no solo del stage",
     "Guardar cuantos toques recibio cada contacto permite medir la secuencia. Hoy es imposible saberlo sin parsear los .md."),
]
tb(s, Inches(0.7), Inches(2.15), Inches(5.8), Inches(0.3), "URGENTE", size=11, color=BAD, bold=True)
bullets(s, Inches(0.7), Inches(2.5), Inches(5.7), col1, size=13, gap=Inches(0.66), dotclr=BAD, sub_size=10.5)
tb(s, Inches(6.9), Inches(2.15), Inches(5.8), Inches(0.3), "IMPORTANTE", size=11, color=ACC, bold=True)
bullets(s, Inches(6.9), Inches(2.5), Inches(5.7), col2, size=13, gap=Inches(0.66), dotclr=ACC, sub_size=10.5)
footer(s, "Hint Media · Plan de accion", nx() + 1)

# ============ 8b LA CHARLA VS EL DOSSIER ============
s = blank(prs)
title(s, "Hallazgo", "La conversacion convierte 7 veces mas que el dossier",
      "Siete de las ocho reuniones del proyecto NO pasaron por el dossier")
bars(s, Inches(0.7), Inches(2.45), Inches(11.9), Inches(1.3), [
    ("Hubo conversacion real", 6.7, GOOD), ("Se mando el dossier", 0.9, BAD),
], maxv=7.5, barh=Inches(0.5), gap=Inches(0.28), labw=Inches(3.4), valw=Inches(1.0))
tb(s, Inches(0.7), Inches(2.1), Inches(8), Inches(0.3), "TASA DE REUNION SEGUN EL CAMINO", size=11, color=ACC, bold=True)
y = Inches(4.25)
for i, (big, lab, sub, col) in enumerate([
    ("66", "respondieron DESPUES\nde recibir el dossier", "no desaparecieron:\ncontestaron", WARN),
    ("1", "de esos 66 termino\nen reunion", "nadie propuso\nuna conversacion", BAD),
    ("7 de 8", "reuniones NO pasaron\npor el dossier", "salieron de conversar", GOOD),
    ("38", "dieron mail o telefono", "la senal de compra\nmas fuerte de la base", GOLD)]):
    x = Inches(0.7) + i * Inches(3.05)
    rect(s, x, y, Inches(2.85), Inches(1.8), fill=CARD, lineclr=col)
    tb(s, x + Inches(0.22), y + Inches(0.16), Inches(2.5), Inches(0.5), big, size=30, bold=True, color=col)
    tb(s, x + Inches(0.22), y + Inches(0.74), Inches(2.5), Inches(0.5), lab, size=11, bold=True, line=1.15)
    tb(s, x + Inches(0.22), y + Inches(1.24), Inches(2.5), Inches(0.5), sub, size=9.5, color=MUT, line=1.2)
rect(s, Inches(0.7), Inches(6.3), Inches(11.9), Inches(0.6), fill=CARD2)
tb(s, Inches(0.95), Inches(6.42), Inches(11.4), Inches(0.4),
   "El dossier no es un paso hacia la reunion. Es el paso que la reemplaza: llega el PDF, el prospecto agradece y el hilo muere con buen clima.",
   size=12.5, bold=True, color=GOLD)
footer(s, "Hint Media · Plan de accion", nx() + 1)

# ============ 8c LANGUAGE BANK ============
s = blank(prs)
title(s, "La herramienta", "Hint Language Bank",
      "En vez de describirle el estilo al modelo, se lo mostramos con los mensajes que funcionaron")
bullets(s, Inches(0.7), Inches(2.25), Inches(5.9), [
    ("El problema que resuelve",
     "Un ejemplo mal etiquetado como correcto produjo 159 mensajes identicos. El modelo copia los ejemplos antes que las reglas."),
    ("De donde sale",
     "De las 1.102 conversaciones propias, clasificadas por resultado verificado: reunion, contacto, conversacion o fracaso."),
    ("Que contiene",
     "Los mensajes reales de las 8 reuniones y los 38 contactos, con la respuesta textual del prospecto al lado."),
], size=13.5, gap=Inches(0.66), dotclr=GOLD, sub_size=11)
rect(s, Inches(7.0), Inches(2.25), Inches(5.6), Inches(2.05), fill=CARD, lineclr=GOOD)
tb(s, Inches(7.25), Inches(2.42), Inches(5.1), Inches(0.3), "APARECEN EN LOS QUE FUNCIONARON", size=10, color=GOOD, bold=True)
tb(s, Inches(7.25), Inches(2.78), Inches(5.1), Inches(1.4),
   "me llamo la atencion  ·  gracias por conectar\nqueria saber  ·  me podias ayudar\nescribiste  ·  pusiste  ·  publicacion\n\nPalabras de lectura real y de pedido.\nNinguna es de venta.", size=11, line=1.35)
rect(s, Inches(7.0), Inches(4.5), Inches(5.6), Inches(2.35), fill=CARD, lineclr=BAD)
tb(s, Inches(7.25), Inches(4.67), Inches(5.1), Inches(0.3), "APARECEN SOLO EN LOS QUE MURIERON", size=10, color=BAD, bold=True)
tb(s, Inches(7.25), Inches(5.03), Inches(5.1), Inches(1.7),
   "credibilidad  ·  presencia  ·  solucion\nconstruimos  ·  resolvemos  ·  escale\ncomplejo  ·  mercados  ·  narrativa\n\n\"mientras\" esta en 0% de los que\nfuncionaron y 10% de los que fallaron:\nes el marcador de la frase larga.", size=11, line=1.35)
footer(s, "Hint Media · Plan de accion", nx() + 1)

# ============ 9 REPOS GITHUB ============
s = blank(prs)
title(s, "Herramientas", "Que esta haciendo el resto del mundo",
      "Proyectos open source de prospeccion y outreach relevantes para nuestro stack")
table(s, Inches(0.7), Inches(2.2), Inches(11.9),
      ["Proyecto", "Que es", "Por que nos sirve"], [
    ["impecablemee/gtm-mcp", "Pipeline B2B cold outreach\npara Claude Code (MCP)", "El mas parecido a lo nuestro. Un comando\nbusca, clasifica y escribe secuencias."],
    ["coldoutboundskills", "30 skills de Claude Code\npara cold outbound", "Skills ya hechas para calificar campanas\ny armar ICP. Directamente reutilizable."],
    ["moaljumaa/linki", "AI SDR self-hosted,\nsecuencias multicanal", "Resuelve exactamente nuestro agujero:\nsecuencias LinkedIn + mail coordinadas."],
    ["tajbaka/OpenOutreach", "LinkedIn + Postgres +\nCRM sobre Google Sheets", "Modelo de 'People ledger' durable.\nMejor que nuestro historial.json plano."],
    ["YALC", "Alternativa open source a\nClay, corre en Claude Code", "Enriquecimiento de leads y scoring ICP\nsin pagar Clay ni Apollo."],
], colw=[Inches(3.2), Inches(3.8), Inches(4.9)], rowh=Inches(0.72), size=11.5)
rect(s, Inches(0.7), Inches(6.2), Inches(11.9), Inches(0.68), fill=CARD2)
tb(s, Inches(0.95), Inches(6.33), Inches(11.4), Inches(0.45),
   "Lectura: el mercado open source resolvio la parte de volumen y secuenciacion. Nuestra ventaja real es la calidad del analisis previo,\n"
   "que ninguna de estas herramientas tiene. Conviene tomarles la mecanica de secuencias, no el criterio de mensaje.", size=11.5, color=GOLD, line=1.3)
footer(s, "Hint Media · Plan de accion", nx() + 1)

# ============ 10 ROADMAP ============
s = blank(prs)
title(s, "Ejecucion", "Plan de 30 / 60 / 90 dias")
blocks = [
    ("ESTA SEMANA", BAD, [
        "Rollback del MSG1: CTA, sin Hint, 60 palabras",
        "SEG1 a los 82 dossiers sin follow-up",
        "MSG2 a los 97 leads que respondieron",
        "Commitear los 40 .md de septiembre sin guardar",
        "Enviar los 5 dossiers por mail pendientes"]),
    ("30 DIAS", WARN, [
        "Secuencia de 7 toques implementada en el programa",
        "Alerta automatica de follow-up vencido",
        "Validador de mensaje antes de enviar",
        "Reasignar volumen: menos tech/mineria, mas consultoria/salud",
        "Campana de resurreccion sobre 773 contactos"]),
    ("60-90 DIAS", GOOD, [
        "Secuencia multicanal LinkedIn + mail",
        "Warm-up sistematico antes del MSG1",
        "Notas de voz en el toque 5",
        "Dashboard con embudo real y reuniones como KPI unico",
        "Programa de referidos explicito"]),
]
for i, (t, col, its) in enumerate(blocks):
    x = Inches(0.7) + i * Inches(4.07)
    rect(s, x, Inches(2.15), Inches(3.85), Inches(4.3), fill=CARD, lineclr=col)
    pill(s, x + Inches(0.25), Inches(2.35), t, color=col, w=Inches(1.7))
    cy = Inches(2.9)
    for it in its:
        rect(s, x + Inches(0.28), cy + Inches(0.08), Inches(0.08), Inches(0.08), fill=col)
        tb(s, x + Inches(0.5), cy, Inches(3.1), Inches(0.7), it, size=11, line=1.3)
        cy += Inches(0.68)
footer(s, "Hint Media · Plan de accion", nx() + 1)

# ============ 11 PROYECCION ============
s = blank(prs)
title(s, "El objetivo", "Que pasa si hacemos esto",
      "Proyeccion sobre el mismo volumen de septiembre (315 contactos), sin gastar una conexion mas")
table(s, Inches(0.7), Inches(2.3), Inches(11.9),
      ["Metrica", "Septiembre real", "Solo rollback del mensaje", "Rollback + secuencia 7 toques"], [
    ["Respuestas",      "50",   "110 - 140", "110 - 140"],
    ["MSG2 enviados",   "20",   "100 - 130", "110 - 140"],
    ["Dossiers",        "10",   "30 - 39",   "35 - 45"],
    ["Reuniones",       "1",    "2 - 3",     "8 - 12"],
], colw=[Inches(3.0), Inches(2.8), Inches(3.0), Inches(3.1)], rowh=Inches(0.55), size=14,
   colorcols={1: lambda v, r: BAD, 2: lambda v, r: WARN, 3: lambda v, r: GOOD})
rect(s, Inches(0.7), Inches(4.75), Inches(5.8), Inches(1.35), fill=CARD, lineclr=WARN)
tb(s, Inches(0.95), Inches(4.92), Inches(5.3), Inches(1.1),
   "Arreglar solo el mensaje recupera el volumen de\nconversaciones, pero casi no mueve las reuniones.\n\nEl mensaje abre la puerta. No la cruza.", size=12.5, line=1.35)
rect(s, Inches(6.8), Inches(4.75), Inches(5.8), Inches(1.35), fill=CARD, lineclr=GOOD)
tb(s, Inches(7.05), Inches(4.92), Inches(5.3), Inches(1.1),
   "La secuencia de 7 toques es lo que multiplica\nlas reuniones por 8-12.\n\nEs la unica correccion que toca el numero que importa.", size=12.5, line=1.35)
rect(s, Inches(0.7), Inches(6.3), Inches(11.9), Inches(0.62), fill=CARD2)
tb(s, Inches(0.95), Inches(6.42), Inches(11.4), Inches(0.4),
   "Base de calculo: tasas historicas propias (junio-julio) para el mensaje, y benchmark de mercado 1:1 ABM (4-8%) para la secuencia completa.",
   size=11, color=MUT)
footer(s, "Hint Media · Plan de accion", nx() + 1)

# ============ 12 CIERRE ============
s = blank(prs)
rect(s, Inches(0), Inches(0), Inches(0.14), H, fill=GOLD, radius=False)
tb(s, Inches(0.9), Inches(1.3), Inches(8), Inches(0.3), "SI SOLO SE HACEN TRES COSAS", size=12, color=GOLD, bold=True)
tb(s, Inches(0.9), Inches(1.8), Inches(11), Inches(0.8), "Las tres que importan", size=42, bold=True)
tres = [
    ("1", "Devolver el MSG1 a como era en junio", "CTA \"tenia una consulta\", sin Hint, 60 palabras. Es gratis y vale 3,6x en respuesta."),
    ("2", "Nadie sale del sistema con un solo toque", "Siete toques o una negativa explicita. Es lo unico que convierte conversaciones en reuniones."),
    ("3", "Trabajar los 179 leads tibios antes de buscar uno nuevo", "97 respondieron sin seguimiento y 82 tienen dossier sin follow-up. Ese stock ya esta pago."),
]
y = Inches(3.0)
for num, t, sub in tres:
    rect(s, Inches(0.9), y, Inches(0.72), Inches(0.72), fill=GOLD)
    tb(s, Inches(0.9), y + Inches(0.12), Inches(0.72), Inches(0.5), num, size=26, bold=True, color=BG, align=PP_ALIGN.CENTER)
    tb(s, Inches(1.85), y + Inches(0.02), Inches(10.5), Inches(0.4), t, size=19, bold=True)
    tb(s, Inches(1.85), y + Inches(0.42), Inches(10.5), Inches(0.4), sub, size=12.5, color=MUT)
    y += Inches(1.15)
rect(s, Inches(0.9), Inches(6.5), Inches(11.5), Pt(2.5), fill=CARD2, radius=False)
tb(s, Inches(0.9), Inches(6.75), Inches(11), Inches(0.4),
   "Hint Media  ·  LinkedIn Outreach  ·  Septiembre 2026", size=11, color=MUT)

out = r"C:/Users/neces/Desktop/CLAUDE/Linkedin/SEPTIEMBRE INFORME/Plan_Mas_Reuniones_2026.pptx"
os.makedirs(os.path.dirname(out), exist_ok=True)
prs.save(out)
print("OK ->", out)
