# Chequeo de formato — G1 ClickAula — Informe de Avance (octubre)

Archivo: `Informe_Avance_G1_ClickAula.pdf` · 21 páginas · generado con Google Docs · Chequeo: 2026-10-07 (3ª pasada)
Estado: **con 12 puntos a corregir**

## Resumen

La parte de formato está casi resuelta. **Los tres índices se regeneraron y pasaron de 32
referencias de página equivocadas a una sola.** La pasada de cursivas quedó completa (*broker*
9/9, *hardware* 8/8, *protoboard* 7/7, *software* 5/5), la terminología se unificó —
«intermediario» desapareció del documento y «placas de pruebas» pasó a «*protoboards*» —, la
cita [7] quedó bien colocada y los tres marcadores `[completar]` se reemplazaron por enlaces.

El problema de esta pasada ya no es tipográfico sino de **coherencia**: la actualización del
estado de los materiales se aplicó en la sección 2.2 pero no se propagó al resto del informe, y
además introdujo una contradicción de fondo. **La Tabla 4 lista una Raspberry Pi 3 modelo B o B+
y una microSD de 16 GB; catorce líneas más abajo, la sección 2.2 dice que lo que se recibió es
una Raspberry Pi Zero W y una microSD de 32 GB.** Son dos placas distintas, y todo el informe
—el esquema de la Figura 1, los consumos de la Tabla 8, el análisis de obstáculos de la sección
4.5— está escrito sobre la Pi 3. Mientras tanto, cuatro secciones siguen diciendo que los
materiales no llegaron.

Hay además un desprendimiento tipográfico visible: el número «4.6» quedó pegado al final del
párrafo anterior y el título de esa sección perdió su numeración.

## Puntos a corregir

1. **Contradicción de materiales dentro de la misma página 8.** Es el punto más grave y el único
   que no se arregla moviendo texto.

   | | Tabla 4 (p.8) | Sección 2.2 (p.8) |
   |---|---|---|
   | Placa | Raspberry Pi 3 modelo B o B+ | **Raspberry Pi Zero W** |
   | Tarjeta | microSD de **16 GB** clase 10 | microSD de **32 GB** |
   | Adaptadores | no figuran | USB-A a microUSB, miniHDMI a HDMI |

   Si la placa efectivamente es una **Pi Zero W**, el cambio no es de inventario: arrastra al
   resto del informe y hay que decidirlo antes de seguir editando.
   - **Tabla 8** (p.13) estima «Raspberry Pi 3 en modo punto de acceso: 400 a 700 mA, pico 1,2 A»
     y de ahí sale el total del sistema. Una Zero W consume bastante menos; el número y el total
     quedan mal.
   - **Sección 4.5** (p.17) discute el bloqueo del controlador inalámbrico «en torno a los veinte
     dispositivos asociados». Ese dato se relevó para la Pi 3. Sobre otra placa hay que
     verificarlo de nuevo, y es justo el riesgo que condiciona el requerimiento RNF-2 (treinta
     pulsadores concurrentes).
   - **Figura 1** (p.9) rotula el bloque central como «Raspberry Pi 3».
   - **Tabla 4** debería listar lo que realmente se va a usar, y el total recalcularse.

   Si en cambio la Zero W es provisoria y la Pi 3 se compra igual, eso hay que escribirlo: hoy el
   informe no lo dice y las dos páginas se contradicen sin explicación.

2. **La sección 2.2 quedó incompleta y desconectada del resto.** El texto nuevo dice qué llegó,
   pero perdió cuatro cosas que tenía la versión anterior y que el informe necesita:
   - **la fecha de recepción** (sin ella no se puede fechar nada de la Tabla 9);
   - **si lo recibido cubre lo solicitado** — hoy el lector tiene que comparar a mano contra la
     Tabla 4 para descubrir que faltan ocho pulsadores, dos baterías, los gabinetes, la fuente y
     el estaño;
   - **el cruce a las secciones 4.2 y 4.6**, que la versión anterior tenía y que ataba el estado
     de provisión al cronograma;
   - **la consecuencia de «el resto de los componentes serán adquiridos por parte del grupo»**:
     sin fecha, sin monto y sin decir qué pasa con el total de $291.511 de la Tabla 4, que ahora
     incluye componentes provistos por la cátedra y componentes a cargo del grupo mezclados.

   Una redacción posible: «Los materiales fueron solicitados a la cátedra por los canales
   institucionales. El **[FECHA]** se recibió una parte del pedido: **[lista]**. Los componentes
   restantes de la Tabla 4 —**[lista]**— serán adquiridos por el grupo antes del **[FECHA]**, por
   un monto de **[$]**. El estado de provisión condiciona las tareas detalladas en las secciones
   4.2 y 4.6.»

