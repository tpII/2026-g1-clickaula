# Chequeo de formato — G1 ClickAula — Informe de Avance (octubre)

Archivo: `Informe_Avance_G1_ClickAula.pdf` · 25 páginas · generado con Google Docs · Chequeo: 2026-10-07
Estado: **con 12 puntos a corregir**

## Resumen

La tipografía y el lenguaje están en regla y son lo más difícil de arreglar a último momento:
Times New Roman 12 pt, interlineado 1,5 real (1,72× el tamaño de fuente), 93 % de las líneas
justificadas, y cero apariciones de primera persona o voseo en todo el cuerpo. Las nueve
tablas y las siete figuras tienen epígrafe numerado debajo y están referenciadas desde el
texto. La bibliografía existe, está completa y tiene fecha de consulta en cada entrada. La
sección 1.2 documenta de manera explícita las correcciones aplicadas tras la devolución del
Plan, lo que facilita la corrección.

Lo que falta es, sobre todo, cierre. El documento tiene 16 marcadores `[completar]` sin
resolver: toda la columna de costos de la Tabla 4, el total del presupuesto y los tres enlaces
de la sección 5.3. Con eso, las secciones "Materiales y Presupuesto" y "Enlaces" no están
entregables. Después hay un conjunto de desajustes entre los índices y el cuerpo (números de
tabla cruzados, cuatro páginas mal), una cita que apunta a la referencia equivocada, y el
registro de los textos que están *dentro* de las figuras, que quedó sin revisar y contrasta con
el del cuerpo.

## Puntos a corregir

1. **Marcadores `[completar]` sin resolver — 16 en total.** Es lo más visible y lo primero que
   mira la corrección.
   - Tabla 4 (p.8): las 12 celdas de "Costo unitario", las 12 de "Referencia" y la celda
     "Total". La sección se titula "Materiales y Presupuesto" y hoy no tiene presupuesto.
   - Sección 5.3 (p.24): "Video de demostración. [completar con el enlace al video]",
     "Bitácora del proyecto. [completar con el enlace a la bitácora]", "Repositorio de código
     fuente. [completar con el enlace al repositorio]".
   - Al cargar los tres enlaces, la URL tiene que quedar **visible como texto**, no como un
     "chip" de Google Docs ni como palabra con hipervínculo: el PDF impreso o abierto en un
     visor sin links la pierde. En Google Docs, pegar la URL y elegir "Mantener como texto sin
     formato" cuando ofrece convertirla en chip.

2. **Índice de tablas: los números 6, 7 y 8 no coinciden con el cuerpo** (p.3). El índice dice:

   | Índice de tablas (p.3) | Cuerpo real |
   |---|---|
   | Tabla 6. Requerimientos de consumo… p.14 | Tabla 6. Grado de avance por componente (p.13) |
   | Tabla 7. Grado de avance por componente… p.13 | Tabla 7. Estado de las tareas comprometidas (p.13) |
   | Tabla 8. Estado de las tareas comprometidas… p.13 | Tabla 8. Requerimientos de consumo (p.14) |

   El cuerpo está bien numerado y correlativo; el error está sólo en el índice, que además
   quedó desordenado por página (14, 13, 13). Reescribir esas tres entradas en el orden 6, 7, 8
   con las leyendas y páginas del cuerpo.

3. **Índice general: tres páginas equivocadas** (p.2). La numeración impresa coincide con la
   del PDF, así que no hay corrimiento que justifique la diferencia:
   - «3.3 Protocolo de mensajería» → el índice dice 11, está en la **12**.
   - «5.3 Enlaces» → el índice dice 23, está en la **24**.
   - «6.- Bibliografía» → el índice dice 24, está en la **25**.

4. **Índice de figuras: una página equivocada** (p.2). «Figura 6. Resultados de una pregunta…»
   → el índice dice 22, el epígrafe está en la **23**.

5. **La referencia [7] está mal aplicada** (p.19). En 4.5, la frase «existen reportes de bloqueo
   del controlador inalámbrico de la Raspberry Pi 3 en torno a los veinte dispositivos
   asociados, limitación de hardware que se resuelve con un adaptador externo [7]» cita el
   manual de configuración de Mosquitto, que no habla de eso. El propio informe lo reconoce en
   la nota al pie de la bibliografía, pero la nota no arregla el marcador: el lector ve una
   afirmación respaldada por una fuente que no la respalda. Dos arreglos:
   - Quitar el `[7]` de esa frase, o reemplazarlo por la cita real (el issue del repositorio del
     kernel de Raspberry Pi y los hilos del foro oficial, que es de donde sale el dato).
   - Agregar `[7]` donde sí corresponde: el párrafo «Configuración por omisión del intermediario
     de mensajes» (pp.18-19), que hoy describe el comportamiento de Mosquitto 2 sin citar nada.

