# Contrato de mensajería — ClickAula

Este documento es la frontera entre el firmware del pulsador y la aplicación.
Mientras las dos partes respeten lo que dice acá, cada una puede cambiar por
dentro sin avisar.

**Versión 1 — 8 de septiembre de 2026.**

---

## Principio de diseño

El pulsador es un **publicador puro**. La aplicación no le manda absolutamente
nada, y el pulsador no se suscribe a ningún tema.

Esto es consecuencia de haber sacado el LED de confirmación: sin LED no hay
nada que encender, y sin nada que encender el pulsador tampoco necesita saber
si la votación está abierta. **Pulsa y publica, siempre.** Es la aplicación la
que decide si ese voto cuenta o se descarta.

Consecuencias prácticas para el firmware:

- No hay que implementar `subscribe()` ni ningún manejador de mensajes entrantes.
- No hay máquina de estados de la partida dentro del ESP8266.
- El voto **no lleva** el número de pregunta: se lo asigna el servidor según
  cuál estaba abierta al momento de recibirlo.
- El pulsador **no necesita reloj**. La marca de tiempo que ordena los votos
  (y por lo tanto define quién respondió primero) la pone la aplicación al
  recibir el mensaje.

---

## Identidad del pulsador

Cada pulsador tiene un `<id>` corto, estable entre reinicios y único.
Recomendación: derivarlo de la MAC del ESP8266.

```cpp
char id[7];
snprintf(id, sizeof(id), "%06x", ESP.getChipId());   // ej. "3a1f5c"
```

El `<id>` sólo se usa internamente. La aplicación le asigna a cada pulsador un
**número** estable la primera vez que lo escucha (`Pulsador 01`, `Pulsador 02`,
…), y ése es el que se muestra en pantalla.

---

## Temas

### 1. Voto — lo publica el pulsador

```
Tema:     aula/voto/<id>
QoS:      1
Retained: no
Payload:  {"opcion":"A","seq":41}
```

| Campo    | Tipo   | Detalle                                                     |
|----------|--------|-------------------------------------------------------------|
| `opcion` | string | `"A"`, `"B"`, `"C"` o `"D"`. A = rojo, B = azul, C = amarillo, D = verde. |
| `seq`    | entero | Contador propio del pulsador, +1 en cada pulsación. Arranca en 1. |

> **Pendiente sobre el QoS.** PubSubClient, la librería más usada para
> ESP8266, **sólo puede publicar en QoS 0** (soporta QoS 1 únicamente al
> suscribirse). Para cumplir este contrato tal como está escrito hay que usar
> `arduino-mqtt` (de 256dpi), que sí publica en QoS 1. La alternativa es
> aceptar QoS 0 y actualizar este documento. El grupo todavía no lo definió.

`seq` sirve para que la aplicación distinga un **reenvío** del mismo mensaje
(QoS 1 garantiza *al menos una vez*, así que los duplicados van a pasar) de una
**segunda pulsación real**. No hace falta que sobreviva a un reinicio.

### 2. Presencia — lo publica el pulsador

```
Tema:     aula/presencia/<id>
QoS:      0
Retained: sí
Payload:  {"online":true}
```

- Se publica una vez al conectarse, y después como latido **cada 5 segundos**.
- La aplicación marca el pulsador como caído si pasan **15 segundos** sin latido.
- El mensaje de última voluntad se declara al conectar, para que el broker
  avise si el nodo se cae de golpe. En PubSubClient 2.8 va como argumentos del
  `connect()`:

```cpp
cliente.connect(id, NULL, NULL, "aula/presencia/3a1f5c", 0, true,
                "{\"online\":false}");
```

Las versiones más nuevas de la librería exponen además un `setWill()` que se
llama antes del `connect()`. Conviene verificar cuál está instalada.

### 3. No hay más temas

La aplicación no publica nada dirigido al pulsador. Si en el futuro hiciera
falta (por ejemplo si vuelve el LED), sería una **versión 2** de este contrato.

---

## Comportamiento esperado del firmware

1. Conectarse a la red WiFi del aula. Reintentar indefinidamente si falla.
2. Registrar la última voluntad y conectarse al broker
   (IP fija de la Raspberry Pi, puerto 1883, sin usuario ni contraseña).
3. Publicar presencia al conectar y cada 5 segundos.
4. Leer los cuatro botones con **antirrebote de 50 ms**.
5. En cada pulsación válida: incrementar `seq` y publicar el voto.
6. Si se cae la conexión, reconectar solo. Los votos emitidos mientras no había
   conexión se pueden descartar o encolar; si se encolan, se publican al
   reconectar con su `seq` original.

---

## Qué hace la aplicación con cada voto

Un voto se **descarta** —sin error, sólo queda en el log— cuando:

| Motivo             | Cuándo pasa                                                  |
|--------------------|--------------------------------------------------------------|
| `fuera_de_ventana` | No hay ninguna pregunta abierta en ese momento.               |
| `opcion_invalida`  | Se votó una opción que esa pregunta no tiene (una D en una pregunta de dos opciones). |
| `ya_voto`          | Ese pulsador ya votó esta pregunta. **Gana la primera pulsación.** |
| `duplicado`        | Ya se procesó un mensaje con ese mismo `(id, seq)`.           |

Si el voto se acepta, queda registrado con la marca de tiempo de recepción,
que es la que define el orden de llegada para el puntaje.

---

## Límite a tener muy presente

`PubSubClient` trae el buffer en **256 bytes** y descarta en silencio todo
mensaje más grande — sin error y sin log. Los payloads de este contrato son de
unos 30 bytes, así que entran holgados; pero si alguna vez se agrega un campo,
conviene verificarlo con `cliente.setBufferSize()`.

---

## Cómo probarlo sin la aplicación

```bash
# ver todo lo que circula
mosquitto_sub -h <ip-de-la-pi> -t 'aula/#' -v

# simular un pulsador a mano
mosquitto_pub -h <ip-de-la-pi> -t aula/presencia/3a1f5c -r -m '{"online":true}'
mosquitto_pub -h <ip-de-la-pi> -t aula/voto/3a1f5c -q 1 -m '{"opcion":"B","seq":1}'
```
