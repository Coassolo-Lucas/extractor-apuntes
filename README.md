# 📚 Extractor y Jerarquizador de Apuntes para NotebookLM

Herramienta en Python para extraer, limpiar y jerarquizar notas de estudio a partir de archivos **PDF exportados desde Google Docs**. Filtra todo el texto de relleno y genera un archivo Markdown limpio (`output/<nombre>_resumen.md`) listo para subir como fuente única a [NotebookLM](https://notebooklm.google.com).

---

## 🎨 Sistema de 4 Colores de Resaltado

La jerarquía visual se basa **100% en los 4 colores de resaltado** definidos (sin depender de negritas ni subrayados):

| Color en Google Docs | Código HEX | Nivel en Markdown | Función y Significado |
| :--- | :--- | :--- | :--- |
| **Morado Oscuro / Púrpura** | `#8E7CC3` | `## 🟣 [TÍTULO]` | **Títulos de sección** y ejes temáticos principales |
| **Naranja** | `#FF9900` | `### 🟠 [CONCEPTO IMPORTANTE]` | **Conceptos clave** y definiciones indispensables |
| **Lavanda / Morado Claro** | `#B4A7D6` | `- 🟪 [Información relacionada]:` | **Información asociada**, explicaciones y ramas directas |
| **Amarillo Claro / Manteca** | `#FFF2CC` | `  - 🟡 [Información complementaria]:` | **Detalles secundarios**, ejemplos, aclaraciones y precisiones |

> ℹ️ **Filtro automático:** Cualquier texto que no tenga uno de estos 4 colores de resaltado es descartado por completo.

---

## 📁 Estructura del Repositorio

```text
ExtractorApuntes/
├── input/                 <- Coloca aquí tus PDFs exportados de Google Docs
│   └── .gitkeep
├── output/                <- Aquí se guardan los archivos Markdown filtrados
│   └── .gitkeep
├── extraer_apuntes.py     <- Script principal de extracción
├── requirements.txt       <- Dependencias (PyMuPDF)
├── .gitignore
└── README.md
```

---

## 🚀 Instalación y Uso Rápido

1. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

2. **Uso Automático:**
   Coloca tu archivo PDF en la carpeta `input/` y ejecuta:
   ```bash
   python extraer_apuntes.py
   ```
   *El script procesará el PDF de `input/` y generará el resultado en `output/<nombre_archivo>_resumen.md`.*

3. **Modo Calibración:**
   Si deseas inspeccionar los colores detectados en un PDF antes de procesar:
   ```bash
   python extraer_apuntes.py "input/mi_clase.pdf" --calibrate
   ```

4. **Procesar un rango de páginas:**
   ```bash
   python extraer_apuntes.py "input/mi_clase.pdf" --start-page 1 --end-page 30
   ```

---

## 🤖 Prompt Optimizado para NotebookLM

Una vez generado el archivo en la carpeta `output/`, súbelo como **fuente única** a tu cuaderno en [NotebookLM](https://notebooklm.google.com) y pega este prompt:

```markdown
He subido mis apuntes de estudio organizados estrictamente bajo un sistema jerárquico de 4 colores. Utiliza ÚNICAMENTE la información de esta fuente (sin inventar ni asumir conceptos externos) para generar:

1. MAPA CONCEPTUAL Y ESTRUCTURA TEMÁTICA:
   - Utiliza como ejes principales los "## 🟣 [TÍTULO]".
   - Anida debajo como nodos centrales los "### 🟠 [CONCEPTO IMPORTANTE]".
   - Vincula a ellos la "- 🟪 [Información relacionada]".
   - Incluye como sub-ramas los datos de "🟡 [Información complementaria]".

2. GUÍA DE ESTUDIO INTENSIVA:
   - Sintetiza cada sección priorizando al máximo los Títulos (🟣) y Conceptos Importantes (🟠).
   - Desarrolla cada concepto con su información relacionada (🟪).
   - Resume la información complementaria (🟡) como puntos de contexto y ejemplos para recordar.

3. QUIZ DE AUTOEVALUACIÓN (10 preguntas de opción múltiple con respuestas justificadas al final):
   - 6 preguntas enfocadas en la comprensión y aplicación de los Conceptos Importantes (🟠).
   - 3 preguntas sobre la Información relacionada (🟪) y su vínculo con los conceptos principales.
   - 1 pregunta sobre detalles o ejemplos de la Información complementaria (🟡).
```
