"""Reparto de puntaje de la modalidad competitiva.

Regla: solo puntúan las respuestas correctas, y el porcentaje depende del
orden de llegada entre ellas.

    1.ª correcta ........ 100 % del puntaje base
    2.ª correcta .........  90 %
    3.ª correcta .........  80 %
    4.ª en adelante ......  60 %
    incorrectas ..........   0

Módulo puro: sin reloj, sin entrada/salida, sin infraestructura (R1, R2).
"""
from .modelo import Acierto

ESCALONES = [1.00, 0.90, 0.80]
ESCALON_RESTO = 0.60


def porcentaje(posicion):
    """`posicion` es 1-based entre las respuestas CORRECTAS."""
    if posicion <= 0:
        raise ValueError("la posición arranca en 1")
    if posicion <= len(ESCALONES):
        return ESCALONES[posicion - 1]
    return ESCALON_RESTO


def puntos(posicion, puntaje_base):
    return int(round(puntaje_base * porcentaje(posicion)))


def repartir(votos, correcta, puntaje_base):
    """Calcula los puntos de una pregunta.

    votos: iterable de Voto.
    correcta: "A".."D", o None si la pregunta no puntúa.

    Devuelve ({pulsador: puntos}, [Acierto]) ordenado por llegada.
    """
    if not correcta:
        return {}, []

    aciertos = sorted((v for v in votos if v.opcion == correcta),
                      key=lambda v: v.recibido_en)

    asignados = {}
    detalle = []
    for i, v in enumerate(aciertos, start=1):
        p = puntos(i, puntaje_base)
        asignados[v.pulsador] = p
        detalle.append(Acierto(posicion=i, pulsador=v.pulsador, puntos=p))
    return asignados, detalle
