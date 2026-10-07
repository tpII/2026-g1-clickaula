# Rúbrica de forma — entregas de Taller de Proyecto II

Criterios de formato con los que se corrigen las cuatro entregas (plan de proyecto, informe
de avance 1, informe de avance 2, entrega final). Esta pasada mira la **forma**: que el
documento sea un informe de ingeniería. El contenido técnico se evalúa aparte.

## Cómo leer el resultado

- **❌ Corregir**: incumple un criterio verificable. Hay que arreglarlo antes de entregar.
- **❓ Revisar**: la herramienta no puede decidir sola (si una frase es coloquial, si un
  bloque es tabla o lista, si una figura vectorial tiene epígrafe). Lo mira una persona.
- **ℹ️ Informativo**: no se penaliza (anexo ausente, fuentes reducidas en tablas o código,
  numeración impresa que arranca después del índice).

La corrección docente separa forma de contenido. Objetivos poco medibles, cronograma sin
fechas intermedias o requerimientos sin cota son contenido y no se marcan en la pasada de
forma. Sí son forma: una figura sin párrafo que la explique, una sección que consiste solo en
una figura, y una figura reemplazada por un link externo (Canva, Drive, Miro) — el informe es
un documento autocontenido.

## 1. Estructura

| Elemento | Qué se espera | Errores típicos |
|---|---|---|
| Carátula | Materia, tipo de entrega, nombre del proyecto y número de grupo, integrantes con legajo, fecha completa (día, mes, año). Sola en la página 1. La plantilla de la cátedra (bloque "TALLER DE PROYECTO 2 / INGENIERÍA EN COMPUTACIÓN" con logos) está bien. | Falta la fecha o solo dice el año; falta el legajo o el número de grupo; la carátula comparte página con la introducción. |
| Índice general | Todas las secciones y subsecciones, con número de página. | Índice a mano desactualizado (páginas corridas); subsecciones que faltan; índice que lista "Anexo" inexistente. |
| Índice de figuras | Una entrada por figura: número, leyenda, página. | Falta aunque haya figuras; leyendas del índice distintas de los epígrafes. |
| Índice de tablas | Ídem para tablas. | Se omite porque "hay una sola tabla" (igual va). |
| Bibliografía | Fuentes con autor/título, URL o editorial y fecha de consulta. Lo citado en el texto está en la lista. | Ausente; solo URLs sueltas; datasheets mencionados y no listados. |
| Anexo | Opcional. Código extenso, datasheets, esquemáticos grandes. | Poner en el cuerpo lo que debería ir en anexo (páginas de código). |
| Números de página | En todas las páginas salvo la carátula; sin ellos el índice no sirve. | Sin numerar; numeración que arranca en la carátula y el índice dice otra cosa. |
| Encabezado y pie | Opcionales. Si los hay, consistentes: misma materia, proyecto y fecha en todas las páginas. | Pie de plantilla con fecha vieja; encabezado de otra entrega. |

Un documento armado como presentación (una idea por página, fuentes grandes, sin párrafos) no
es un informe.

## 2. Lenguaje

