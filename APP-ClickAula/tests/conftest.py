"""Dobles de prueba y constructores de encuestas.

Todo lo que el servicio necesita del mundo exterior entra por puertos, así que
los dobles son de cuatro líneas y no hace falta ni base ni intermediario MQTT
para probar una partida entera.
"""
import pytest

from dominio.modelo import (MODALIDAD_ANONIMA, MODALIDAD_COMPETENCIA, Encuesta,
                            Pregunta)
from servicios.sesion import ServicioSesion


class RelojFalso:
    """Reloj que sólo avanza cuando el test lo dice."""

    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t

    def avanzar(self, segundos):
        self.t += segundos
        return self.t


class RepoEncuestasFalso:
    def __init__(self, *encuestas):
        self.por_id = {e.id: e for e in encuestas}

    def obtener(self, encuesta_id):
        return self.por_id.get(encuesta_id)


class RepoPulsadoresFalso:
    """Asigna números en el orden en que aparecen, como la base real."""

    def __init__(self):
        self.numeros = {}

    def numero_de(self, pulsador_id):
        if pulsador_id not in self.numeros:
            self.numeros[pulsador_id] = len(self.numeros) + 1
        return self.numeros[pulsador_id]


class HistorialFalso:
    def __init__(self):
        self.guardados = []

    def guardar(self, resumen):
        self.guardados.append(resumen)
        return len(self.guardados)


class NotificadorFalso:
    def __init__(self):
        self.snapshots = []

    def publicar(self, snapshot):
        self.snapshots.append(snapshot)

    @property
    def ultimo(self):
        return self.snapshots[-1] if self.snapshots else None


# ------------------------------------------------------------- constructores
def pregunta(orden, opciones=2, correcta="A", segundos=None, enunciado=None):
    return Pregunta(
        orden=orden,
        enunciado=enunciado or f"Pregunta {orden}",
        opciones=[f"opción {chr(ord('A') + i)}" for i in range(opciones)],
        correcta=correcta,
        segundos=segundos,
    )


def encuesta_competitiva(n_preguntas=3, segundos=30, puntaje_base=500, id=1):
    return Encuesta(
        id=id, nombre="Competencia de prueba", modalidad=MODALIDAD_COMPETENCIA,
        puntaje_base=puntaje_base, segundos=segundos,
        preguntas=[pregunta(i) for i in range(1, n_preguntas + 1)],
    )


def encuesta_anonima(n_preguntas=3, segundos=30, id=2):
    return Encuesta(
        id=id, nombre="Encuesta anónima de prueba", modalidad=MODALIDAD_ANONIMA,
        puntaje_base=0, segundos=segundos,
        preguntas=[pregunta(i, opciones=4, correcta=None)
                   for i in range(1, n_preguntas + 1)],
    )


# ------------------------------------------------------------------ fixtures
@pytest.fixture
def reloj():
    return RelojFalso()


@pytest.fixture
def avisos():
    return NotificadorFalso()


@pytest.fixture
def historial():
    return HistorialFalso()


@pytest.fixture
def armar(reloj, avisos, historial):
    """Devuelve una función que arma un servicio con las encuestas que se le pasen."""
    def _armar(*encuestas, timeout_presencia_s=15.0):
        return ServicioSesion(
            encuestas=RepoEncuestasFalso(*encuestas),
            pulsadores=RepoPulsadoresFalso(),
            historial=historial,
            notificador=avisos,
            reloj=reloj,
            timeout_presencia_s=timeout_presencia_s,
        )
    return _armar
