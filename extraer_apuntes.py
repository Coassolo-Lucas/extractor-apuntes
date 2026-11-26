#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
Extractor y Jerarquizador de Apuntes para NotebookLM (Sistema de 4 Colores)
================================================================================
Clasificación visual exclusiva por color de resaltado (sin negrita ni subrayado):

  1. 🟣 Título (#8e7cc3):
     Secciones y títulos temáticos principales (## 🟣 [TÍTULO] <texto>).
  2. 🟠 Concepto Importante (#ff9900):
     Conceptos clave y definiciones esenciales (### 🟠 [CONCEPTO IMPORTANTE] <texto>).
  3. 🟪 Información relacionada (#b4a7d6):
     Contenido y conceptos asociados (- 🟪 [Información relacionada]: <texto>).
  4. 🟡 Información complementaria o secundaria (#fff2cc):
     Detalles, ejemplos, aclaraciones y datos (  - 🟡 [Información complementaria]: <texto>).

Carpetas de trabajo:
  - input/  -> Coloca aquí los archivos PDF exportados de Google Docs.
  - output/ -> Aquí se generarán los archivos Markdown estructurados para NotebookLM.
================================================================================
"""

import os
import sys
import re
import math
import argparse

try:
    import pymupdf  # PyMuPDF
except ImportError:
    print("\n❌ Error: 'pymupdf' no está instalado.")
    print("👉 Instálalo ejecutando: pip install pymupdf\n")
    sys.exit(1)


# Directorios base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def hex_to_rgb(hex_str):
    """Convierte cadena HEX ('#RRGGBB') a tupla RGB con valores 0.0 - 1.0."""
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def rgb_to_hex(rgb):
    """Convierte tupla RGB (0.0 - 1.0) a cadena HEX '#RRGGBB'."""
    r, g, b = [max(0, min(255, int(round(c * 255)))) for c in rgb[:3]]
    return f"#{r:02X}{g:02X}{b:02X}"


# Definición canónica de los 4 colores objetivos
COLOR_DEFINITIONS = {
    'titulo': {
        'hex': '#8E7CC3',
        'rgb': hex_to_rgb('#8E7CC3'),
        'label': '🟣 Título',
        'prefix': '## 🟣 [TÍTULO]',
        'level': 1
    },
    'concepto': {
        'hex': '#FF9900',
        'rgb': hex_to_rgb('#FF9900'),
        'label': '🟠 Concepto Importante',
        'prefix': '### 🟠 [CONCEPTO IMPORTANTE]',
        'level': 2
    },
    'relacionada': {
        'hex': '#B4A7D6',
        'rgb': hex_to_rgb('#B4A7D6'),
        'label': '🟪 Información relacionada',
        'prefix': '- 🟪 [Información relacionada]:',
        'level': 3
    },
    'complementaria': {
        'hex': '#FFF2CC',
        'rgb': hex_to_rgb('#FFF2CC'),
        'label': '🟡 Información complementaria o secundaria',
        'prefix': '  - 🟡 [Información complementaria]:',
        'level': 4
    }
}


def classify_color(rgb, tolerance=0.12):
    """
    Compara un color RGB con los 4 colores objetivo usando distancia euclidiana.
    Devuelve la clave de la categoría ('titulo', 'concepto', 'relacionada', 'complementaria')
    o None si no corresponde a ninguno de los 4 colores.
    """
    best_key = None
    min_dist = float('inf')

    for key, info in COLOR_DEFINITIONS.items():
        target = info['rgb']
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb[:3], target)))
        if dist < min_dist:
            min_dist = dist
            best_key = key

    if min_dist <= tolerance:
        return best_key
    return None


def get_page_highlights(page):
    """
    Extrae todos los resaltados presentes en la página, cubriendo tanto:
      1. Anotaciones estándar de PDF (Acrobat, lectores PDF).
      2. Dibujos vectoriales directos de Google Docs (rectángulos con 'fill').
    """
    highlights = []

    # 1. Anotaciones de tipo Highlight
    for a in page.annots():
        if a.type[1] == 'Highlight':
            c = a.colors.get('stroke') or a.colors.get('fill')
            if not c:
                continue
            color = tuple(float(v) for v in c[:3])

            quads = []
            if a.vertices and len(a.vertices) >= 4:
                for i in range(0, len(a.vertices), 4):
                    quads.append(pymupdf.Quad(a.vertices[i:i+4]).rect)
            else:
                quads.append(a.rect)

            for q in quads:
                highlights.append({'rect': q, 'color': color, 'source': 'annot'})

    # 2. Dibujos vectoriales directos de Google Docs
    for d in page.get_drawings():
        rect = pymupdf.Rect(d['rect'])
        # Ignorar fondo blanco completo de página
        if rect.width > page.rect.width * 0.9 and rect.height > page.rect.height * 0.9:
            continue

        fill = d.get('fill')
        if fill is not None and fill != (1.0, 1.0, 1.0) and rect.height >= 4:
            highlights.append({
                'rect': rect,
                'color': tuple(float(v) for v in fill[:3]),
                'source': 'drawing'
            })

    return highlights


def calibrate_document(pdf_path, start_page=1, end_page=None):
    """
    Modo de inspección: lista todos los colores detectados en el archivo y
    muestra a qué categoría de las 4 se asigna cada uno.
    """
    if not os.path.exists(pdf_path):
        print(f"\n❌ Error: No se encontró el archivo '{pdf_path}'")
        return

    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    start_idx = max(0, start_page - 1)
    end_idx = min(total_pages, end_page) if end_page else total_pages

    print("\n" + "=" * 82)
    print(f"🔍 CALIBRACIÓN DE COLORES EN: '{os.path.basename(pdf_path)}'")
    print(f"   Páginas analizadas: {start_idx + 1} a {end_idx} (Total: {total_pages})")
    print("=" * 82)

    stats = {}
    for pno in range(start_idx, end_idx):
        page = doc[pno]
        for h in get_page_highlights(page):
            rgb = h['color']
            hex_c = rgb_to_hex(rgb)
            rgb255 = tuple(int(round(c * 255)) for c in rgb[:3])
            key = (hex_c, rgb255)
            stats[key] = stats.get(key, 0) + 1

    if not stats:
        print("\n⚠️ No se detectaron resaltados en el rango seleccionado.\n")
        return

    print("\n{:<10} {:<18} {:<12} {:<38}".format(
        "HEX", "RGB (0-255)", "Ocurrencias", "Clasificación"
    ))
    print("-" * 82)

    for (hex_c, rgb255), count in sorted(stats.items(), key=lambda x: -x[1]):
        rgb_float = tuple(c / 255.0 for c in rgb255)
        matched_cat = classify_color(rgb_float)
        if matched_cat:
            info = COLOR_DEFINITIONS[matched_cat]
            desc = f"{info['label']} ({info['hex']})"
        else:
            desc = "❌ Descartado (No coincide con los 4 colores)"

        print("{:<10} {:<18} {:<12} {:<38}".format(hex_c, str(rgb255), count, desc))

    print("-" * 82)
    print("\n🎯 Colores objetivo configurados:")
    for key, cinfo in COLOR_DEFINITIONS.items():
        print(f"   - {cinfo['label']:<45}: {cinfo['hex']}")
    print()


def extract_study_notes(pdf_path, output_md, start_page=1, end_page=None):
    """
    Lee el PDF en orden de lectura, extrae exclusivamente el texto resaltado
    bajo los 4 colores definidos y genera el archivo Markdown estructurado.
    """
    if not os.path.exists(pdf_path):
        print(f"\n❌ Error: No se encontró el archivo: '{pdf_path}'")
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
        highlights = get_page_highlights(page)
        if not highlights:
            continue

        words = page.get_text("words")
        page_classified_words = []

        for w in words:
            # w: (x0, y0, x1, y1, word_text, block_no, line_no, word_no)
            w_rect = pymupdf.Rect(w[0], w[1], w[2], w[3])
            center = pymupdf.Point((w[0] + w[2]) / 2.0, (w[1] + w[3]) / 2.0)
            w_text = w[4].strip()
            if not w_text:
                continue

            # Buscar si el centro o cuerpo de la palabra coincide con un resaltado
            matched_category = None
            for h in highlights:
                if h['rect'].contains(center) or (not (w_rect & h['rect']).is_empty and (w_rect & h['rect']).width > w_rect.width * 0.35):
                    cat = classify_color(h['color'])
                    if cat:
                        matched_category = cat
                        break

            # Si no coincide con ninguno de los 4 colores, se descarta por completo
            if not matched_category:
                continue

            page_classified_words.append({
                'text': w_text,
                'category': matched_category,
                'level': COLOR_DEFINITIONS[matched_category]['level'],
                'page': pno + 1,
                'y0': w[1],
                'x0': w[0]
            })

        # Agrupar palabras contiguas con la misma categoría de color en la página
        cur_group = None
        for pw in page_classified_words:
            if cur_group is None:
                cur_group = {
                    'category': pw['category'],
                    'level': pw['level'],
                    'text': pw['text'],
                    'page': pw['page'],
                    'y0': pw['y0'],
                    'x0': pw['x0']
                }
            elif cur_group['category'] == pw['category']:
                cur_group['text'] += ' ' + pw['text']
            else:
                raw_items.append(cur_group)
                cur_group = {
                    'category': pw['category'],
                    'level': pw['level'],
                    'text': pw['text'],
                    'page': pw['page'],
                    'y0': pw['y0'],
                    'x0': pw['x0']
                }
        if cur_group:
            raw_items.append(cur_group)

    if not raw_items:
        print("\n⚠️ No se encontró texto con los 4 colores especificados.")
        print("💡 Ejecuta en modo calibración para ver los códigos de color de tu PDF:")
        print(f"   python {sys.argv[0]} \"{pdf_path}\" --calibrate\n")
        return False

    # Ordenar por secuencia natural de lectura
    raw_items.sort(key=lambda it: (it['page'], round(it['y0'] / 4) * 4, it['x0']))

    # Limpieza de cohesión de texto y unión de líneas partidas
    cleaned_items = []
    for it in raw_items:
        txt = it['text'].strip()
        txt = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', txt)
        txt = re.sub(r'\s+', ' ', txt)
        if not txt:
            continue

        if (cleaned_items and
            cleaned_items[-1]['category'] == it['category'] and
            cleaned_items[-1]['page'] == it['page'] and
            abs(it['y0'] - cleaned_items[-1]['y0']) < 24):
            cleaned_items[-1]['text'] += ' ' + txt
        else:
            cleaned_items.append(it)

    # Construir el documento Markdown estructurado para NotebookLM
    lines = [
        f"# Resumen de Estudio: {os.path.splitext(os.path.basename(pdf_path))[0]}",
        "> *Documento estructurado como fuente única de estudio para NotebookLM.*",
        "> *Estructura generada mediante clasificación exacta de 4 colores de resaltado.*",
        "",
        "---",
        ""
    ]

    counts = {'titulo': 0, 'concepto': 0, 'relacionada': 0, 'complementaria': 0}
    has_title = False
    has_concept = False

    for it in cleaned_items:
        cat = it['category']
        txt = it['text'].strip()
        if not txt:
            continue

        counts[cat] += 1

        if cat == 'titulo':
            has_title = True
            lines.append("")
            lines.append(f"## 🟣 [TÍTULO] {txt}")
            lines.append("")
        elif cat == 'concepto':
            has_concept = True
            lines.append("")
            lines.append(f"### 🟠 [CONCEPTO IMPORTANTE] {txt}")
            lines.append("")
        elif cat == 'relacionada':
            lines.append(f"- 🟪 [Información relacionada]: {txt}")
        elif cat == 'complementaria':
            indent = "  " if (has_concept or has_title) else ""
            lines.append(f"{indent}- 🟡 [Información complementaria]: {txt}")

    content = "\n".join(lines)
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(content)

    print("\n✅ Resumen generado exitosamente:")
    print(f"   - 🟣 Títulos (#8e7cc3):                     {counts['titulo']}")
    print(f"   - 🟠 Conceptos Importantes (#ff9900):       {counts['concepto']}")
    print(f"   - 🟪 Información relacionada (#b4a7d6):     {counts['relacionada']}")
    print(f"   - 🟡 Información complementaria (#fff2cc): {counts['complementaria']}")
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
        description="Extrae y jerarquiza apuntes en PDF bajo el sistema de 4 colores para NotebookLM."
    )
    parser.add_argument("pdf", nargs="?", default=None, help="Ruta al archivo PDF (si se omite, busca en input/)")
    parser.add_argument("-o", "--output", default=None, help="Archivo Markdown de salida (por defecto en output/)")
    parser.add_argument("--start-page", type=int, default=None, help="Página inicial (1-indexed)")
    parser.add_argument("--end-page", type=int, default=None, help="Página final (1-indexed)")
    parser.add_argument("-c", "--calibrate", action="store_true", help="Inspecciona los colores detectados en el PDF")

    args = parser.parse_args()

    target_pdf = args.pdf
    if not target_pdf:
        target_pdf = find_default_pdf()

    if not target_pdf or not os.path.exists(target_pdf):
        print("\n❌ No se especificó ningún archivo PDF o no se encontró en 'input/'.")
        print("💡 Opciones:")
        print("   1. Coloca tu PDF en la carpeta 'input/' y ejecuta:")
        print("      python extraer_apuntes.py")
        print("   2. O especifica la ruta:")
        print("      python extraer_apuntes.py \"ruta/a/tu_archivo.pdf\"\n")
        sys.exit(1)

    if args.calibrate:
        calibrate_document(target_pdf, start_page=args.start_page or 1, end_page=args.end_page)
        return

    # Ruta de salida por defecto en output/
    if args.output:
        output_file = args.output
    else:
        base_name = os.path.splitext(os.path.basename(target_pdf))[0]
        output_file = os.path.join(OUTPUT_DIR, f"{base_name}_resumen.md")

    extract_study_notes(
        target_pdf,
        output_file,
        start_page=args.start_page or 1,
        end_page=args.end_page
    )


if __name__ == "__main__":
    main()