6. **Carátula sin fecha completa** (p.1). Dice «Octubre de 2026»; se pide día, mes y año.
   Agregar el día de entrega. En la misma página, faltan dos tildes en los nombres: «Valentin
   Ventos» → Valentín, «Joaquin Labarta» → Joaquín.

7. **Las leyendas del índice de figuras no reproducen los epígrafes, y de forma despareja**
   (p.2). Las Figuras 1, 2 y 3 aparecen truncadas antes de los dos puntos («Figura 1. Esquema
   general de ClickAula», cuando el epígrafe sigue «: nodos publicadores, punto de acceso e
   intermediario de mensajes, y aplicación suscriptora»), mientras que las Figuras 4, 6 y 7
   figuran con la leyenda completa. Unificar: o todas completas, o todas recortadas con el mismo
   criterio. Lo mismo vale para el índice de tablas, que omite el punto final de los epígrafes.

8. **El registro de los textos dentro de las figuras no se revisó.** El cuerpo está impecable,
   pero las imágenes contradicen ese registro y son parte del documento:
   - **Voseo en la Figura 3** (p.21): la interfaz muestra «Escribí la pregunta» y, dos veces,
     «Opción (podés dejarla vacía)».
   - **«broker» en las Figuras 1, 3, 4 y 6** (pp.10, 21, 23): en los rótulos del diagrama
     («Mosquitto (broker)») y en el encabezado de la aplicación («broker conectado»), mientras
     el cuerpo dice siempre «intermediario de mensajes».
   - **«protoboard» y «pull-ups» en la Figura 2** (p.11), cuando el cuerpo usa «placa de
     pruebas» y «resistencias de elevación interna».
   - **Coloquialismo en la Figura 2**: «el botón sólo une sus dos patas cuando se la aprieta».
   Las Figuras 1 y 2 son de producción propia, así que se regeneran. Las capturas de pantalla
   (3, 4, 6) dependen de la interfaz: el arreglo de fondo es cambiar los textos de la aplicación
   y volver a capturar, lo que además deja la interfaz consistente con el informe.

9. **«firmware» va en cursiva una sola vez de seis.** Está en cursiva en p.5 y en redonda en
   p.7, p.12, p.15 (dos veces, una en el título 4.4.1) y p.24. «hardware» y «software» están
   siempre en redonda. Elegir un criterio y aplicarlo a las tres palabras en todo el documento;
   el defecto concreto es la inconsistencia, no cuál de los dos criterios se elija.

10. **Legibilidad de la Figura 2** (p.11). El diagrama principal se lee bien, pero el bloque
    «3 · Resumen de conexiones» y la línea de notas al pie quedan muy por debajo del tamaño
    mínimo legible al imprimir. Dos opciones: exportar la figura a mayor resolución y ampliarla,
    o sacar ese resumen de la imagen y ponerlo como tabla real del informe, con su epígrafe
    «Tabla N» — que además lo vuelve seleccionable y buscable.

11. **Tres páginas mayormente vacías.** La p.9 queda con tres líneas (95 % en blanco) por el
    cierre de 2.3; la p.22 con poco menos de la mitad vacía porque la Figura 6 se fue entera a
    la p.23; la p.24 al 75 % por la sección 5.3. Es un punto menor, pero se marca. Ajustar el
    tamaño de la Figura 6 para que entre en la p.22, o dejar que el texto fluya.

12. **Las sub-subsecciones 4.4.1 a 4.4.4 están a 12 pt**, el mismo cuerpo del texto, y sólo se
    distinguen por la negrita. Las secciones van a 15 pt y las subsecciones a 13 pt. Bajar el
    nivel 3 a un escalón intermedio propio (12,5 pt, o 12 pt en versalitas) haría la jerarquía
    visible de un vistazo. Es lo más menor de la lista.

## Para que lo mire alguien del grupo

- **Carátula sin la plantilla de la cátedra** (p.1). El Plan de Proyecto usaba el bloque
  «TALLER DE PROYECTO 2 / INGENIERÍA EN COMPUTACIÓN» con los logos de la Facultad y de la UNLP;
  este informe no lo tiene. La plantilla no es obligatoria según el criterio de forma, pero si
  la cátedra la pide para todas las entregas, conviene recuperarla del Plan.
- **Los cinco bloques de código en el cuerpo** (pp.15-18, en Consolas 8,5 pt). Son extractos
  cortos y cada uno viene explicado, así que no son "páginas de código" que deberían ir a un
  anexo. Además los títulos de 4.4 parecen venir de la plantilla del informe. Confirmar contra
  la plantilla que ese es el lugar previsto.
