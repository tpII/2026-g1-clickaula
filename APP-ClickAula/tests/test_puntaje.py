"""Reparto de puntaje de la modalidad competitiva (R3)."""
import pytest

from dominio import puntaje
from dominio.modelo import Voto


def voto(pid, opcion, t):
    return Voto(pulsador=pid, opcion=opcion, recibido_en=t)


def test_escalones_por_orden_de_llegada():
    assert puntaje.porcentaje(1) == 1.00
    assert puntaje.porcentaje(2) == 0.90
    assert puntaje.porcentaje(3) == 0.80
    assert puntaje.porcentaje(4) == 0.60
    assert puntaje.porcentaje(40) == 0.60


def test_posicion_cero_es_un_error_de_programacion():
    with pytest.raises(ValueError):
        puntaje.porcentaje(0)


def test_solo_puntuan_las_correctas_y_en_orden_de_llegada():
    votos = [voto("p1", "A", 10.0), voto("p2", "B", 10.1),
             voto("p3", "A", 10.2), voto("p4", "A", 10.3)]
    asignados, detalle = puntaje.repartir(votos, "A", 500)

    assert asignados == {"p1": 500, "p3": 450, "p4": 400}
    assert "p2" not in asignados                   # votó mal: cero
    assert [a.posicion for a in detalle] == [1, 2, 3]
    assert [a.pulsador for a in detalle] == ["p1", "p3", "p4"]


def test_el_orden_lo_da_el_instante_no_el_orden_de_la_lista():
    # Llegan desordenados: MQTT no garantiza orden entre publicadores distintos.
    votos = [voto("tarde", "A", 20.0), voto("temprano", "A", 10.0)]
    asignados, detalle = puntaje.repartir(votos, "A", 100)

    assert asignados["temprano"] == 100
    assert asignados["tarde"] == 90
    assert detalle[0].pulsador == "temprano"


def test_cuarta_correcta_en_adelante_cobra_el_escalon_de_resto():
    votos = [voto(f"p{i}", "A", 10.0 + i) for i in range(1, 7)]
    asignados, _ = puntaje.repartir(votos, "A", 1000)

    assert [asignados[f"p{i}"] for i in range(1, 7)] == \
        [1000, 900, 800, 600, 600, 600]


def test_pregunta_sin_respuesta_correcta_no_reparte_nada():
    votos = [voto("p1", "A", 10.0), voto("p2", "B", 10.1)]
    assert puntaje.repartir(votos, None, 500) == ({}, [])


def test_sin_votos_no_reparte_nada():
    assert puntaje.repartir([], "A", 500) == ({}, [])
