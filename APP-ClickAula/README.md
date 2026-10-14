# ClickAula — aplicación de votación

Aplicación web del sistema de votación en el aula sin conexión (Taller de
Proyecto II, proyecto G1). Corre en la computadora del coordinador; la
Raspberry Pi es punto de acceso WiFi y broker MQTT.

Funciona **completamente offline**: no hay una sola referencia a internet en
todo el proyecto, ni CDN, ni fuentes remotas, ni librerías de gráficos.

---

## Levantar todo en simulación, sin hardware

Necesitás sólo Docker Desktop.

```bash
docker compose --profile simulacion up -d --build
```

El `-d` es importante: deja los contenedores corriendo en segundo plano y te
devuelve la terminal. Sin él, `docker compose` se queda mostrando los logs y no
podés escribir el comando siguiente (para salir de ahí, Ctrl+C, que además
frena todo).

Eso levanta tres contenedores: el broker Mosquitto, la aplicación y ocho
pulsadores simulados. Después, una sola vez, cargá las encuestas de ejemplo:

```bash
docker compose exec app python sim/sembrar.py
```

Y ya está:

1. Abrí **http://localhost:5000**
2. En «Encuestas» apretá **Ejecutar** en *Repaso de redes*.
3. Abrí la **proyección** en otra ventana con el botón «Abrir proyección ↗»
   del encabezado (o http://localhost:5000/proyeccion).
4. Vas a ver los ocho pulsadores simulados en la sala de espera. Apretá
   **Comenzar** y votan solos.
5. Cuando termina, en **Historial** quedan los resultados, y de ahí se bajan
   en CSV listos para abrir con Excel.

Comandos útiles mientras corre:

```bash
docker compose logs -f app          # ver los logs de la aplicación
docker compose logs -f simulador    # ver qué están votando los simulados
docker compose ps                   # qué está levantado
docker compose down                 # bajar todo
```

### Sólo la aplicación, sin simulador

```bash
docker compose up --build
```

### Cambiar la simulación

```bash
# 30 pulsadores: prueba de carga de un aula completa
docker compose run --rm simulador python sim/simulador.py \
    --n 30 --broker broker --app http://app:5000 --acierto 0.55

# votos disparados en cualquier momento, para ver el descarte fuera de ventana
docker compose run --rm simulador python sim/simulador.py \
    --n 6 --broker broker --app http://app:5000 --caos
```

Opciones del simulador: `--n`, `--acierto`, `--min-demora`, `--max-demora`,
`--participacion`, `--caos`.

---

## Sin Docker

```bash
pip install -r requirements.txt
mosquitto -c mosquitto/mosquitto.conf &      # o el broker de la Raspberry Pi
CLICKAULA_DEV=1 python run.py
python sim/sembrar.py
python sim/simulador.py --n 8
```

---

## Pruebas

```bash
pip install -r requirements-dev.txt    # una sola vez: agrega pytest
python3 -m pytest       # dominio y servicio, sin broker ni base, menos de 1 s
bash prueba_e2e.sh      # partida completa en las dos modalidades
bash prueba_bordes.sh   # cierre por tiempo, doble voto, duplicados, caída de nodo
```

---

## Cómo está armado

Tres capas. De adentro hacia afuera: las reglas, la orquestación, y el mundo.

```
dominio/               las reglas. No importa Flask, ni SQLite, ni MQTT.
├── modelo.py          Encuesta, Pregunta, Voto, Pulsador, constantes
├── puntaje.py         puntaje competitivo (100/90/80/60 % según orden)
├── partida.py         máquina de estados: ventana de votación y descartes
├── pulsadores.py      quién está en línea y quién se cayó
└── puertos.py         qué le pide el dominio al mundo

servicios/sesion.py    junta las tres cosas que el dominio no tiene:
                       el reloj, el candado y los repositorios

app/composicion.py     el único lugar que elige implementaciones concretas
app/repositorios.py    traduce entre SQLite y los objetos del dominio
app/config.py          configuración por variables de entorno
app/db.py              SQLite: encuestas, preguntas, pulsadores e histórico
app/mqtt_client.py     suscriptor MQTT (única entrada de datos)
app/bus.py             bus de eventos hacia los navegadores (SSE)
app/server.py          vistas y API

run.py                 arranque: base, reloj, cliente MQTT y servidor web
tests/                 62 tests; los dobles están en tests/conftest.py
sim/simulador.py       pulsadores simulados
sim/sembrar.py         encuestas de ejemplo
contrato.md            contrato de mensajería para el firmware
```

**El dominio no mira el reloj.** El instante entra siempre como parámetro. Es
lo que permite probar una partida de cinco preguntas de treinta segundos en
milisegundos, y reproducir un error exactamente en vez de esperar a que vuelva
a pasar.

### Decisiones que conviene conocer antes de tocar el código

**El servidor es la única autoridad.** El navegador no decide nada: no cierra
preguntas, no calcula puntajes, no valida votos. Un hilo reloj cierra las
preguntas al vencer el tiempo, así que el cierre ocurre aunque no haya ninguna
pestaña abierta. La cuenta regresiva que se ve en pantalla es sólo una
interpolación de los milisegundos que manda el servidor.

**Un solo proceso.** El cliente MQTT y el servidor web comparten memoria: el
estado de la partida vive en `composicion.sesion`. Por eso **no** hay que levantar
esto con varios workers de gunicorn — cada worker abriría su propio cliente
MQTT y procesaría cada voto varias veces.

**Estado completo en cada evento.** El servidor empuja el snapshot entero por
SSE en lugar de eventos incrementales. Con treinta pulsadores el mensaje es
chico y evita toda una familia de errores de desincronización. Si se cierra la
ventana de proyección, se recarga y retoma sola.

**La respuesta correcta no viaja mientras la pregunta está abierta.** El
snapshot manda `correcta: null` hasta que la pregunta cierra, así no se puede
espiar desde el navegador. La excepción es `CLICKAULA_DEV=1`, que habilita
`/api/estado?espia=1` para que el simulador pueda acertar a propósito.
**Sacar esa variable antes de usarlo en el aula.**

**El histórico guarda sólo agregados.** Nunca votos individuales: por cada
ejecución quedan la fecha, el nombre, la modalidad, los participantes, el
conteo por opción de cada pregunta y —en competencia— el podio.

**Los pulsadores viejos no cuentan como presentes.** Los mensajes de presencia
son retenidos, así que al arrancar el broker entrega los de sesiones
anteriores. La aplicación los registra pero los da por caídos hasta que llegue
un latido de verdad.

### Reglas de juego implementadas

- Gana la **primera pulsación**: el voto no se puede cambiar.
- Puntaje competitivo sobre la base configurada (500 por defecto), según el
  orden de llegada **entre las respuestas correctas**: 100 %, 90 %, 80 %, y
  60 % de la cuarta en adelante. Las incorrectas no suman.
- En encuesta anónima no hay respuestas correctas, ni puntaje, ni podio, y al
  cerrar una pregunta se pasa directo a la siguiente.
- Las preguntas admiten de 2 a 4 opciones. Un voto a una opción inexistente se
  descarta.
- El denominador de los porcentajes son los pulsadores en línea **al abrir**
  la pregunta, así el número no cambia si alguien se cae en el medio.

---

## Variables de entorno

| Variable             | Por defecto | Para qué                                        |
|----------------------|-------------|-------------------------------------------------|
| `MQTT_HOST`          | `localhost` | Broker. En el aula, la IP de la Raspberry Pi.   |
| `MQTT_PORT`          | `1883`      |                                                 |
| `WEB_PORT`           | `5000`      |                                                 |
| `DB_PATH`            | `data/clickaula.db` |                                         |
| `PUNTAJE_BASE`       | `500`       | Valor inicial al crear una encuesta.            |
| `SEGUNDOS_PREGUNTA`  | `30`        | Ídem.                                           |
| `PRESENCIA_TIMEOUT_S`| `15`        | Sin latido en esa ventana, el pulsador se da por caído. |
| `CLICKAULA_DEV`      | `0`         | `1` habilita `?espia=1`. **Sólo para desarrollo.** |

---

## Pasarlo al aula

1. Sacar `CLICKAULA_DEV` del `docker-compose.yml`.
2. Apuntar `MQTT_HOST` al broker de la Raspberry Pi (o levantar el broker allá
   y dejar sólo el servicio `app` acá).
3. Publicar el puerto 1883 y abrir el firewall de Windows para que los
   pulsadores reales lleguen al broker.
4. Abrir `/proyeccion` en la pantalla del proyector y `/` en la del coordinador.