**No va**: primera persona singular y plural ("creo", "decidimos", "nuestro sistema", "nos
pareció"), voseo y tuteo ("vos", "podés", "fijate", "tú", "puedes"), coloquialismos ("re",
"medio", "un montón", "la idea es que", "está bueno", "básicamente", "capaz", "contando a
ojo", "hasta que alguien lo note"), apelaciones al lector ("como se puede ver arriba, ¿no?"),
aclaraciones de chat entre paréntesis ("(lo que se espera de la interfaz)").

**Sí va**: impersonal con "se" ("se propone", "se implementará"), tercera persona ("el grupo
definió", "el sistema expone"), voz técnica: verbos precisos (implementar, exponer, validar,
dimensionar) y sustantivos concretos (latencia, throughput, consumo en reposo).

**Siglas.** Toda sigla se desarrolla en su primer uso — "Speech-to-Text (STT)", "producto
mínimo viable (MVP)" — o se referencia. Excepciones de uso general que no hace falta definir:
PC, USB, LED, RAM, CPU, HTTP, WiFi, ID, URL, PDF, GPS. Sí se definen las del dominio: GPIO,
GND, PWM, MQTT, QoS, TSDB, MCP, PIR, STT, TTS, OCR, LLM, API, JSON.

**Anglicismos.** Los términos en inglés van en *cursiva*, siempre y de la misma manera. No se
exige el equivalente en castellano cuando es vocabulario del protocolo o de la herramienta
(*broker*, *topic*, *payload*, *dashboard*, *pipeline*). Sí se corrige el anglicismo adaptado
a la castellana ("hosteo", "moqueado", "scrapear", "por default"): se reemplaza por el verbo
en castellano o por el término en inglés en cursiva.

**Ortografía.** Tildes faltantes y erratas ("Suscribiendose", "compilacion", "el nodo pública"
por "publica", "Proximos") se marcan. Pasar el corrector antes de exportar.

**Objetivos redactados como tareas** con librerías, lenguajes o productos ("implementar con
FastMCP en Python", "usar Claude para…") no corresponde: los objetivos dicen qué se logra; el
cómo va en Identificación de partes.

**Listas con viñetas.** Si los ítems son fragmentos que completan la frase introductoria ("Se
espera haber completado: · flujo de captura; · conversión STT; …"), van en minúscula,
separados por punto y coma y con punto final en el último. Si cada ítem es una oración
completa, van con mayúscula inicial y punto. Cualquiera de las dos es correcta; lo que se
corrige es mezclarlas dentro del mismo documento. Las etiquetas en negrita al inicio de los
ítems también se unifican (todas con dos puntos o ninguna).

Cuando la herramienta marca un "candidato" de primera persona, hay que leer la oración
completa: "los extremos del cable" no es primera persona; "que establezcamos" sí.

### Registro esperado por sección

| Sección | Qué debe decir | Fuera de registro |
|---|---|---|
| Introducción | Problema, contexto, para quién, por qué importa. Es una introducción de informe: sin especificación técnica, salvo que el proyecto lo requiera para entenderse. | Detalles de implementación, nombres de librerías, formatos de datos, código. |
| Objetivos | General (uno, verbo en infinitivo) y particulares. | Objetivos redactados como tareas ("comprar la Raspberry") o como deseos ("que ande bien"). |
| Requerimientos / funcionalidad | Enunciados numerados (RF01…, RNF01…), separados en funcionales y no funcionales. | Narración ("primero el usuario entra y después…"); viñetas sin numerar. |
| Esquema gráfico | Figura del sistema con epígrafe y párrafo que la explique bloque por bloque. | Figura sin explicación; explicación sin figura. |
| Identificación de partes (hardware, alimentación, software) | Listado con cantidades, modelos, tensión/corriente, justificación técnica de cada elección. | "Vamos a usar un ESP32 porque es lo que tenemos". |
| Cronograma / avances | Hitos, dependencias, qué se entrega en cada informe. | Justificaciones de diseño, promesas vagas ("si llegamos"). |
| Informe de avance (IA1/IA2) | Qué se hizo contra lo planificado, desvíos y causas, evidencia (mediciones, capturas con epígrafe), replanificación. | Diario personal ("esta semana no pudimos"), excusas sin plan. |
| Entrega final | Descripción completa del sistema, pruebas y resultados, conclusiones, trabajo futuro, manual de uso. | Conclusiones emotivas ("aprendimos mucho"), resultados sin números. |

## 3. Títulos y subtítulos

- Jerarquía visible: sección (más grande o numerada 1., 2.), subsección (2.1, o tamaño
  intermedio), sub-subsección si hace falta. Mismo nivel = mismo estilo en todo el documento.
- El texto del título en el cuerpo y en el índice es el mismo (mayúsculas, numeración,
  puntuación incluidas) y la página coincide (se admite numeración impresa que arranca
  después de carátula e índice, si es consistente).
- Los títulos no terminan en dos puntos ni en punto.
- No hay títulos "huérfanos" (al final de una página con el contenido en la siguiente).

## 4. Figuras y tablas

- Toda figura y toda tabla tiene epígrafe **debajo**, con numeración correlativa y leyenda
  descriptiva: "Figura 3. Arquitectura de mensajería MQTT entre nodos e intermediario".
  También las tablas, aunque LaTeX, Typst y varias guías de estilo pongan el de las tablas
  arriba por defecto: acá el criterio es debajo para las dos (ver sección 6 para cambiarlo).
- Numeración independiente para figuras y para tablas, ambas desde 1. Si la herramienta
  rotula "Cuadro", unificar con lo que dice el texto ("Tabla").
- El texto las referencia por número ("como muestra la Figura 2") antes o después de que
  aparezcan.
- El índice de figuras y el índice de tablas reproducen las leyendas y las páginas.
- Toda figura va incrustada en el PDF, legible al tamaño de impresión (rótulos internos que
  no se leen: exportar a mayor resolución o partir la figura). Un link a un diagrama externo
  no reemplaza a la figura.
- Diagramación: páginas mayormente vacías porque una imagen o tabla se fue entera a la
  siguiente es un punto menor, pero se marca (ajustar tamaño o permitir que el texto fluya).
- Los links (video, repositorio, drive) van con la URL visible en el texto, no solo como
  "chip" o texto con hipervínculo: el PDF impreso o pasado por un visor sin links la pierde.
- Las capturas de pantalla y los esquemáticos son figuras; los listados con columnas son
  tablas. Un bloque de código no es ni una cosa ni la otra (puede ir en anexo o con formato
  de código y fuente monoespaciada).

## 5. Tipografía y párrafo

- Cuerpo en **Arial, Times New Roman o Libertinus, 12 pt**. Equivalentes métricos (Liberation
  Serif/Sans) se aceptan; Calibri/Carlito, Cambria, Roboto, Computer Modern (la fuente por
  defecto de LaTeX), etc., no.
- Tamaños menores solo en epígrafes, tablas, notas y código (≤ 11 pt está bien ahí).
- **Interlineado 1,5** en los párrafos del cuerpo. Listas y tablas pueden ir a simple.
- **Justificado** en los párrafos. Listas, tablas y títulos no necesitan justificarse.
- Lo que se evalúa es el resultado impreso. El "1,15" por defecto de Google Docs y el
  `\linespread{1.15}` de LaTeX miden 1,33–1,39× el tamaño de fuente: eso es interlineado
  simple, aunque el menú diga otra cosa. El 1,5 real mide entre 1,5× (Typst) y 1,72× (Word).

## 6. Cómo se corrige en cada herramienta

| Qué | Google Docs | Word / LibreOffice | LaTeX | Typst |
|---|---|---|---|---|
| Índice general | Insertar → Índice (títulos con estilos Título 1/2) | Referencias → Tabla de contenido | `\tableofcontents` | `#outline()` |
| Índice de figuras / tablas | No es nativo: lista a mano con número, leyenda y página, o complemento "Table of Contents" con estilo propio para epígrafes | Referencias → Insertar tabla de ilustraciones (usa Insertar título) | `\listoffigures` / `\listoftables` | `#outline(target: figure.where(kind: image))` / `kind: table` |
| Epígrafe debajo | Párrafo centrado debajo, con un estilo propio ("Epígrafe") para poder listarlo | Referencias → Insertar título → posición "Debajo de la selección" | `\caption` después del `tabular`/`includegraphics`; `\usepackage[spanish,es-tabla]{babel}` para "Tabla" | `#show figure.where(kind: table): set figure.caption(position: bottom)` |
| Referencia por número | A mano ("la Tabla 2") | Referencias → Referencia cruzada | `\ref` / `\autoref` | `@etiqueta` |
| Fuente y tamaño | Estilos → Texto normal → Times/Arial 12 y "Actualizar para que coincida" | Estilos → Normal | `\usepackage{newtxtext}` o `\usepackage{libertinus}`; `\documentclass[12pt]` | `#set text(font: "Times New Roman", size: 12pt)` |
| Interlineado 1,5 | Formato → Interlineado → 1,5 (el "1,15" por defecto es simple) | Párrafo → Interlineado 1,5 | `\usepackage{setspace}` `\onehalfspacing` (`\linespread{1.15}` NO es 1,5) | `#set par(leading: 1.5em)` aprox.; medir |
| Justificado | Ctrl+Shift+J | Ctrl+J | por defecto | `#set par(justify: true)` |
| Números de página | Insertar → Números de página | Insertar → Número de página | por defecto | `#set page(numbering: "1")` |
| Flotante que deja media página vacía | Reducir la imagen o mover el párrafo | Ídem | `\begin{table}[htbp]`, o `[H]` con `float` | `#place` / reducir |
