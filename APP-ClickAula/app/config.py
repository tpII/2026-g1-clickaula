"""Configuración leída del entorno, con valores por defecto para desarrollo."""
import os

# Las constantes de juego se reexportan desde el dominio para que haya una
# sola verdad: si mañana hay cinco opciones, se cambia en `dominio/modelo.py`.
from dominio.modelo import (COLOR_OPCION, MODALIDAD_ANONIMA,  # noqa: F401
                            MODALIDAD_COMPETENCIA, OPCIONES)

# --- MQTT -------------------------------------------------------------------
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "clickaula-app")

TOPIC_VOTO = "aula/voto/+"
TOPIC_PRESENCIA = "aula/presencia/+"

# --- Web --------------------------------------------------------------------
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "5000"))

# --- Base de datos ----------------------------------------------------------
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "data", "clickaula.db"))

# --- Reglas de juego --------------------------------------------------------
PUNTAJE_BASE_DEFECTO = int(os.getenv("PUNTAJE_BASE", "500"))
SEGUNDOS_DEFECTO = int(os.getenv("SEGUNDOS_PREGUNTA", "30"))

# Un pulsador se considera caído si no manda latido en esta ventana.
PRESENCIA_TIMEOUT_S = float(os.getenv("PRESENCIA_TIMEOUT_S", "15"))

# Resolución del reloj que cierra las preguntas.
TICK_S = 0.2

# --- Desarrollo -------------------------------------------------------------
# Con DEV=1 el endpoint /api/estado acepta ?espia=1 y revela la respuesta
# correcta de la pregunta abierta. Lo usa el simulador para poder "acertar".
# NUNCA activarlo en el aula.
DEV = os.getenv("CLICKAULA_DEV", "0") == "1"
