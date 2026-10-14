#!/usr/bin/env python3
"""Simulador de pulsadores: reemplaza al hardware para desarrollar y probar.

Levanta N clientes MQTT que se comportan como pulsadores reales — publican
presencia con latido y mensaje de última voluntad, y publican votos en
`aula/voto/<id>` — pero además consultan la API de la aplicación para saber
cuándo hay una pregunta abierta. Un pulsador de verdad no puede hacer eso
(es un publicador puro); el simulador se lo permite porque es una herramienta
de prueba que corre en la misma PC.

Ejemplos:
    python sim/simulador.py --n 8
    python sim/simulador.py --n 30 --acierto 0.55        # prueba de carga
    python sim/simulador.py --n 6 --caos                 # votos fuera de ventana
"""
import argparse
import json
import random
import threading
import time
import urllib.request

import paho.mqtt.client as mqtt

LETRAS = ["A", "B", "C", "D"]


class Pulsador:
    def __init__(self, idx, args):
        self.id = f"sim{idx:02d}"
        self.args = args
        self.seq = 0
        self.respondida = None          # orden de la última pregunta ya votada
        self.cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"puls-{self.id}")
        # Última voluntad: si el nodo se cae, el broker avisa por nosotros.
        self.cli.will_set(f"aula/presencia/{self.id}",
                          json.dumps({"online": False}), qos=0, retain=True)

    def conectar(self):
        self.cli.connect(self.args.broker, self.args.puerto, keepalive=30)
        self.cli.loop_start()
        self.anunciar()

    def anunciar(self):
        self.cli.publish(f"aula/presencia/{self.id}",
                         json.dumps({"online": True}), qos=0, retain=True)

    def votar(self, opcion):
        self.seq += 1
        self.cli.publish(f"aula/voto/{self.id}",
                         json.dumps({"opcion": opcion, "seq": self.seq}), qos=1)

    def desconectar(self):
        self.cli.publish(f"aula/presencia/{self.id}",
                         json.dumps({"online": False}), qos=0, retain=True)
        time.sleep(0.1)
        self.cli.loop_stop()
        self.cli.disconnect()


def leer_estado(base):
    try:
        with urllib.request.urlopen(f"{base}/api/estado?espia=1", timeout=3) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def elegir(preg, acierto):
    """Elige una opción: acierta con probabilidad `acierto` si hay correcta."""
    n = len(preg["opciones"])
    letras = LETRAS[:n]
    correcta = preg.get("correcta")
    if correcta and random.random() < acierto:
        return correcta
    if correcta:
        malas = [l for l in letras if l != correcta]
        return random.choice(malas) if malas else correcta
    return random.choice(letras)


def main():
    ap = argparse.ArgumentParser(description="Simulador de pulsadores de ClickAula")
    ap.add_argument("--n", type=int, default=8, help="cantidad de pulsadores (por defecto 8)")
    ap.add_argument("--broker", default="localhost")
    ap.add_argument("--puerto", type=int, default=1883)
    ap.add_argument("--app", default="http://localhost:5000",
                    help="URL de la aplicación, para saber cuándo abre una pregunta")
    ap.add_argument("--acierto", type=float, default=0.6,
                    help="probabilidad de responder bien (0 a 1)")
    ap.add_argument("--min-demora", type=float, default=0.4,
                    help="demora mínima en segundos antes de votar")
    ap.add_argument("--max-demora", type=float, default=9.0,
                    help="demora máxima en segundos antes de votar")
    ap.add_argument("--participacion", type=float, default=0.95,
                    help="probabilidad de que un pulsador vote una pregunta dada")
    ap.add_argument("--caos", action="store_true",
                    help="además, disparar votos fuera de la ventana para probar el descarte")
    args = ap.parse_args()

    print(f"Conectando {args.n} pulsadores simulados a {args.broker}:{args.puerto}…")
    pulsadores = []
    for i in range(1, args.n + 1):
        p = Pulsador(i, args)
        p.conectar()
        pulsadores.append(p)
        time.sleep(0.03)
    print(f"Listos: {', '.join(p.id for p in pulsadores)}")
    print(f"Mirando {args.app} para detectar preguntas abiertas.  Ctrl+C para salir.\n")

    # Latido de presencia
    parar = threading.Event()

    def latir():
        while not parar.wait(5):
            for p in pulsadores:
                p.anunciar()
    threading.Thread(target=latir, daemon=True).start()

    def caos():
        while not parar.wait(random.uniform(3, 8)):
            p = random.choice(pulsadores)
            p.votar(random.choice(LETRAS))
    if args.caos:
        threading.Thread(target=caos, daemon=True).start()
        print("Modo caos activo: se enviarán votos en cualquier momento.\n")

    orden_visto = None
    try:
        while True:
            s = leer_estado(args.app)
            if not s:
                time.sleep(1)
                continue

            if s["estado"] != "PREGUNTA_ABIERTA":
                orden_visto = None
                time.sleep(0.4)
                continue

            preg = s["pregunta"]
            if preg["orden"] == orden_visto:
                time.sleep(0.3)
                continue
            orden_visto = preg["orden"]

            if preg.get("correcta") is None and s.get("competitivo"):
                print("  (sin ?espia=1: los simulados van a responder al azar — "
                      "levantá la app con CLICKAULA_DEV=1 para que puedan acertar)")

            restante = (s.get("restante_ms") or 0) / 1000
            tope = max(0.5, min(args.max_demora, restante - 0.5))
            print(f"Pregunta {preg['orden']}/{preg['total']}: {preg['enunciado'][:60]}")

            for p in pulsadores:
                if random.random() > args.participacion:
                    continue
                demora = random.uniform(args.min_demora, tope)
                opcion = elegir(preg, args.acierto)
                threading.Timer(demora, p.votar, args=(opcion,)).start()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nCerrando pulsadores…")
    finally:
        parar.set()
        for p in pulsadores:
            try:
                p.desconectar()
            except Exception:
                pass


if __name__ == "__main__":
    main()
