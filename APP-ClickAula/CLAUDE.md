# CLAUDE.md — ClickAula

Contrato interno del equipo: **qué stack usamos, qué reglas no se rompen y
cómo está organizado el proyecto**. Vale tanto para una persona como para un
agente de IA que tome el trabajo.

Si vas a escribir el **firmware del pulsador**, leé las secciones 1, 6, 7 y 8.
Ahí está todo lo que necesitás y no te hace falta entender la aplicación.

*Última actualización: 10 de octubre de 2026.*

---

## 1. El proyecto en una pantalla

**ClickAula** es un sistema de votación en el aula tipo Kahoot que funciona
**sin internet**. Proyecto G1 de Taller de Proyecto II, Facultad de
Informática, UNLP. **Entrega final: diciembre de 2026.**

```
┌─────────────┐          ┌──────────────────┐          ┌─────────────────┐
│  Pulsador   │  WiFi    │  Raspberry Pi 3  │  WiFi    │  PC coordinador │
│  NodeMCU    │ ───────► │  hostapd+dnsmasq │ ───────► │  app Python     │
│  4 botones  │   MQTT   │  Mosquitto       │   MQTT   │  SQLite + web   │
└─────────────┘          └──────────────────┘          └─────────────────┘
   publica                  solo encamina                  decide todo
```

Tres ideas que explican el resto del diseño:

**El pulsador es un publicador puro.** No se suscribe a nada, no recibe nada,
no sabe si hay una votación abierta. Pulsa y publica, siempre.

**El servidor es la única autoridad.** Decide cuándo abre y cierra cada
pregunta, qué votos valen y cuánto suman. Ni el navegador ni el pulsador
deciden nada.

**Todo es local.** No hay nube, no hay internet, no hay servicios externos.

### Reparto del trabajo

| Parte | Estado | Responsable |
|---|---|---|
| Aplicación web y simulador | Funcionando y probada | Valentín |
| Contrato de mensajería | Cerrado, versión 1 | Valentin/Mateo |
| **Firmware del pulsador** | **Sin empezar** | Mateo |
| Raspberry Pi como punto de acceso | Investigado, sin implementar | Joaquin |
| Armado físico | Sin empezar, esperando materiales | Joaquin/Mateo/Valentin |

---

## 2. Stack

Esto está fijo. Cambiarlo requiere acuerdo del grupo.

| Capa | Herramienta | Versión |
|---|---|---|
| Lenguaje | Python | 3.12 |
| Web | Flask | 3.0.3 |
| Mensajería | paho-mqtt | 2.1.0 |
| Base de datos | SQLite (módulo `sqlite3` de la biblioteca estándar) | — |
| Intermediario | Eclipse Mosquitto | 2.x |
| Frontend | HTML, CSS y JavaScript sin bibliotecas | — |
| Firmware | C++ sobre Arduino, para ESP8266 | — |
| Entorno | Docker y Docker Compose | — |

**Dependencias de Python: dos.** Flask y paho-mqtt. Nada más. Si creés que
hace falta una tercera, plantealo en el grupo antes de instalarla.

### Decisiones de stack ya tomadas y por qué

**SQLite y no PostgreSQL.** Un solo proceso escribe, hay treinta clientes como
mucho y todo corre en una notebook sin internet. Postgres agregaría un
servidor que instalar y administrar en cada máquina, y chocaría con el
objetivo de que la aplicación sea un ejecutable que se abre y anda.

**Sin ORM.** Con repositorios de por medio (sección 4), `sqlite3` pelado
alcanza y no agrega dependencias. SQLAlchemy se evaluó y se descartó: para
siete tablas en un solo proceso es más ceremonia que beneficio.

**Sin bibliotecas en el frontend.** No es minimalismo por gusto: una
referencia a un CDN rompe la aplicación en un aula sin internet. Los gráficos
de barras son `div` con CSS. La actualización en vivo usa *Server-Sent
Events*, que es HTTP puro.

---

## 3. Las reglas que no se rompen

Cada una existe porque romperla ya costó caro o costaría caro.

### Dominio