3. **Cuatro lugares siguen diciendo que los materiales no llegaron**, en contradicción con 2.2:

   | Pág. | Dónde | Qué dice |
   |---|---|---|
   | 11 | Tabla 6, fila Raspberry Pi | «La implementación comienza con la recepción del equipamiento» |
   | 12 | 4.3, *Hardware* probado | «A la fecha de este informe no se ha probado ningún componente físico» — sin explicar por qué, ahora que hay dos NodeMCU y una placa disponibles |
   | 12 | 4.3, cierre | «deberán contrastarse con mediciones una vez que se disponga del equipamiento» |
   | 17-18 | 4.6, párrafo y Tabla 9 | «Las restantes comienzan con la recepción de los materiales», y siete filas con plazos «desde la recepción de los materiales» |

   La Tabla 9 además quedó internamente incoherente: la columna **Dependencia** dice «Ninguna»
   para *Firmware* del pulsador y para la configuración de la Raspberry Pi, pero la columna
   **Plazo previsto** de esas mismas filas sigue siendo relativa a un hito que, según «Ninguna»,
   ya no aplica. Con la fecha de recepción del punto 2, esos plazos se convierten en fechas de
   calendario y el problema desaparece.

4. **El número «4.6» quedó pegado al párrafo anterior** (p.17). El texto termina «…para
   seleccionar el de mejor calidad.**4.6**» y el título de la sección siguiente queda como
   «Planificación de las partes faltantes», sin numerar. En Google Docs: cortar el «4.6» del final
   del párrafo, poner el cursor delante de «Planificación» y escribirlo ahí, verificando que la
   línea tenga aplicado el estilo de subtítulo. Después hay que regenerar el índice general, que
   hoy muestra «4.6 Planificación de las partes faltantes» correctamente sólo por casualidad.

5. **La sección 4.5 perdió el problema de la demora.** La versión anterior abría con «Entrega de
   materiales pendiente. Es el factor de mayor impacto sobre el cronograma…» y ese párrafo se
   eliminó. Un informe de avance tiene que registrar los desvíos y sus causas: la demora ocurrió,
   condicionó cuatro tareas durante semanas y se resolvió parcialmente. Conviene reponerlo como
   problema resuelto, no borrarlo — sobre todo porque la sección 4.6 todavía habla de «la
   recepción de los materiales» como si el lector supiera de qué se trata.

6. **Los tres enlaces de la sección 5.3 no muestran la URL** (pp.20-21). Dicen «Link», «Enlace a
   BITACORA.md» y «Enlace al Repositorio», con el hipervínculo detrás. Las URLs están en el PDF
   —`https://drive.google.com/drive/u/0/folders/1e6SOL-…`,
   `https://github.com/tpII/2026-g1-clickaula/blob/main/BITACORA.md` y
   `https://github.com/tpII/2026-g1-clickaula`— pero son invisibles al imprimir o en un visor sin
   links, que es exactamente lo que la corrección señala. Hay que escribir la URL como texto
   visible. Además «Link» es un anglicismo evitable: «Video de demostración.
   https://drive.google.com/…».

7. **La sección 5.2 quedó reducida a una oración sin motivo** (p.20): «No se incluyen fotografías
   de partes físicas construidas.» La versión anterior explicaba por qué y remitía a la Figura 2;
   al recortarla se perdió una de las dos referencias a esa figura. O se explica el motivo y la
   fecha prevista de armado, o —si ya montaron algo con los dos NodeMCU recibidos— acá van las
   fotos, como Figuras 8 en adelante con su epígrafe y su entrada en el índice de figuras.

8. **Una página mal en el índice general** (p.2): «5.3 Enlaces» dice 21 y está en la **20**. Es la
   única de las 32 que quedó. Los índices de figuras y de tablas están ahora correctos en las
   dieciséis entradas.

