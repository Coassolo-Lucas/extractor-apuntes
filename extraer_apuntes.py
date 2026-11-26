#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
Extractor y Jerarquizador de Apuntes para NotebookLM
================================================================================
Flujo simplificado de 2 colores principales + subrayado:
  1. 🔴 Naranja (Conceptos muy importantes):
     - Con negrita: Se jerarquiza como título principal (### 🔴 [CONCEPTO MUY IMPORTANTE]).
     - Sin negrita: Texto complementario del concepto (- 🟠 [Concepto / Explicación]).
  2. 🟣 Morado / Violeta (Conceptos relacionados):
     - Conceptos asociados al tema principal (- 🟣 [Concepto relacionado]).
  3. ✏️ Subrayado (Detalles y precisiones):
     - Texto con subrayado (  - ✏️ [Detalle clave]).

Carpetas por defecto:
  - input/  -> Coloca aquí tus PDFs exportados desde Google Docs.
  - output/ -> Aquí se generarán los resúmenes en Markdown para NotebookLM.
================================================================================
"""

import os
import sys
import re
import argparse
import colorsys

try:
    import pymupdf  # PyMuPDF
except ImportError:
    print("\n❌ Error: 'pymupdf' no está instalado.")
    print("👉 Instálalo con: pip install pymupdf\n")
    sys.exit(1)


# Directorios base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Paletas de Google Docs reconocidas
ORANGE_HEXES = ["#FF9900", "#FF8A00", "#F9CB9C", "#FCE5CD", "#FFB066"]
PURPLE_HEXES = ["#9900FF", "#674EA7", "#8E7CC3", "#B4A7D6", "#D9D2E9", "#C27BA0", "#D5A6BD"]


def rgb_to_hex(rgb):
    """Convierte tupla/lista RGB (0.0 - 1.0) a formato HEX '#RRGGBB'."""
    r, g, b = [max(0, min(255, int(round(c * 255)))) for c in rgb[:3]]
    return f"#{r:02X}{g:02X}{b:02X}"


def classify_color(rgb, custom_orange_hex=None, custom_purple_hex=None):
    """
    Clasifica un color RGB en:
      - 'orange': Naranja (Concepto muy importante)
      - 'purple': Morado (Concepto relacionado)
      - 'other': Otros colores complementarios
    """
    hex_str = rgb_to_hex(rgb).upper()

    if custom_orange_hex and hex_str == custom_orange_hex.upper():
        return 'orange'
    if custom_purple_hex and hex_str == custom_purple_hex.upper():
        return 'purple'

    if hex_str in [h.upper() for h in ORANGE_HEXES]:
        return 'orange'
    if hex_str in [h.upper() for h in PURPLE_HEXES]:
        return 'purple'

    r, g, b = rgb[:3]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h_deg = h * 360.0

    # Naranja: tono entre 10° y 48°
    if 10.0 <= h_deg <= 48.0 and s >= 0.20:
        return 'orange'

    # Morado / Violeta: tono entre 250° y 325°
    if 250.0 <= h_deg <= 325.0 and s >= 0.15:
        return 'purple'

    return 'other'


def get_page_markings(page):
    """
    Extrae anotaciones estándar y dibujos vectoriales (rectángulos y líneas de Google Docs).
    """
    highlights = []
    underlines = []

    # 1. Anotaciones formales de PDF
    for a in page.annots():
        atype = a.type[1]
        if atype not in ('Highlight', 'Underline'):
            continue
        c = a.colors.get('stroke') or a.colors.get('fill') or [0, 0, 0]
        color = tuple(float(v) for v in c[:3])
        quads = []
        if a.vertices and len(a.vertices) >= 4:
            for i in range(0, len(a.vertices), 4):
                quads.append(pymupdf.Quad(a.vertices[i:i+4]).rect)
        else:
            quads.append(a.rect)

        if atype == 'Highlight':
            for q in quads:
                highlights.append({'rect': q, 'color': color, 'source': 'annot'})
        elif atype == 'Underline':
            for q in quads:
                underlines.append({'rect': q, 'source': 'annot'})

    # 2. Dibujos vectoriales directos de Google Docs
    for d in page.get_drawings():
        rect = pymupdf.Rect(d['rect'])
        if rect.width > page.rect.width * 0.9 and rect.height > page.rect.height * 0.9:
            continue

        fill = d.get('fill')
        if fill is not None and fill != (1.0, 1.0, 1.0) and rect.height >= 4:
            highlights.append({
                'rect': rect,
                'color': tuple(float(v) for v in fill[:3]),
                'source': 'drawing'
            })

        if rect.height <= 2.5 and rect.width >= 5:
            text_rect = pymupdf.Rect(rect.x0, rect.y0 - 13, rect.x1, rect.y1 + 2)
            underlines.append({'rect': text_rect, 'source': 'drawing'})

    return highlights, underlines


def calibrate_document(pdf_path, start_page=1, end_page=None):
    """Inspecciona y muestra en consola los colores detectados."""
    if not os.path.exists(pdf_path):
        print(f"\n❌ Error: No se encontró el archivo '{pdf_path}'")
        return

    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    start_idx = max(0, start_page - 1)
    end_idx = min(total_pages, end_page) if end_page else total_pages

    print("\n" + "=" * 78)
    print(f"🔍 CALIBRACIÓN DE COLORES: '{os.path.basename(pdf_path)}'")
    print(f"   Páginas analizadas: {start_idx + 1} a {end_idx} (Total: {total_pages})")
    print("=" * 78)

    stats = {}
    total_underlines = 0

    for pno in range(start_idx, end_idx):
        page = doc[pno]
        hl_list, ul_list = get_page_markings(page)
        total_underlines += len(ul_list)

        for h in hl_list:
            rgb = h['color']
            hex_c = rgb_to_hex(rgb)
            rgb255 = tuple(int(round(c * 255)) for c in rgb[:3])
            key = (h['source'], hex_c, rgb255)
            stats[key] = stats.get(key, 0) + 1

    print("\n{:<10} {:<10} {:<18} {:<12} {:<24}".format(
        "Origen", "HEX", "RGB (0-255)", "Ocurrencias", "Clasificación estimada"
    ))
    print("-" * 78)

    for (src, hex_c, rgb255), count in sorted(stats.items(), key=lambda x: -x[1]):
        rgb_float = tuple(c / 255.0 for c in rgb255)
        c_type = classify_color(rgb_float)
        if c_type == 'orange':
            clasif = "🔴 Naranja (Muy importante)"
        elif c_type == 'purple':
            clasif = "🟣 Morado (Relacionado)"
        else:
            clasif = "🔵 Complementario"

        print("{:<10} {:<10} {:<18} {:<12} {:<24}".format(src, hex_c, str(rgb255), count, clasif))

    if total_underlines > 0:
        print("{:<10} {:<10} {:<18} {:<12} {:<24}".format("subrayado", "---", "(trazos negros)", total_underlines, "✏️ Detalle subrayado"))

    print("-" * 78 + "\n")


def extract_study_notes(pdf_path, output_md, start_page=1, end_page=None, custom_orange=None, custom_purple=None):
    """Procesa el PDF y escribe el resumen estructurado en Markdown."""
    if not os.path.exists(pdf_path):
        print(f"\n❌ No se encontró el archivo: '{pdf_path}'")
        return False

    os.makedirs(os.path.dirname(os.path.abspath(output_md)), exist_ok=True)

    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    start_idx = max(0, start_page - 1)
    end_idx = min(total_pages, end_page) if end_page else total_pages

    print("\n" + "=" * 70)
    print(f"🚀 Extrayendo apuntes de: {os.path.basename(pdf_path)}")
    print(f"📄 Rango: Páginas {start_idx + 1} a {end_idx} (de {total_pages})")
    print(f"🎯 Salida: {output_md}")
    print("=" * 70)

    raw_items = []

    for pno in range(start_idx, end_idx):
        page = doc[pno]
        highlights, underlines = get_page_markings(page)
        if not highlights and not underlines:
            continue

        spans = []
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    font_lower = span.get("font", "").lower()
                    flags = span.get("flags", 0)
                    is_bold = bool(flags & 16) or ("bold" in font_lower) or ("black" in font_lower)
                    spans.append({
                        'rect': pymupdf.Rect(span['bbox']),
                        'bold': is_bold,
                        'text': span.get('text', '')
                    })

        words = page.get_text("words")
        page_classified_words = []

        for w in words:
            w_rect = pymupdf.Rect(w[0], w[1], w[2], w[3])
            center = pymupdf.Point((w[0] + w[2]) / 2.0, (w[1] + w[3]) / 2.0)
            w_text = w[4].strip()
            if not w_text:
                continue

            # Subrayado: Nivel 4
            is_underlined = False
            for u in underlines:
                if u['rect'].contains(center) or (not (w_rect & u['rect']).is_empty and (w_rect & u['rect']).width > w_rect.width * 0.35):
                    is_underlined = True
                    break

            # Resaltado
            hl_color = None
            for h in highlights:
                if h['rect'].contains(center) or (not (w_rect & h['rect']).is_empty and (w_rect & h['rect']).width > w_rect.width * 0.35):
                    hl_color = h['color']
                    break

            if not is_underlined and not hl_color:
                continue

            # Negrita
            is_bold = False
            for s in spans:
                if s['rect'].contains(center) or (not (w_rect & s['rect']).is_empty and (w_rect & s['rect']).width > w_rect.width * 0.35):
                    is_bold = s['bold']
                    break

            # Jerarquía simplificada:
            if is_underlined:
                level = 4  # ✏️ Detalle
            elif hl_color:
                ctype = classify_color(hl_color, custom_orange, custom_purple)
                if ctype == 'orange':
                    # Si tiene negrita es Concepto Muy Importante (Nivel 1)
                    # Si no tiene negrita sigue siendo parte del concepto (Nivel 2)
                    level = 1 if is_bold else 2
                elif ctype == 'purple':
                    level = 3  # 🟣 Concepto relacionado
                else:
                    level = 5  # Otros complementarios
            else:
                continue

            page_classified_words.append({
                'text': w_text,
                'level': level,
                'page': pno + 1,
                'y': w[1],
                'x': w[0]
            })

        # Agrupar palabras contiguas con mismo nivel
        cur_group = None
        for pw in page_classified_words:
            if cur_group is None:
                cur_group = {'level': pw['level'], 'text': pw['text'], 'page': pw['page'], 'y0': pw['y'], 'x0': pw['x']}
            elif cur_group['level'] == pw['level']:
                cur_group['text'] += ' ' + pw['text']
            else:
                raw_items.append(cur_group)
                cur_group = {'level': pw['level'], 'text': pw['text'], 'page': pw['page'], 'y0': pw['y'], 'x0': pw['x']}
        if cur_group:
            raw_items.append(cur_group)

    if not raw_items:
        print("\n⚠️ No se encontraron fragmentos marcados.")
        return False

    raw_items.sort(key=lambda it: (it['page'], round(it['y0'] / 4) * 4, it['x0']))

    # Limpieza de cohesión de texto
    cleaned_items = []
    for it in raw_items:
        txt = it['text'].strip()
        txt = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', txt)
        txt = re.sub(r'\s+', ' ', txt)
        if not txt:
            continue

        if cleaned_items and cleaned_items[-1]['level'] == it['level'] and cleaned_items[-1]['page'] == it['page'] and abs(it['y0'] - cleaned_items[-1]['y0']) < 22:
            cleaned_items[-1]['text'] += ' ' + txt
        else:
            cleaned_items.append(it)

    # Construir Markdown optimizado para NotebookLM
    lines = [
        f"# Resumen de Apuntes: {os.path.basename(pdf_path)}",
        "> *Documento filtrado para NotebookLM.*",
        "> *Naranja en negrita = Conceptos muy importantes | Naranja = Explicación | Morado = Conceptos relacionados | Subrayado = Detalles*",
        "",
        "---",
        ""
    ]

    has_level_1 = False
    counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for it in cleaned_items:
        lvl = it['level']
        txt = it['text'].strip()
        if not txt:
            continue

        counts[lvl] += 1

        if lvl == 1:
            has_level_1 = True
            lines.append("")
            lines.append(f"### 🔴 [CONCEPTO MUY IMPORTANTE] {txt}")
            lines.append("")
        elif lvl == 2:
            # Explicación del concepto en naranja (sin negrita)
            lines.append(f"- 🟠 [Concepto / Explicación]: {txt}")
        elif lvl == 3:
            # Morado: Concepto relacionado
            indent = "  " if has_level_1 else ""
            lines.append(f"{indent}- 🟣 [Concepto relacionado]: {txt}")
        elif lvl == 4:
            # Subrayado: Detalle clave
            indent = "  " if has_level_1 else ""
            lines.append(f"{indent}- ✏️ [Detalle]: {txt}")
        elif lvl == 5:
            indent = "  " if has_level_1 else ""
            lines.append(f"{indent}- 🔵 [Info complementaria]: {txt}")

    content = "\n".join(lines)
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(content)

    print("\n✅ Resumen generado exitosamente:")
    print(f"   - 🔴 Conceptos muy importantes (Naranja + Negrita): {counts[1]}")
    print(f"   - 🟠 Explicación / Texto en naranja:                {counts[2]}")
    print(f"   - 🟣 Conceptos relacionados (Morado):               {counts[3]}")
    print(f"   - ✏️ Detalles subrayados:                           {counts[4]}")
    if counts[5] > 0:
        print(f"   - 🔵 Otros colores complementarios:                 {counts[5]}")
    print(f"   - 📁 Guardado en: {os.path.abspath(output_md)}")
    print("=" * 70 + "\n")
    return True


def find_default_pdf():
    """Busca automáticamente un archivo PDF en input/ o en el directorio actual."""
    if os.path.exists(INPUT_DIR):
        input_pdfs = [os.path.join(INPUT_DIR, f) for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
        if input_pdfs:
            return input_pdfs[0]

    local_pdfs = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    if local_pdfs:
        return local_pdfs[0]

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Extrae y organiza apuntes en PDF para NotebookLM (Naranja = Muy importante, Morado = Relacionado, Subrayado = Detalle)."
    )
    parser.add_argument("pdf", nargs="?", default=None, help="Ruta al archivo PDF (si se omite, busca en input/)")
    parser.add_argument("-o", "--output", default=None, help="Archivo Markdown de salida (por defecto en output/)")
    parser.add_argument("--start-page", type=int, default=None, help="Página inicial")
    parser.add_argument("--end-page", type=int, default=None, help="Página final")
    parser.add_argument("-c", "--calibrate", action="store_true", help="Inspecciona los colores detectados")
    parser.add_argument("--orange", default=None, help="Código HEX personalizado para naranja")
    parser.add_argument("--purple", default=None, help="Código HEX personalizado para morado")

    args = parser.parse_args()

    target_pdf = args.pdf
    if not target_pdf:
        target_pdf = find_default_pdf()

    if not target_pdf or not os.path.exists(target_pdf):
        print("\n❌ No se especificó ningún archivo PDF o no se encontró en la carpeta 'input/'.")
        print("💡 Opciones:")
        print("   1. Coloca tu archivo en la carpeta 'input/' y vuelve a ejecutar:")
        print("      python extraer_apuntes.py")
        print("   2. O pásalo directamente como argumento:")
        print("      python extraer_apuntes.py ruta/a/tu_archivo.pdf\n")
        sys.exit(1)

    if args.calibrate:
        calibrate_document(target_pdf, start_page=args.start_page or 1, end_page=args.end_page)
        return

    # Determinar nombre del archivo de salida
    if args.output:
        output_file = args.output
    else:
        base_name = os.path.splitext(os.path.basename(target_pdf))[0]
        output_file = os.path.join(OUTPUT_DIR, f"{base_name}_resumen.md")

    extract_study_notes(
        target_pdf,
        output_file,
        start_page=args.start_page or 1,
        end_page=args.end_page,
        custom_orange=args.orange,
        custom_purple=args.purple
    )


if __name__ == "__main__":
    main()