**R1 · `dominio/` no importa nada de infraestructura.** Ni Flask, ni
`sqlite3`, ni paho, ni `requests`. Si el dominio necesita algo de afuera, se
define un puerto (una interfaz) y la infraestructura lo implementa. Hay un
test que verifica esto.

**R2 · El dominio no llama al reloj ni hace entrada/salida.** El instante
entra como parámetro: `comenzar(instante, presentes)`,
`registrar_voto(pulsador, opcion, seq, instante)`, `cerrar(instante,
presentes)`, `marcar_caidos(instante)`. Así una partida completa se prueba en
milisegundos en vez de esperar treinta segundos por pregunta, y cualquier error
se reproduce exactamente. Hay un test que verifica esto. El único que mira el
reloj de verdad es `servicios/sesion.py`, y lo recibe por constructor.

**R3 · Toda regla de juego nueva entra con su test.** El puntaje y la máquina
de estados son el corazón del sistema; si se rompen, se rompe todo.
`python3 -m pytest` antes de cada *commit*: tarda menos de un segundo, no hay
excusa.

### Persistencia

**R4 · Un solo proceso escribe la base.** El cliente MQTT y el servidor web
comparten memoria. Nada de varios *workers* de gunicorn: cada uno abriría su
propio cliente MQTT y procesaría cada voto varias veces.

**R5 · Un cambio de esquema es siempre una migración nueva.** Una migración ya
aplicada no se edita jamás, ni para arreglar una coma.

**R6 · El histórico guarda solo agregados.** Nunca el voto individual de un
pulsador. Es lo que hace que la modalidad anónima sea anónima de verdad.

### Red y producto

**R7 · Nada que dependa de internet.** Ni CDN, ni fuentes remotas, ni
servicios externos, ni NTP. Si algo necesita conexión, está mal.

**R8 · El contrato MQTT se versiona.** Cambiarlo obliga a actualizar
`contrato.md`, este archivo, y avisarle al resto. Es la única pieza que rompe
a las dos mitades del proyecto a la vez.

**R9 · El pulsador es publicador puro.** No se suscribe a nada. Si alguien
quiere devolverle un mensaje, eso es una versión 2 del contrato y se discute
primero.

**R10 · `CLICKAULA_DEV` jamás queda activo fuera de desarrollo.** Con esa
variable en 1, la respuesta correcta viaja al navegador y se puede espiar.

### Proceso

**R11 · Español** en código, comentarios, nombres de variables y
documentación. Los nombres del dominio también: `pulsador`, `voto`,
`encuesta`, `partida`.

**R12 · Los comentarios explican por qué, no qué.** El qué ya está en el
código.

---

## 4. Arquitectura

### Hacia dónde vamos

Núcleo de dominio puro rodeado de adaptadores. El patrón se llama puertos y
adaptadores, y se usa justamente cuando la parte valiosa y frágil —las reglas
y la máquina de estados— tiene que quedar aislada de todo lo que puede fallar:
la red, el *broker*, el disco, el navegador.

```
clickaula/
├── dominio/              ← no importa nada de infraestructura (R1)
│   ├── modelo.py         Encuesta, Pregunta, Voto, Pulsador
│   ├── puntaje.py        reparto de puntos
│   ├── partida.py        máquina de estados, sin reloj ni E/S (R2)
│   └── puertos.py        interfaces de persistencia
├── adaptadores/
│   ├── persistencia/     SQLite: implementa los puertos, más migraciones
│   ├── mensajeria/       cliente MQTT entrante
│   └── web/              Flask: fábrica, blueprints, SSE
├── servicios/            orquestación: reloj, supervisión, arranque
└── tests/
```

Del lado de Flask esto es lo que recomienda la documentación oficial para
aplicaciones que crecen: paquete en lugar de módulo, función `create_app()`
como fábrica y *blueprints* para agrupar vistas.

### Dónde estamos hoy

**El dominio ya está extraído (fases 0 y 1).** El código actual está así:

```
run.py                   arranque y filtro del registro
pytest.ini               configuración de los tests

dominio/                 núcleo puro: no importa infraestructura (R1)
├── modelo.py            Encuesta, Pregunta, Voto, Pulsador, constantes
├── puntaje.py           reparto de puntos
├── partida.py           máquina de estados, sin reloj ni E/S (R2)
├── pulsadores.py        registro de presencia, sin reloj (R2)
└── puertos.py           Protocol de los repositorios y del notificador

servicios/
└── sesion.py            orquesta: hilo reloj, candado, snapshot

app/                     adaptadores (irán a adaptadores/ en la fase 3)
├── composicion.py       único lugar que une puerto y adaptador
├── repositorios.py      SQLite → objetos de dominio
├── exportar.py          armado de los CSV de resultados
├── config.py            configuración por variables de entorno
├── db.py                SQLite: esquema y acceso    → adaptadores/persistencia
├── mqtt_client.py       suscriptor MQTT             → adaptadores/mensajeria
├── bus.py               eventos hacia los navegadores → adaptadores/web
├── server.py            vistas y API                → adaptadores/web
├── templates/           7 plantillas
└── static/              CSS y 5 archivos de JavaScript

tests/                   62 tests, corren en menos de un segundo
sim/simulador.py         pulsadores simulados
sim/sembrar.py           encuestas de ejemplo
```

`app/engine.py` y `app/scoring.py` ya no existen: su contenido quedó repartido
entre `dominio/` y `servicios/sesion.py`.

**Si estás tocando el firmware, nada de esto te afecta.** El contrato de la
sección 6 no cambia con la reestructuración.

La pieza que hace posible todo lo demás es que **el dominio no consulta el
reloj**: el instante entra como parámetro. Por eso una partida de cinco
preguntas de treinta segundos se prueba en milisegundos, y por eso hay 62
tests y no tres.

### Plan de migración

Cada fase deja la aplicación funcionando. Nunca hay un estado roto.

| Fase | Qué | Estado |
|---|---|---|
| 0 | Corregir el bug de deduplicación (sección 10) | **Hecha** |
| 1 | Extraer `dominio/`, sacar el reloj, escribir tests | **Hecha** |
| 2 | Puertos y repositorios | **Hecha** |
| — | Migraciones versionadas | **Descartada**, ver abajo |
| — | Exportación de resultados a CSV | **Hecha** |
| 5 | Integración con los pulsadores reales | Esperando materiales |
| 3 | Flask como paquete con fábrica y blueprints | Si queda tiempo |
| 6 | Empaquetado de escritorio | Si queda tiempo |
| — | Robustez: supervisión y recuperación tras caída | **Descartada**, ver abajo |

**Por qué se descartaron las migraciones.** Estaban pensadas como paso previo
a persistir la partida en curso, que agregaba tablas. Descartado eso, el
esquema de la sección 5 no tiene ningún cambio pendiente, y un sistema de
migraciones sin ninguna migración que aplicar es ceremonia. Si algún día hay
que tocar el esquema, **R5 sigue valiendo**: se arma el mecanismo en ese
momento y el cambio entra como migración, no como un `ALTER TABLE` a mano.

**Por qué se descartó la recuperación tras caída.** El escenario que cubre es
que la aplicación muera en medio de una ronda y haya que retomarla donde
estaba. Para una clase de cuarenta minutos con el coordinador presente,
rearrancar la ronda cuesta menos que mantener el estado de la partida
duplicado en disco. Lo que queda de esa idea y sí conviene tener es el
registro a archivo, que no depende de nada de esto.

---

## 5. Base de datos

Archivo único: **`data/clickaula.db`**. Seis tablas: `encuesta`, `pregunta`,
`pulsador`, `ejecucion`, `ejecucion_pregunta` y `ejecucion_podio`.

Dos cosas que conviene saber:

**La partida en curso vive en memoria, no en la base.** Qué pregunta está
abierta, quién votó qué, los puntajes acumulados: todo eso está en RAM hasta
que se guarda en el histórico. Si la aplicación se reinicia en medio de una
ronda, esa ronda se pierde y hay que volver a largarla. Es una decisión
tomada, no un pendiente: ver el plan de migración de la sección 4.

**La base usa modo WAL**, así que son tres archivos: `.db`, `.db-wal` y
`.db-shm`. Si copiás la base, copiá los tres.

### Exportación a CSV

Desde el historial se descargan dos archivos por ejecución:

```
GET /historial/<id>/preguntas.csv    una fila por pregunta
GET /historial/<id>/podio.csv        una fila por puesto (sólo competencia)
```

