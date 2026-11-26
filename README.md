# 📚 Extractor y Jerarquizador de Apuntes para NotebookLM

Herramienta en Python para extraer, limpiar y jerarquizar notas de estudio a partir de archivos **PDF exportados desde Google Docs**. Filtra todo el texto de relleno y genera un archivo Markdown limpio (`output/<nombre>_resumen.md`) listo para subir como fuente a [NotebookLM](https://notebooklm.google.com).

---

## 🎨 Código de Colores y Jerarquía de Estudio

Para mantener la toma de apuntes simple y ágil, el sistema utiliza **2 colores principales + subrayado**:

| Formato Visual en Google Docs | Nivel en Markdown | Significado / Uso |
| :--- | :--- | :--- |
| **Resaltado Naranja + Negrita** | `### 🔴 [CONCEPTO MUY IMPORTANTE]` | Concepto principal / Definición clave |
| **Resaltado Naranja (sin negrita)** | `- 🟠 [Concepto / Explicación]:` | Explicación o contenido complementario del concepto |
| **Resaltado Morado / Violeta** | `  - 🟣 [Concepto relacionado]:` | Conceptos o ramas asociadas al tema |
| **Texto Subrayado (*underline*)** | `  - ✏️ [Detalle]:` | Precisiones, datos de examen o detalles puntuales |

> **Nota:** Cualquier texto que no tenga resaltado ni subrayado es descartado automáticamente.

---

## 📁 Estructura del Proyecto

```text
ExtractorApuntes/
├── input/                 <- Coloca aquí tus PDFs exportados de Google Docs
│   └── .gitkeep
├── output/                <- Aquí se guardan los archivos Markdown filtrados
│   └── .gitkeep
├── extraer_apuntes.py     <- Script principal de extracción y jerarquización
├── requirements.txt       <- Dependencias (PyMuPDF)
├── .gitignore
└── README.md
```

---

## 🚀 Instalación Rápida

1. Clona el repositorio o abre la carpeta en tu editor / terminal.
2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

---

## 💻 Modo de Uso

### 1. Uso Automático (Recomendado)
Coloca tu archivo PDF en la carpeta `input/` y ejecuta:

```bash
python extraer_apuntes.py
```
*El script detectará automáticamente el PDF dentro de `input/` y creará el resumen en la carpeta `output/`.*

### 2. Procesar un archivo específico
```bash
python extraer_apuntes.py input/mi_clase.pdf
```

### 3. Filtrar por rango de páginas
```bash
python extraer_apuntes.py input/apuntes.pdf --start-page 1 --end-page 20
```

### 4. Modo Calibración (inspeccionar colores detectados)
```bash
python extraer_apuntes.py input/apuntes.pdf --calibrate
```

---

## 🤖 Prompt para NotebookLM

Una vez generado tu archivo en `output/`, súbelo como fuente a NotebookLM y utiliza el siguiente prompt:

```markdown
He subido mis apuntes de estudio filtrados y jerarquizados visualmente. Utiliza ÚNICAMENTE la información de esta fuente para generar:

1. MAPA CONCEPTUAL Y ESTRUCTURA:
   - Nodos principales: Únicamente los "🔴 [CONCEPTO MUY IMPORTANTE]".
   - Ramas asociadas: Los "🟣 [Concepto relacionado]".
   - Explicaciones y desarrollo: Los "🟠 [Concepto / Explicación]".
   - Precisiones técnicas: Los "✏️ [Detalle]".

2. GUÍA DE ESTUDIO INTENSIVA:
   - Sintetiza cada tema priorizando los conceptos clave (🔴 y 🟣).
   - Destaca los detalles subrayados (✏️) como puntos críticos para exámenes.

3. QUIZ DE AUTOEVALUACIÓN (10 preguntas con respuestas justificadas al final):
   - 6 preguntas sobre conceptos muy importantes (🔴).
   - 3 preguntas sobre conceptos relacionados (🟣).
   - 1 pregunta sobre detalles técnicos subrayados (✏️).
```
