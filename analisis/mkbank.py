# -*- coding: utf-8 -*-
"""Genera HINT_LANGUAGE_BANK.md a partir de los datos reales."""
import os, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"C:/Users/neces/Desktop/CLAUDE/Linkedin/HINT_LANGUAGE_BANK.md"
d = json.load(open(os.path.join(HERE, 'bank_raw.json'), encoding='utf-8'))
bank = d['bank']


def fmt(e, con_resp=True, lim=460):
    s = "**%s** · %s · %s · %s · %d palabras\n\n" % (
        e['nombre'], e['sector'], e['pais'], e['mes'], e['palabras'])
    m = re.sub(r'\n+', '\n> ', e['msg1'][:lim].strip())
    s += "> " + m + "\n"
    if con_resp and e['resp']:
        r = re.sub(r'\s+', ' ', e['resp'])[:230]
        s += "\nContestó: *\"%s\"*\n" % r
    return s


L = []
w = L.append
w("# HINT LANGUAGE BANK")
w("")
w("Extraído de 1.102 conversaciones reales (junio a septiembre 2026). Cada ejemplo está clasificado por")
w("**resultado verificado**, no por opinión. Esta es la fuente de verdad sobre cómo escribe Florencia")
w("cuando consigue algo.")
w("")
w("**Cómo usarlo:** los ejemplos de este archivo pesan más que cualquier regla abstracta del prompt.")
w("Un modelo chico copia el ejemplo antes que la instrucción. Por eso acá sólo hay mensajes que")
w("consiguieron un resultado medible, y los que fallaron están marcados como tales.")
w("")
w("| Resultado | Casos |")
w("|---|---|")
w("| Reunión agendada | 8 |")
w("| Dieron mail o teléfono | 33 |")
w("| Conversación sostenida | 62 |")
w("| Pidieron dossier y ahí murió | 70 |")
w("| Respondieron y murió | 239 |")
w("| Sin respuesta | 690 |")
w("")
w("---")
w("")
w("## 1. La fórmula que más resultados consiguió")
w("")
w("Aparece casi idéntica en la mayoría de los mensajes que terminaron en reunión o en contacto directo.")
w("Es de junio y julio, los dos mejores meses del proyecto.")
w("")
w("```")
w("[Nombre], gracias por conectar!")
w("Me llamó la atención [hecho textual y concreto del contenido del prospecto].")
w("[Observación breve sobre esa elección suya].")
w("Si estoy entendiendo bien lo que leí, tenía una consulta y quería saber si me podías ayudar.")
w("```")
w("")
w("Tres rasgos que la distinguen de lo que se escribió después:")
w("")
w("1. **No menciona Hint Media.** La agencia aparece recién en el segundo mensaje.")
w("2. **Cita algo textual.** No resume el perfil: nombra una frase, un dato o una decisión concreta.")
w("3. **Pide ayuda en vez de ofrecer valor.** El prospecto queda en posición de experto.")
w("")
w("---")
w("")
w("## 2. Mensajes que terminaron en REUNIÓN")
w("")
w("Son seis de los ocho casos del proyecto (dos no tienen MSG1 registrado).")
w("")
for e in bank['REUNION'][:6]:
    w(fmt(e))
    w("")
w("---")
w("")
w("## 3. Mensajes donde el prospecto dio su mail o teléfono")
w("")
w("La señal de compra más fuerte de la base: el 55% de quienes dieron contacto terminó pidiendo dossier.")
w("")
for e in bank['CONTACTO'][:8]:
    w(fmt(e))
    w("")
w("---")
w("")
w("## 4. Mensajes que abrieron conversación sostenida")
w("")
w("La conversación convierte a reunión 6,7% contra 0,9% del dossier. Es el camino que funciona.")
w("")
for e in bank['CHARLA'][:6]:
    w(fmt(e, lim=400))
    w("")
w("---")
w("")
w("## 5. Mensajes que NO funcionaron")
w("")
w("Recibieron respuesta y el hilo murió, o directamente no recibieron nada. **No imitar.**")
w("")
for e in bank['RESPONDIO_MURIO'][:5]:
    w(fmt(e, con_resp=False, lim=420))
    w("")
w("---")
w("")
w("## 6. Vocabulario medido")
w("")
w("Frecuencia de aparición en los mensajes que consiguieron reunión, contacto o conversación,")
w("contra los que no obtuvieron respuesta.")
w("")
w("### Palabras presentes en los que funcionaron")
w("")
w("| Palabra | En los que funcionaron | En los que no |")
w("|---|---|---|")
for a, b, c in [("me llamó la atención", "54%", "27%"), ("conectar", "51%", "20%"),
                ("quería saber", "50%", "22%"), ("me podías ayudar", "49%", "22%"),
                ("tenía", "50%", "22%"), ("consulta", "44%", "22%"),
                ("si estoy entendiendo bien", "43%", "21%"), ("artículo / nota / publicación", "6%", "2%"),
                ("pusiste / escribiste", "5%", "2%")]:
    w("| %s | %s | %s |" % (a, b, c))
w("")
w("Son palabras de lectura real y de pedido. Ninguna es de venta.")
w("")
w("### Palabras que sólo aparecen en los que murieron")
w("")
w("| Palabra | En los que funcionaron | En los que no |")
w("|---|---|---|")
for a, b, c in [("mientras", "0%", "10%"), ("mercados", "0%", "6%"), ("presencia", "0%", "5%"),
                ("credibilidad", "1%", "8%"), ("cliente", "2%", "12%"), ("solución", "0%", "3%"),
                ("construimos", "0%", "3%"), ("resolvemos", "0%", "3%"), ("escale", "0%", "2,5%"),
                ("complejo", "0%", "2,5%"), ("gerente", "0%", "3,5%")]:
    w("| %s | %s | %s |" % (a, b, c))
w("")
w("Es el vocabulario del pitch: abstracciones de agencia y palabras de catálogo.")
w("**\"mientras\" con 0% contra 10% es el marcador más claro de frase subordinada larga:**")
w("cuando aparece, el mensaje se volvió denso.")
w("")
w("---")
w("")
w("## 7. Advertencias de lectura")
w("")
w("- Los mensajes ganadores son mayormente de junio y julio; los perdedores de agosto y septiembre.")
w("  Parte de esta diferencia mide el cambio de metodología, no la palabra en sí. El vocabulario")
w("  y el método están entrelazados: las palabras del pitch vienen con el pitch.")
w("- Sólo hay 8 reuniones en toda la base. Cualquier patrón sobre ese grupo es orientativo, no ley.")
w("- Los ejemplos de la sección 5 fallaron por el conjunto del mensaje, no necesariamente por una frase.")
w("")

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print("OK ->", OUT)
print("lineas:", len(L))