El armado está en `app/exportar.py`, en funciones puras que reciben el
diccionario de `db.obtener_ejecucion`. Tres decisiones que **no hay que
"arreglar"**, porque cada una tapa un problema concreto:

- **El separador es punto y coma y los decimales llevan coma.** Es como
  interpreta los CSV Excel en español. Con separador de coma, el archivo se
  abre todo apilado en la primera columna.
- **El archivo arranca con la marca de orden de bytes** (`﻿`). Sin ella,
  Excel en Windows lee el UTF-8 como Latin-1 y los enunciados salen con "Ã¡"
  en lugar de "á".
- **Las opciones que una pregunta no tiene quedan vacías, no en cero.** Un cero
  en "Votos C" se lee como "nadie eligió C"; vacío dice "no existía C".

Como el histórico guarda sólo agregados (R6), el CSV no puede contener el voto
individual de nadie ni el identificador de un pulsador. `test_exportar.py` lo
deja escrito.

---

## 6. El contrato de mensajería

**Versión 1.** La copia canónica está en `contrato.md`; esto es el resumen
operativo.

### ⚠ Antes de escribir una línea de firmware

Hay **una decisión abierta** que el grupo tiene que cerrar, porque cambia la
biblioteca que vas a usar:

El contrato especifica **QoS 1** para los votos. Pero **PubSubClient, la
biblioteca más usada para ESP8266, solo puede publicar en QoS 0** — lo soporta
para suscribirse, no para publicar, y no avisa: `publish()` ni siquiera acepta
un parámetro de QoS. Las dos salidas son:

- **Mantener QoS 1** y usar `arduino-mqtt` (de 256dpi, aparece como "MQTT" en
  el gestor de bibliotecas). Es lo recomendado: un voto perdido es la peor
  falla posible, porque el alumno apretó, no pasó nada y sin LED nadie se
  entera.
- **Aceptar QoS 0** con PubSubClient, actualizar este contrato y avisar. Más
  simple, y de paso hace desaparecer el bug de deduplicación de la sección 10.

### Identidad del pulsador

Identificador corto, estable entre reinicios, derivado de la MAC:

```cpp
char id[7];
snprintf(id, sizeof(id), "%06x", ESP.getChipId());   // ej. "3a1f5c"
```

La aplicación le asigna sola un número (Pulsador 01, 02…) la primera vez que
lo escucha. Vos no te ocupás de eso.

### Tema 1 — Voto

```
Tema:     aula/voto/<id>
QoS:      1  (ver la decisión abierta de más arriba)
Retained: no
Payload:  {"opcion":"A","seq":41}
```

- `opcion` — `"A"`, `"B"`, `"C"` o `"D"`.
- `seq` — contador propio, arranca en 1, +1 en cada pulsación.

El voto **no lleva el número de pregunta** — el pulsador no lo sabe y no lo
necesita, se lo asigna el servidor. Tampoco lleva marca de tiempo: el ESP8266
no tiene reloj y el orden de llegada lo determina la aplicación al recibir.

### Tema 2 — Presencia

```
Tema:     aula/presencia/<id>
QoS:      0
Retained: sí
Payload:  {"online":true}
```

Se publica al conectar y como latido **cada 5 segundos**. La aplicación da por
caído al pulsador a los **15 segundos** sin latido.

El mensaje de última voluntad se declara **al conectar**. En PubSubClient 2.8
va como argumentos del `connect()`:

```cpp
cliente.connect(id, NULL, NULL, topicPresencia, 0, true, "{\"online\":false}");
```

Las versiones más nuevas exponen además un `setWill()` previo al `connect()`.
Verificá cuál tenés antes de copiar código de internet.

### No hay más temas

La aplicación no publica nada dirigido al pulsador (R9).

---

## 7. Hardware del pulsador

### Mapa de pines

| Opción | Color | Pin | GPIO |
|---|---|---|---|
| A | Rojo | D1 | GPIO5 |
| B | Azul | D2 | GPIO4 |
| C | Amarillo | D6 | GPIO12 |
| D | Verde | D7 | GPIO13 |

