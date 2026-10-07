# formato-entregas — chequeá el formato antes de entregar

Skill para que el grupo pase su PDF (plan de proyecto, informe de avance, entrega final) por
los mismos criterios de forma con que lo corrige la cátedra, **antes** de mandarlo. Devuelve
una lista de qué corregir, con página y cómo hacerlo en Google Docs, Word, LaTeX o Typst.

> Guía paso a paso (instalación, uso y cómo leer el resultado):
> [how-to/formato-entregas.md](../../how-to/formato-entregas.md).

```
skills/formato-entregas/
├── SKILL.md                 instrucciones para el asistente (Claude Code, Cowork, Copilot)
├── references/rubrica.md    la rúbrica de forma completa: leela aunque no uses IA
└── scripts/analizar_pdf.py  medición mecánica: fuente, tamaño, interlineado, justificado,
                             índice vs. títulos, epígrafes, candidatos de lenguaje
```

## Requisitos

- Python 3.9 o superior (sin paquetes extra).
- **poppler** (`pdftohtml`, `pdftotext`, `pdfinfo`) en el PATH:
  - macOS: `brew install poppler`
  - Debian/Ubuntu: `sudo apt install poppler-utils`
  - Windows: `winget install oschwartz10612.Poppler` (o `conda install -c conda-forge poppler`)
    y agregar la carpeta `bin` al PATH.

Probar: `pdfinfo -v` tiene que responder.

## Cómo usarla

### Con Claude Code (recomendado)

Copiar la carpeta al repo del grupo, así queda disponible para todos los integrantes:

```bash
mkdir -p .claude/skills
cp -r <ruta-a-ia-guidelines-taller>/skills/formato-entregas .claude/skills/
```

O, para tenerla en todos los proyectos, en `~/.claude/skills/formato-entregas`.

Después, en Claude Code, con el PDF a mano:

```
Chequeá el formato de docs/plan_de_proyecto.pdf
```

La skill corre el script, lee el PDF y escribe `plan_de_proyecto_chequeo.md` al lado. Con
Claude Cowork es igual: subir la carpeta como skill y pedir el chequeo.

### Solo el script (sin asistente)

```bash
python3 skills/formato-entregas/scripts/analizar_pdf.py docs/plan_de_proyecto.pdf
```

Imprime un informe en Markdown con ✅/❌/❓ por criterio medible: fuente y tamaño del cuerpo,
interlineado (con el valor medido), justificado, carátula, índice y su cotejo con los
títulos, epígrafes y referencias, imágenes y tablas sin epígrafe, y candidatos de primera
persona o voseo con su contexto. Lo que el script no puede medir (registro por sección,
bibliografía bien formada, legibilidad de figuras) está en `references/rubrica.md`.

### Con GitHub Copilot

Copilot no ejecuta skills, pero sí toma contexto: abrí `references/rubrica.md` en una
pestaña, corré el script en la terminal y pegá su salida en el chat con algo como:

```
Con la rúbrica abierta y esta salida del script, ¿qué tengo que corregir en el PDF?
```

## Qué mide y qué no

| Lo mide el script | Lo tiene que leer alguien (o el asistente) |
|---|---|
| Fuente y tamaño del cuerpo | Registro técnico por sección (introducción sin implementación, objetivos que no sean tareas) |
| Interlineado real (no el del menú) | Siglas sin definir, anglicismos sin cursiva, ortografía |
| Justificado | Bibliografía bien formada y citada desde el texto |
| Índice ↔ títulos, página por página | Figuras legibles, figuras incrustadas (no links) |
| Epígrafes debajo, numeración, referencias desde el texto | Coloquialismos y aclaraciones de chat |
| Imágenes y tablas sin epígrafe | Consistencia de estilos de títulos y listas |
| Candidatos de 1ª persona / voseo | Si el candidato es de verdad primera persona |

## Umbrales que conviene saber

- **Interlineado**: se mide salto entre líneas ÷ tamaño de fuente. Simple ≈ 1,15–1,4;
  **1,5 ≈ 1,5–1,75**; doble ≈ 2,3. El "1,15" por defecto de Google Docs mide 1,33× y el
  `\linespread{1.15}` de LaTeX 1,39×: los dos son simple. El 1,5 real: Formato → Interlineado
  → 1,5 en Docs; `\usepackage{setspace}` + `\onehalfspacing` en LaTeX.
- **Fuente**: Arial, Times New Roman o Libertinus (la de Typst). Computer Modern (LaTeX por
  defecto), Calibri, Cambria y Roboto no.
- **Epígrafes**: debajo, también en tablas. LaTeX y Typst los ponen arriba por defecto en
  tablas; la rúbrica dice cómo cambiarlo.