9. **La entrada de la Figura 3 en el índice de figuras no coincide con el epígrafe** (p.2):

   - índice: «Editor de encuestas**:alta** de preguntas con sus opciones y **respuesta** correcta.»
   - epígrafe: «Editor de encuestas**: alta** de preguntas con sus opciones y **la** respuesta correcta.»

   Falta el espacio después de los dos puntos, falta «la», y sobra el punto final que las otras
   seis entradas no llevan.

10. **Residuos de puntuación y fechas:**
    - Tabla 7 (p.12): dos celdas sin punto final, «Falta implementar en Raspberry» y «Falta
      implementar en NodeMCU», mientras las otras cinco lo llevan. La primera además dice
      «Raspberry» a secas.
    - El epígrafe de la Tabla 7 sigue fijando el corte «al 6 de octubre de 2026» mientras la
      carátula dice 11 de octubre. Unificar la fecha de corte.
    - Tildes faltantes en la carátula (p.1): «Valentin Ventos» → Valentín, «Joaquin Labarta» →
      Joaquín. Viene de las dos pasadas anteriores.
    - Una aparición de *firmware* quedó en redonda: Tabla 6, p.11, «Comienza con el porteo de la
      simulación al firmware». Las otras ocho están en cursiva.

11. **Voseo dentro de la Figura 3** (p.18), sin cambios. La captura del editor sigue mostrando
    «Escribí la pregunta» y, dos veces, «Opción (podés dejarla vacía)». Es el único voseo del
    documento; se corrige cambiando los textos de la aplicación y volviendo a capturar.

12. **Las Figuras 1 y 2 siguen sin regenerarse**, y ahora el desfase con el cuerpo es mayor:
    - **Figura 1** (p.9) rotula el bloque central «Punto de acceso e **intermediario**». Esa
      palabra ya no existe en ninguna parte del texto —se reemplazó por *broker* en las nueve
      apariciones— así que la figura es el único lugar donde sobrevive. Y además rotula «Raspberry
      Pi 3» (ver punto 1).
    - **Figura 2** (p.10): «riel azul **del** protoboard» (el cuerpo usa femenino, «la
      *protoboard*»), «**pull-ups** internos» en plural y sin cursiva, y el coloquialismo «el
      botón sólo une sus dos patas cuando **se la aprieta**». Sigue además el problema de
      legibilidad del bloque «3 · Resumen de conexiones» y de la línea de notas al pie, que
      conviene sacar de la imagen y poner como tabla del informe.

## Para que lo mire alguien del grupo

- **El reclamo sobre el límite de dispositivos asociados** (p.17) sigue sin cita propia, con la
  nota de la bibliografía declarándolo. Es honesto, pero si la placa pasó a ser una Zero W el dato
  además cambia de objeto (ver punto 1).
- **La columna «Referencia» de la Tabla 4** dice «MercadoLibre» en las doce filas. Ahora que parte
  de los componentes llegó de la cátedra y parte la compra el grupo, esa columna podría distinguir
  las dos procedencias.
- **Carátula sin la plantilla de la cátedra**, igual que en las pasadas anteriores. El Plan de
  Proyecto usaba el bloque con los logos de la Facultad y la UNLP.
- **Los cinco bloques de código en el cuerpo** (pp.13-16, Consolas 8,5 pt): extractos cortos y
  explicados, no «páginas de código» de anexo. Confirmar contra la plantilla del informe.
- **Las sub-subsecciones 4.4.1 a 4.4.4 siguen a 12 pt**, el mismo cuerpo del texto. Punto menor.

## Lo que está bien y hay que conservar

- **Los tres índices**, regenerados y correctos salvo una entrada. El de figuras y el de tablas
  coinciden en las dieciséis páginas.
- **El lenguaje del cuerpo**: cero primera persona, voseo o coloquialismos en 21 páginas. El único
  voseo está dentro de una captura.
- **Las cursivas de anglicismos**, completas salvo una aparición, y aplicadas también en títulos,
  celdas de tabla y entradas en negrita, que era lo que faltaba en la pasada anterior.
- **La terminología unificada**: *broker* en las nueve apariciones, *protoboard* en las siete,
  sin convivencia con los términos viejos.