Cada botón: una pata al pin, la otra a masa. Las cuatro masas van a un riel
común. Ver `Conexionado_Pulsador.png`.

**Los pines no son intercambiables.** Evitá D0, D3, D4 y D8: el ESP8266
consulta su estado al arrancar para elegir el modo de operación. Un botón
conectado a uno de ellos y presionado durante el encendido hace que la placa
arranque en modo programación en lugar de ejecutar tu código, sin ninguna
señal de que eso pasó. D9 y D10 son la consola serie.

### Lógica de los botones

```cpp
pinMode(PIN_A, INPUT_PULLUP);
```

Con resistencia de elevación interna la lógica queda **invertida**: `HIGH` en
reposo, `LOW` al presionar. Es el error más común de la primera vez.

No hay resistencias externas ni capacitores. El circuito es el NodeMCU, cuatro
botones y ocho cables.

### Alimentación

Batería portátil de 5 V → cable micro-USB → NodeMCU. Nada más. No hay
regulador externo: al eliminarse el LED el pulsador quedó sin cargas externas,
y el único consumidor es el propio módulo, alimentado como previó el
fabricante de la placa.

Consumo: 5 V, unos 80 mA medios y 200 mA de pico al transmitir.

### Red

WiFi 2,4 GHz (el ESP8266 no soporta 5 GHz), generada por la Raspberry Pi.
Broker en la IP de la Pi, puerto 1883, sin usuario ni contraseña. Sin salida a
internet: no sirve NTP ni actualización por la nube.

---

## 8. Qué tiene que hacer el firmware

1. Conectar al WiFi del aula. Reintentar indefinidamente si falla.
2. Declarar la última voluntad y conectar al broker.
3. Publicar presencia al conectar y cada 5 segundos.
4. Leer los cuatro botones con **antirrebote de 50 ms**.
5. En cada pulsación: incrementar `seq` y publicar el voto.
6. Reconectar solo si se cae la conexión, sin bloquear la lectura de botones.

Esqueleto de referencia con PubSubClient. **Es un punto de partida, no la
versión final**: falta manejar la reconexión de WiFi sin bloquear y decidir
qué hacer con los votos emitidos mientras no hay conexión.

```cpp
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char*   SSID      = "ClickAula";
const char*   PASS      = "...";
const char*   BROKER    = "192.168.4.1";       // IP fija de la Raspberry Pi
const uint8_t PINES[4]  = {5, 4, 12, 13};      // D1 D2 D6 D7
const char*   OPCION[4] = {"A", "B", "C", "D"};

char id[7], topicVoto[32], topicPresencia[32];
uint32_t seq = 0, ultimoLatido = 0, ultimoCambio[4] = {0};
bool estadoPrevio[4] = {HIGH, HIGH, HIGH, HIGH};

WiFiClient red;
PubSubClient mqtt(red);

void setup() {
  snprintf(id, sizeof(id), "%06x", ESP.getChipId());
  snprintf(topicVoto, sizeof(topicVoto), "aula/voto/%s", id);
  snprintf(topicPresencia, sizeof(topicPresencia), "aula/presencia/%s", id);

  for (int i = 0; i < 4; i++) pinMode(PINES[i], INPUT_PULLUP);

  WiFi.mode(WIFI_STA);
  WiFi.begin(SSID, PASS);
  mqtt.setServer(BROKER, 1883);
  // Sin setCallback: este nodo no se suscribe a nada (R9).
}

void conectar() {
  while (!mqtt.connected()) {
    if (mqtt.connect(id, NULL, NULL, topicPresencia, 0, true,
                     "{\"online\":false}")) {
      mqtt.publish(topicPresencia, "{\"online\":true}", true);
    } else {
      delay(1000);
    }
  }
}

void loop() {
  if (!mqtt.connected()) conectar();
  mqtt.loop();

  uint32_t ahora = millis();

  if (ahora - ultimoLatido > 5000) {
    ultimoLatido = ahora;
    mqtt.publish(topicPresencia, "{\"online\":true}", true);
  }

  for (int i = 0; i < 4; i++) {
    bool nivel = digitalRead(PINES[i]);            // LOW = apretado
    if (nivel != estadoPrevio[i] && ahora - ultimoCambio[i] > 50) {
      ultimoCambio[i] = ahora;
      estadoPrevio[i] = nivel;
      if (nivel == LOW) {                          // flanco de pulsación
        char payload[40];
        snprintf(payload, sizeof(payload),
                 "{\"opcion\":\"%s\",\"seq\":%lu}", OPCION[i], ++seq);
        mqtt.publish(topicVoto, payload, false);   // ojo: QoS 0 en esta librería
      }
    }
  }
}
```

