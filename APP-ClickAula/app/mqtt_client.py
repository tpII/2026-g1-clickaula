"""Cliente MQTT: única entrada de datos desde los pulsadores.

El pulsador es un publicador puro. La aplicación no le manda absolutamente
nada, así que acá sólo nos suscribimos. Ver contrato.md.
"""
import json
import threading

import paho.mqtt.client as mqtt

from . import config
from .composicion import sesion

_estado = {"conectado": False, "ultimo_error": None}


def conectado():
    return dict(_estado)


def _pulsador_de(topic):
    return topic.rsplit("/", 1)[-1]


def _on_connect(client, userdata, flags, reason_code, properties=None):
    # En paho 2.x reason_code es un objeto ReasonCode, no un entero.
    ok = not getattr(reason_code, "is_failure", reason_code != 0)
    _estado["conectado"] = ok
    if ok:
        _estado["ultimo_error"] = None
        client.subscribe([(config.TOPIC_VOTO, 1), (config.TOPIC_PRESENCIA, 0)])
        print("[mqtt] conectado y suscripto", flush=True)
    else:
        _estado["ultimo_error"] = f"conexión rechazada ({reason_code})"


def _on_disconnect(client, userdata, flags, reason_code, properties=None):
    _estado["conectado"] = False
    print("[mqtt] desconectado, reintentando…", flush=True)


def _on_message(client, userdata, msg):
    pid = _pulsador_de(msg.topic)
    try:
        payload = json.loads(msg.payload.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        print(f"[mqtt] payload ilegible en {msg.topic}", flush=True)
        return

    if msg.topic.startswith("aula/voto/"):
        opcion = str(payload.get("opcion", "")).upper()
        motivo = sesion.votar(pid, opcion, payload.get("seq"))
        if motivo:
            print(f"[voto] {pid} {opcion} descartado: {motivo}", flush=True)

    elif msg.topic.startswith("aula/presencia/"):
        # Un payload vacío es el mensaje de última voluntad al caerse el nodo.
        online = bool(payload.get("online", False))
        # msg.retain=True significa que el broker nos entregó un mensaje
        # guardado de antes: registra al pulsador pero sin darlo por vivo.
        sesion.visto(pid, online=online, retenido=bool(msg.retain))


def arrancar():
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=config.MQTT_CLIENT_ID)
    c.on_connect = _on_connect
    c.on_disconnect = _on_disconnect
    c.on_message = _on_message
    c.reconnect_delay_set(min_delay=1, max_delay=10)

    def _run():
        while True:
            try:
                c.connect(config.MQTT_HOST, config.MQTT_PORT, keepalive=30)
                c.loop_forever(retry_first_connection=True)
            except Exception as e:
                _estado["conectado"] = False
                _estado["ultimo_error"] = str(e)
                print(f"[mqtt] {e}; reintento en 3 s", flush=True)
                import time
                time.sleep(3)

    threading.Thread(target=_run, daemon=True, name="mqtt").start()
    return c