- **Tipografía**: Times New Roman 12 pt, interlineado 1,5 real (1,72×), justificado al 84 %.
- **Epígrafes**: los 16 debajo del objeto, numerados y referenciados desde el texto.
- **Bibliografía**: siete entradas con autor, título en cursiva, URL y fecha de consulta; la
  cita [7] ahora bien colocada, antes del punto y con espacio.
- **Números de página** coincidentes con los índices, sin corrimiento.

## Qué cambió desde el chequeo anterior

**Resuelto (8 de 11):**

| # anterior | Punto | Cómo quedó |
|---|---|---|
| 1 | 32 referencias de página mal | ✅ quedó **una** (punto 8) |
| 2 | Tres `[completar]` en 5.3 | ⚠️ reemplazados por enlaces, pero sin URL visible (punto 6) |
| 3 | Dos leyendas recortadas en el índice | ⚠️ Tabla 8 corregida; Figura 3 quedó distinta otra vez (punto 9) |
| 4 | Cursivas faltantes en títulos, negritas y celdas | ✅ siete de ocho resueltas; queda una (punto 10) |
| 5 | Términos viejos y nuevos conviviendo | ✅ «intermediario» y «placas de pruebas» eliminados |
| 6 | Cita [7] pegada al punto | ✅ «…sin salida a internet [7].» |
| 7 | Tildes en la carátula | ❌ sin cambios (punto 10) |
| 8 | Voseo en la Figura 3 | ❌ sin cambios (punto 11) |
| 9 | Figuras 1 y 2 sin regenerar | ❌ sin cambios, y el desfase creció (punto 12) |
| 10 | Legibilidad de la Figura 2 | ❌ sin cambios |
| 11 | Páginas con mucho blanco | ✅ el documento bajó de 23 a 21 páginas |

**Nuevo en esta pasada:** la contradicción Pi 3 / Pi Zero W y el inventario incompleto (puntos 1
y 2), las cuatro secciones que siguen diciendo que no llegaron los materiales (punto 3), el «4.6»
desprendido del título (punto 4), la pérdida del problema de la demora en 4.5 (punto 5), la
sección 5.2 reducida a una oración (punto 7) y los residuos de puntuación de la Tabla 7 (punto 10).

## Detalle por criterio

| Criterio | Estado | Observación |
|---|---|---|
| Carátula | ⚠️ | Completa y con fecha. Faltan dos tildes; sin la plantilla de la cátedra. |
| Índice general y correspondencia con títulos | ⚠️ | 30 entradas, textos coincidentes. Una página mal (punto 8); el título 4.6 perdió su número en el cuerpo (punto 4). |
| Índice de figuras / Índice de tablas | ⚠️ | Las dieciséis páginas correctas. Una leyenda que no coincide (punto 9). |
| Epígrafes debajo de figuras y tablas | ✅ | Los 16 debajo del objeto, numerados y referenciados desde el texto. |
| Bibliografía | ✅ | Siete entradas completas, las siete citadas desde el texto, cita bien colocada. |
| Anexo (opcional) | ℹ️ | No hay. No se penaliza. |
| Números de página | ✅ | En todas salvo la carátula; sin corrimiento respecto de los índices. |
| Lenguaje: sin 1ª persona ni voseo | ⚠️ | El cuerpo, impecable. El voseo sobrevive dentro de la Figura 3. |
| Registro adecuado por sección (siglas, anglicismos, ortografía) | ⚠️ | Cursivas y terminología resueltas salvo una aparición y «Link». Falta el texto de las Figuras 1 y 2. |
| Coherencia interna del contenido | ❌ | Tabla 4 contra 2.2 (punto 1); cuatro secciones desactualizadas (punto 3); Tabla 9 con dependencia y plazo incoherentes. |
| Títulos y subtítulos identificados y jerarquizados | ❌ | El «4.6» quedó en el párrafo anterior (punto 4). Nivel 3 al mismo cuerpo de 12 pt. |
| Fuente Arial / Times New Roman / Libertinus 12 pt | ✅ | Times New Roman 12 pt en el 70,5 % de los caracteres. Consolas 8,5 pt sólo en código. |
| Interlineado 1,5 | ✅ | 20,7 pt sobre 12 pt = 1,72×, que es el 1,5 real. |
| Texto justificado | ✅ | 84 % de las líneas largas terminan en el margen derecho. |