### Trampas conocidas

**PubSubClient trae el buffer en 256 bytes.** Un mensaje más grande se
descarta **en silencio**. Los de este contrato tienen unos 30 bytes y entran
holgados, pero si agregás un campo, verificalo con `setBufferSize()`.

**`millis()` desborda a los 49 días.** La resta `ahora - ultimo` funciona
igual si las dos son `uint32_t`. No compares con `<` directo.

**No uses `delay()` en el `loop`.** Bloquea la lectura de botones y la
atención del cliente MQTT.

**El identificador de cliente MQTT tiene que ser único.** Con dos pulsadores
usando el mismo, el broker patea a uno cada vez que el otro se conecta, y vas
a ver nodos entrando y saliendo sin explicación. El `id` derivado del chip lo
resuelve solo.

---

## 9. Cómo probar

### Ver el tráfico — lo primero que hay que tener abierto

```bash
mosquitto_sub -h <ip-del-broker> -t 'aula/#' -v
```

Te dice al instante si el problema está en el pulsador o en la aplicación.

### Simular un pulsador a mano, sin firmware

```bash
mosquitto_pub -h <ip> -t aula/presencia/3a1f5c -r -m '{"online":true}'
mosquitto_pub -h <ip> -t aula/voto/3a1f5c -q 1 -m '{"opcion":"B","seq":1}'
```

### Levantar el sistema completo

```bash
docker compose --profile simulacion up -d --build
docker compose exec app python sim/sembrar.py     # encuestas de ejemplo
```

Panel en **http://localhost:5000**, proyección en **/proyeccion**.

Para que un pulsador real llegue al broker del contenedor hay que publicar el
puerto 1883 (ya está en el compose) y abrir el firewall de Windows.

### Por qué se descartó un voto

```bash
docker compose logs -f app
```

Los motivos son `fuera_de_ventana` (no hay pregunta abierta), `opcion_invalida`
(esa pregunta no tiene esa opción), `ya_voto` (gana la primera pulsación) y
`duplicado` (mismo `id` y mismo `seq`).

### Pruebas automatizadas

Tres niveles, del más rápido al más lento. Empezá siempre por el primero.

```bash
pip install -r requirements-dev.txt    # una sola vez: agrega pytest
python3 -m pytest       # 62 tests del dominio y del servicio, menos de 1 s
bash prueba_e2e.sh      # partida completa en las dos modalidades, con broker
bash prueba_bordes.sh   # cierre por tiempo, doble voto, duplicados, caídas
```

Los tests no necesitan broker, base ni Flask: el dominio es puro y el servicio
recibe dobles de cuatro líneas (`tests/conftest.py`). Si uno falla, falla por
una regla de juego, no por el entorno.

Qué cubre cada archivo:

| Archivo | Qué custodia |
|---|---|
| `test_puntaje.py` | escalones 100/90/80/60, orden por instante de llegada |
| `test_partida.py` | máquina de estados, los cuatro motivos de descarte, resumen |
| `test_pulsadores.py` | presencia, vencimientos, mensajes retenidos |
| `test_sesion.py` | **la forma del snapshot**, reloj, archivado |
| `test_exportar.py` | formato de los CSV y R6: nunca el voto individual |
| `test_arquitectura.py` | R1 y R2: que nadie meta infraestructura en el dominio |

`test_arquitectura.py` es el que más vale a largo plazo: lee los `import` de
`dominio/` con el analizador sintáctico de Python y falla si aparece algo que
no sea biblioteca estándar de estructuras de datos. Es la regla R1 convertida
en test, para que no dependa de que alguien se acuerde.

`CLAVES_SNAPSHOT` en `test_sesion.py` es el contrato con el frontend. Si
agregás una clave al snapshot, agregala ahí y tocá el `.js` que la consume.

