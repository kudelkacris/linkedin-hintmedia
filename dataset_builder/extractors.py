"""
Parsers de archivos conversaciones/*.md. Dos formatos detectados en el corpus:
  - markdown plano: "# Nombre" + campos en negrita ("**Campo:** valor") + headers "## ..." con bloques ">"
  - frontmatter (estilo memoria): "---\nname:\n...\n---" seguido de markdown
Ambos devuelven el mismo dict crudo (raw record), sin clasificar nada todavía.
"""
import re
import os

BOLD_FIELD_RE = re.compile(r'\*\*([^:*]+):\*\*\s*(.*)')
HEADER_RE = re.compile(r'^##\s+(.+)$')
QUOTE_RE = re.compile(r'^>\s?(.*)$')
H1_RE = re.compile(r'^#\s+(.+)$')
FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---\n?', re.DOTALL)
YAML_LINE_RE = re.compile(r'^(\w+):\s*(.*)$')


def parse_frontmatter(text):
    """Extrae name/description/metadata.type del bloque YAML simple inicial."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    block = m.group(1)
    data = {}
    for line in block.split('\n'):
        line = line.strip()
        ym = YAML_LINE_RE.match(line)
        if ym:
            data[ym.group(1)] = ym.group(2).strip()
    rest = text[m.end():]
    return data, rest


def extract_bold_fields(text):
    """Captura todos los **Campo:** valor del documento. Si un campo aparece más de una vez
    (ej. 'Estado' actualizado a lo largo de la conversación), se queda con el ÚLTIMO valor no
    vacío, porque representa el estado más reciente."""
    fields = {}
    for line in text.split('\n'):
        m = BOLD_FIELD_RE.match(line.strip())
        if m:
            key = m.group(1).strip().lower()
            val = m.group(2).strip()
            if val:
                fields[key] = val
    return fields


def extract_sections(text):
    """
    Devuelve lista de (header_text, body_lines) para cada bloque "## ...".
    body_lines incluye tanto líneas '>' (citas) como texto plano debajo del header.
    """
    sections = []
    current_header = None
    current_lines = []
    for line in text.split('\n'):
        hm = HEADER_RE.match(line.strip())
        if hm:
            if current_header is not None:
                sections.append((current_header, current_lines))
            current_header = hm.group(1).strip()
            current_lines = []
        elif current_header is not None:
            current_lines.append(line)
    if current_header is not None:
        sections.append((current_header, current_lines))
    return sections


def quotes_from_lines(lines):
    out = []
    for line in lines:
        qm = QUOTE_RE.match(line.strip())
        if qm and qm.group(1):
            out.append(qm.group(1))
    return '\n'.join(out).strip()


def first_h1(text):
    for line in text.split('\n'):
        m = H1_RE.match(line.strip())
        if m:
            return m.group(1).strip()
    return ''


def classify_section(header):
    """Mapea un header de texto libre a una categoría conocida (msg1, respuesta_msg1, msg2, ...)."""
    h = header.lower()
    if 'seg2' in h or 'seguimiento 2' in h:
        return 'seg2'
    if 'seg1' in h or 'seguimiento 1' in h or re.search(r'\bseg\b', h):
        return 'seg1'
    if 'msg3' in h or 'dossier' in h:
        return 'dossier'
    if 'msg4' in h or 'cierre' in h:
        return 'cierre'
    if h.startswith('respuesta') or 'respuesta' in h:
        return 'respuesta'
    if h.startswith('msg') or h.startswith('mensaje'):
        return 'msg'
    if 'nota' in h:
        return 'notas'
    if 'conversaci' in h or 'resumen' in h:
        return 'resumen'
    return 'otro'


def parse_file(path):
    """Parsea un archivo .md y devuelve un dict crudo con toda la información extraíble por regex."""
    with open(path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    fm_data, rest = parse_frontmatter(raw_text)
    body = rest if fm_data else raw_text

    bold_fields = extract_bold_fields(body)
    sections = extract_sections(body)

    nombre = bold_fields.get('nombre') or first_h1(body) or fm_data.get('name', '').replace('-', ' ').title()

    # Acumular bloques por categoría, en orden de aparición (puede haber MSG1 y MSG2 ambos clasificados como 'msg')
    msg_blocks = []      # todas las secciones tipo 'msg' (MSG1, MSG2, MSG3...) en orden
    respuesta_blocks = []  # todas las respuestas del prospecto, en orden
    seg1_text, seg2_text, dossier_text, cierre_text, notas_text = '', '', '', '', ''

    for header, lines in sections:
        cat = classify_section(header)
        quoted = quotes_from_lines(lines)
        plain = '\n'.join(l.strip() for l in lines if l.strip() and not l.strip().startswith('>')).strip()
        block_text = quoted or plain
        if cat == 'msg':
            msg_blocks.append((header, block_text))
        elif cat == 'respuesta':
            respuesta_blocks.append((header, block_text))
        elif cat == 'seg1':
            seg1_text += ('\n' + block_text) if seg1_text else block_text
        elif cat == 'seg2':
            seg2_text += ('\n' + block_text) if seg2_text else block_text
        elif cat == 'dossier':
            dossier_text += ('\n' + block_text) if dossier_text else block_text
        elif cat == 'cierre':
            cierre_text += ('\n' + block_text) if cierre_text else block_text
        elif cat == 'notas':
            notas_text += ('\n' + block_text) if notas_text else block_text

    msg1_text = msg_blocks[0][1] if len(msg_blocks) >= 1 else ''
    msg2_text = msg_blocks[1][1] if len(msg_blocks) >= 2 else ''
    respuesta_msg1_text = respuesta_blocks[0][1] if len(respuesta_blocks) >= 1 else ''
    respuesta_dossier_text = ''
    # Heurística: la respuesta al dossier suele ser la respuesta que sigue al bloque MSG2/dossier
    if len(respuesta_blocks) >= 2:
        respuesta_dossier_text = respuesta_blocks[1][1]

    estado_raw = bold_fields.get('estado', '')
    fecha_raw = bold_fields.get('fecha', '')

    return {
        'fuente_archivo': os.path.basename(path),
        'nombre': nombre,
        'empresa': bold_fields.get('empresa', ''),
        'pais': bold_fields.get('país', bold_fields.get('pais', '')),
        'sector': bold_fields.get('sector', ''),
        'cargo': bold_fields.get('cargo', ''),
        'estado_raw': estado_raw,
        'fecha_raw': fecha_raw,
        'msg1_text': msg1_text,
        'msg2_text': msg2_text,
        'respuesta_msg1_text': respuesta_msg1_text,
        'respuesta_dossier_text': respuesta_dossier_text,
        'seg1_text': seg1_text,
        'seg2_text': seg2_text,
        'dossier_text': dossier_text,
        'cierre_text': cierre_text,
        'notas_text': notas_text,
        'full_text': raw_text,
        'all_respuestas': [t for _, t in respuesta_blocks],
        'is_frontmatter_format': bool(fm_data),
    }