- **p.24 y p.25**: el análisis automático marcó interlineado y justificado fuera de norma en
  esas dos páginas. Mirándolas, parecen falsos positivos — son páginas con pocos párrafos
  largos (5.3 son tres líneas sueltas; la bibliografía son entradas con sangría), y la medición
  no tuvo líneas suficientes. Verificar a ojo y, si se ven bien, ignorar.

## Lo que está bien y hay que conservar

- **El lenguaje.** Cero apariciones de primera persona, voseo o coloquialismos en 25 páginas.
  Construcciones impersonales consistentes («se decidió», «se optó», «se resolvió», «el grupo no
  dispone»). Es lo que más pesa en la corrección y lo más caro de arreglar después.
- **Las siglas**, todas definidas en su primer uso: MQTT (Message Queuing Telemetry Transport),
  QoS (Quality of Service), IoT (Internet of Things), SSE (Server-Sent Events).
- **Tipografía**: Times New Roman 12 pt, interlineado 1,5 medido en 1,72× (el valor real de
  Word/Docs, no el «1,15» que se confunde con 1,5), justificado en el 93 % de las líneas. Los
  tamaños menores aparecen sólo donde corresponde: epígrafes 9,5 pt, tablas 10 pt y código 8,5 pt.
- **Epígrafes**: los 16 (9 tablas + 7 figuras) están debajo del objeto, numerados, con leyenda
  descriptiva y referenciados por número desde el texto. Las dos numeraciones son independientes
  y correlativas desde 1.
- **Bibliografía**: siete entradas con autor, título en cursiva, URL y fecha de consulta.
- **Requerimientos numerados** (RF-1 a RF-7, RNF-1 a RNF-6, RT-1 a RT-5) y efectivamente
  referenciados desde el texto (RNF-1, RNF-4, RT-1, RT-5, RF-2, RF-3).
- **Números de página** en todas las páginas salvo la carátula, coincidentes con los índices.
- **La sección 1.2** enumera una por una las correcciones aplicadas tras la devolución del Plan.

## Detalle por criterio

| Criterio | Estado | Observación |
|---|---|---|
| Carátula | ❌ | Materia, tipo de entrega, proyecto, grupo e integrantes con legajo, sola en la p.1. Falta el día en la fecha; faltan tildes en dos nombres; sin la plantilla de la cátedra (ver punto 6 y "para que lo mire alguien del grupo"). |
| Índice general y correspondencia con títulos | ❌ | 33 entradas, jerarquía completa; 27 coinciden exactamente. Tres páginas mal: 3.3, 5.3 y 6 (punto 3). |
| Índice de figuras / Índice de tablas | ❌ | Ambos presentes. Tablas 6-8 cruzadas (punto 2); Figura 6 con página equivocada (punto 4); leyendas truncadas de manera despareja (punto 7). |
| Epígrafes debajo de figuras y tablas, correlativos con el índice | ✅ | Los 16 debajo del objeto, numerados y referenciados desde el texto. |
| Bibliografía | ❌ | Presente y bien formada (7 entradas con fecha de consulta), pero la cita [7] del cuerpo apunta a la fuente equivocada (punto 5). |
| Anexo (opcional) | ℹ️ | No hay. No se penaliza. |
| Números de página | ✅ | En todas las páginas salvo la carátula; la numeración impresa coincide con la del PDF. |
| Lenguaje: sin 1ª persona ni voseo | ❌ | El cuerpo está impecable. El voseo aparece sólo dentro de la captura de la Figura 3 (punto 8). |
| Registro adecuado por sección (siglas, anglicismos, ortografía) | ❌ | Siglas definidas y registro correcto en el cuerpo. Desprolijidades: «firmware» en cursiva 1 de 6 veces (punto 9); «broker», «protoboard», «pull-ups» y un coloquialismo dentro de las figuras (punto 8); dos tildes en la carátula (punto 6). |
| Títulos y subtítulos identificados y jerarquizados | ⚠️ | Esquema numerado consistente, ningún título termina en punto ni dos puntos, sin títulos huérfanos. El nivel 3 (4.4.x) usa el mismo cuerpo de 12 pt (punto 12). |
| Fuente Arial / Times New Roman / Libertinus 12 pt | ✅ | Times New Roman 12 pt en el 72 % de los caracteres. Consolas 8,5 pt sólo en los bloques de código, admitido. |
| Interlineado 1,5 | ✅ | 20,7 pt sobre fuente de 12 pt = 1,72×, que es el 1,5 real. Las excepciones son índices y tablas, admitidas. |
| Texto justificado | ✅ | 93 % de las líneas largas terminan en el margen derecho. |

### Diagramación (punto menor)

| Página | Ocupación | Causa |
|---|---|---|
| 9 | ~5 % | Cierre de la sección 2.3, tres líneas. |
| 22 | ~55 % | La Figura 6 no entró y se fue entera a la p.23. |
| 24 | ~25 % | Sección 5.3 Enlaces. |