---

## 10. Pendientes conocidos

**Bug de deduplicación — cerrado en la fase 0.** La aplicación recordaba los
pares `(pulsador, seq)` procesados para descartar reenvíos, pero `seq` vuelve a
empezar en 1 cuando el nodo se reinicia y la aplicación lo tomaba por reenvío:
descartaba en silencio todos los votos de ese pulsador por el resto de la
sesión. Ahora la lista se vacía al abrir cada pregunta
(`dominio/partida.py`, `_abrir`), y además vive en la partida y no en el
servicio, así que empezar otra encuesta también la deja limpia. Queda
custodiado por dos tests de regresión que no se tocan:
`test_un_pulsador_que_reinicia_vuelve_a_votar` y
`test_un_pulsador_que_reinicia_sigue_votando_en_la_partida_siguiente`.
El `docker compose restart app` ya no hace falta.

De la aplicación no queda ninguno abierto. Lo que falta del proyecto es el
firmware, la Raspberry Pi como punto de acceso y el armado físico.

### Riesgos evaluados y aceptados

No son olvidos. Se discutieron, se midió el costo de cerrarlos y se decidió
dejarlos así. Si alguien pregunta en la defensa, la respuesta está acá.

**La aplicación escucha en toda la red del aula.** `WEB_HOST` es `0.0.0.0`, así
que cualquier dispositivo conectado a la WiFi de la Raspberry Pi llega a
`http://<ip-del-pc>:5000/partida` y puede cerrar preguntas o abortar la
partida. *Por qué se acepta:* el acceso ya está controlado por la clave de la
red, que no es pública; hace falta además conocer la dirección del PC y la
ruta. Atarlo a `127.0.0.1` cerraría eso, pero impediría abrir el panel o la
proyección desde otra máquina, que es algo que sí se puede necesitar el día de
la demostración. *Si alguna vez hace falta cerrarlo:* publicar el puerto como
`127.0.0.1:5000:5000` en `docker-compose.yml`, no tocar `WEB_HOST` — dentro de
un contenedor eso rompe el mapeo de puertos.

**El intermediario MQTT no pide credenciales.** Con `allow_anonymous true`,
cualquiera en esa WiFi puede publicar en `aula/voto/<id>` y votar como un
pulsador ajeno, o inventar pulsadores que no existen. *Por qué se acepta:* la
misma clave de red es la que lo protege, y agregar usuario y contraseña obliga
a tocar el firmware de todos los pulsadores. *Importante:* si el grupo decide
cerrarlo, **hay que decidirlo antes de que se escriba la reconexión del
firmware**, no después: son dos argumentos más en el `connect()` y es mucho más
barato ponerlos desde el principio.

**La partida en curso no sobrevive a un reinicio de la aplicación** (sección 5).

**Raspberry Pi como punto de acceso.** Investigado, sin implementar. Hay
reportes de bloqueo del controlador inalámbrico cerca de los 20 dispositivos
asociados; Raspberry Pi OS Bookworm pasó a NetworkManager y ya no lee
`dhcpcd.conf`; conviene usar concesiones de dirección cortas; y falta medir
los canales 1, 6 y 11 antes de fijar el de la red.

---

## 11. Qué requiere discusión del grupo

No lo decidas solo:

- Volver a poner el LED de confirmación. Tira abajo R9 y obliga a una versión
  2 del contrato.
- Cualquier cambio al contrato de mensajería.
- Poner usuario y contraseña en el intermediario MQTT. Toca el firmware de
  todos los pulsadores, así que conviene cerrarlo antes de que esté escrito.
- Agregar una dependencia.
- Cambiar el modelo de puntaje o las reglas de votación.
- Cambiar de motor de base de datos.

---

## 12. Documentos del proyecto

| Archivo | Qué es |
|---|---|
| `CLAUDE.md` | Este archivo. Stack, reglas y arquitectura. |
| `contrato.md` | Contrato de mensajería. Copia canónica. |
| `README.md` | Cómo levantar la aplicación. |
| `pytest.ini` | Configuración de los tests. |
| `Conexionado_Pulsador.png` | Diagrama de cableado del pulsador. |
| `AGENTS.md` | Remite a este archivo. |
