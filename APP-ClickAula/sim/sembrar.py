#!/usr/bin/env python3
"""Carga dos encuestas de ejemplo para poder probar sin cargar nada a mano."""
import json
import sys
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"

EJEMPLOS = [
    {
        "nombre": "Repaso de redes",
        "modalidad": "competencia",
        "segundos": 20,
        "puntaje_base": 500,
        "preguntas": [
            {"enunciado": "¿Qué protocolo usa ClickAula para los votos?",
             "opciones": ["HTTP", "MQTT", "FTP", "SMTP"], "correcta": "B"},
            {"enunciado": "¿En qué banda trabaja el ESP8266?",
             "opciones": ["2.4 GHz", "5 GHz", "Las dos", "900 MHz"], "correcta": "A"},
            {"enunciado": "¿Qué significa QoS 1 en MQTT?",
             "opciones": ["Exactamente una vez", "Como mucho una vez",
                          "Al menos una vez", "Ninguna garantía"], "correcta": "C"},
            {"enunciado": "¿Qué hace hostapd en la Raspberry Pi?",
             "opciones": ["Guarda los votos", "Genera la red WiFi",
                          "Sirve la web", "Reparte direcciones IP"], "correcta": "B"},
            {"enunciado": "¿Cuál de estos NO necesita internet?",
             "opciones": ["Kahoot", "ClickAula", "Google Forms", "Mentimeter"],
             "correcta": "B"},
        ],
    },
    {
        "nombre": "Opinión sobre la actividad",
        "modalidad": "anonima",
        "segundos": 25,
        "puntaje_base": 500,
        "preguntas": [
            {"enunciado": "¿Cómo te resultó la actividad de hoy?",
             "opciones": ["Muy fácil", "Justa", "Difícil", "Muy difícil"], "correcta": None},
            {"enunciado": "¿Volverías a participar?",
             "opciones": ["Sí", "No"], "correcta": None},
            {"enunciado": "¿Qué te gustaría que agreguemos?",
             "opciones": ["Más preguntas", "Más tiempo", "Trabajo en equipo",
                          "Premios"], "correcta": None},
        ],
    },
]


def main():
    for e in EJEMPLOS:
        datos = json.dumps(e).encode("utf-8")
        req = urllib.request.Request(f"{BASE}/api/encuestas", data=datos,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                print(f"Creada: {e['nombre']}  (id {json.loads(r.read())['id']})")
        except Exception as ex:
            print(f"No se pudo crear «{e['nombre']}»: {ex}")


if __name__ == "__main__":
    main()
