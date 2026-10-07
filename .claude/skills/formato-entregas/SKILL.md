---
name: formato-entregas
description: Chequea el formato de una entrega de Taller de Proyecto II (plan de proyecto, informe de avance 1 y 2, entrega final) antes de mandarla, con los mismos criterios con que la corrige la cátedra. Verifica estructura (carátula, índice, índices de figuras y tablas, bibliografía), lenguaje (sin primera persona ni voseo, registro técnico, siglas definidas, anglicismos en cursiva), títulos contra el índice, epígrafes debajo de figuras y tablas, y tipografía (Arial, Times New Roman o Libertinus 12 pt, interlineado 1,5, justificado). Devuelve la lista de lo que hay que corregir, con página y cómo arreglarlo en la herramienta que usa el grupo. Usar SIEMPRE que alguien pida revisar, chequear, validar o "ver si está bien el formato" de un informe, plan o entrega en PDF de la materia, aunque solo diga "fijate si esto pasa" o pase el archivo.
---

# Chequeo de formato — entregas de Taller de Proyecto II

Antes de evaluar el contenido, la cátedra corrige la **forma**: que el documento sea un
informe de ingeniería y no un chat. Esta skill hace esa misma pasada sobre el PDF del grupo
para que lo que se entregue ya esté en regla. Los criterios están en
`references/rubrica.md`: son los mismos con los que se corrige.

El resultado es una lista de cosas concretas para arreglar, con página y con la instrucción
para la herramienta que usa el grupo (Google Docs, Word, LaTeX, Typst). Lo que la skill no
puede decidir sola queda separado, para que lo mire una persona del grupo.

## Procedimiento

### 1. Pasada mecánica

```bash
python3 <skill>/scripts/analizar_pdf.py "<ruta al pdf>"
```

Requiere Python 3 y poppler (`pdftohtml`, `pdftotext`, `pdfinfo` en el PATH; ver README).
Mide lo que un ojo humano no mide bien:

- familia y tamaño de la fuente del cuerpo (precisión ≈ 0,3 pt);
- interlineado: salto entre líneas / tamaño de fuente. Simple ≈ 1,15–1,4; **1,5 ≈ 1,5–1,75**;
  doble ≈ 2,3. El "1,15" de Google Docs y el `\linespread{1.15}` de LaTeX caen en simple;
- justificado (líneas largas que terminan en el margen, sin contar viñetas ni últimas líneas);
- títulos por tamaño y negrita; entradas del índice y su cotejo con los títulos (tolera que
  la numeración impresa arranque después de carátula e índice);
- epígrafes «Figura N» / «Tabla N», si están debajo de una imagen o tabla, si el texto los
  referencia por número, y si hay imágenes o tablas sin epígrafe;
- candidatos de lenguaje: pronombres, verbos en -amos/-emos/-imos, voseo;
- con qué herramienta se generó el PDF.

Guardar la salida en un archivo temporal. Conviene también `pdftotext -layout "<pdf>"
salida.txt` para buscar frases y citar textualmente.

Confiar en el script para fuente, tamaño, interlineado y presencia o ausencia de secciones.
Tratar como **pistas** lo que marca con ❓ o llama "candidato": los verbos en primera
persona plural tienen falsos positivos ("los extremos"), y las tablas se detectan por
geometría.

### 2. Lectura del PDF

Leer el PDF completo (de a 10–20 páginas) para lo que necesita criterio:

- **Lenguaje y registro por sección**: es lo que más pesa y lo que el script menos ve. Leer
  cada sección con la pregunta "¿esto lo firmaría un ingeniero ante un cliente?". Marcar
  primera persona, voseo/tuteo, coloquialismos, aclaraciones de chat, anglicismos sin
  cursiva, siglas sin definir en su primer uso, y registro inadecuado a la sección (una
  introducción no lleva detalles de implementación; los objetivos no son tareas con
  librerías). Anotar página y cita corta.
- **Carátula**: materia, tipo de entrega, proyecto y grupo, integrantes con legajo, fecha
  completa.
- **Títulos vs. índice** cuando el script duda; jerarquía visible y consistente.
- **Figuras y tablas**: epígrafe numerado debajo de todas, referencia desde el texto,
  índices de figuras y tablas que coincidan, figuras legibles e incrustadas (no links).
- **Bibliografía**: existencia y formato mínimo; que lo citado en el texto esté en la lista.
- Cualquier ❓ o "parcial" del script.

### 3. El informe de chequeo

Escribir `<nombre-del-pdf>_chequeo.md` junto al PDF, con esta estructura:

```markdown
# Chequeo de formato — <Grupo> <Proyecto> — <Instancia>

Archivo: `<pdf>` · <páginas> páginas · generado con <herramienta> · Chequeo: <AAAA-MM-DD>
Estado: **listo para entregar** / **con N puntos a corregir**

## Resumen
<Qué está en regla; qué falta o se desvía, agrupado. 4–6 líneas.>

## Puntos a corregir
<Lista numerada. Cada punto: qué está mal, dónde (página, sección, cita corta), qué se
espera y cómo se arregla en la herramienta del grupo (sección 6 de la rúbrica). Ordenar de
lo estructural a lo tipográfico. Agrupar lo repetitivo ("primera persona en 14 lugares:
p.2 «decidimos», p.4 «nuestro», …") en un solo punto con todos los lugares.>

## Para que lo mire alguien del grupo
<Solo lo que la skill no pudo resolver: página, qué mirar y por qué hay duda.>

## Lo que está bien y hay que conservar
<Breve, concreto.>

## Detalle por criterio
| Criterio | Estado | Observación |
| Carátula | ✅/❌ | … |
| Índice general y correspondencia con títulos | | |
| Índice de figuras / Índice de tablas | | |
| Epígrafes debajo de figuras y tablas, correlativos con el índice | | |
| Bibliografía | | |
| Anexo (opcional) | ✅/ℹ️ | |
| Números de página | | |
| Lenguaje: sin 1ª persona ni voseo | | |
| Registro adecuado por sección (siglas, anglicismos, ortografía) | | |
| Títulos y subtítulos identificados y jerarquizados | | |
| Fuente Arial / Times New Roman / Libertinus 12 pt | | |
| Interlineado 1,5 | | |
| Texto justificado | | |
```

Ser concreto y útil, no severo: la lista es para arreglar el documento, no para calificar a
nadie. No opinar sobre la calidad técnica del proyecto ni sobre la redacción más allá del
registro. Si el documento pasa todo, decirlo en una línea y listar igual lo que está bien.

## Criterios rápidos

- **Estructura**: carátula, índice general, índice de figuras, índice de tablas,
  bibliografía, números de página; anexo opcional. Un informe con figuras y sin índice de
  figuras es ❌, no ❓. Va aunque haya una sola figura o una sola tabla.
- **Lenguaje**: impersonal o tercera persona ("se propone", "el sistema permite", "el grupo
  definió"); nada de "nosotros/nuestro/decidimos", nada de "vos/podés/fijate"; siglas
  definidas en su primer uso; términos en inglés en cursiva; sin coloquialismos.
- **Títulos**: jerarquía visible y coincidente con el índice, mismas palabras y misma página.
- **Figuras y tablas**: epígrafe **debajo** (también en tablas), numerado, con leyenda;
  referencia desde el texto; índices de figuras y tablas correlativos; figuras legibles e
  incrustadas; links con URL visible.
- **Tipografía**: Arial, Times New Roman o Libertinus, 12 pt en el cuerpo (epígrafes, tablas
  y código pueden ir más chicos), interlineado 1,5 real, párrafos justificados.
