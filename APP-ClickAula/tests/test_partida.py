"""Máquina de estados de la partida (R3).

Todos estos tests corren en milisegundos porque la partida no consulta el
reloj: el instante entra como parámetro (R2).
"""
import pytest
from conftest import encuesta_anonima, encuesta_competitiva, pregunta

from dominio.modelo import (DUPLICADO, FUERA_DE_VENTANA, LOBBY,
                            OPCION_INVALIDA, PREGUNTA_ABIERTA, RESULTADOS,
                            RESUMEN, YA_VOTO, Encuesta,
                            MODALIDAD_COMPETENCIA)
from dominio.partida import Partida


def test_una_encuesta_sin_preguntas_no_arma_partida():
    vacia = Encuesta(id=9, nombre="vacía", modalidad=MODALIDAD_COMPETENCIA,
                     puntaje_base=500, segundos=30, preguntas=[])
    with pytest.raises(ValueError):
        Partida(vacia)


def test_arranca_en_la_sala_de_espera():
    p = Partida(encuesta_competitiva())
    assert p.estado == LOBBY
    assert p.pregunta_actual() is None
    assert p.restante_ms(0.0) is None


def test_comenzar_abre_la_primera_pregunta_y_fija_el_cierre():
    p = Partida(encuesta_competitiva(segundos=30))
    p.comenzar(100.0, presentes=4)

    assert p.estado == PREGUNTA_ABIERTA
    assert p.pregunta_actual().orden == 1
    assert p.esperados == 4
    assert p.cierra_en == 130.0
    assert p.restante_ms(100.0) == 30000
    assert p.restante_ms(129.5) == 500
    assert p.restante_ms(200.0) == 0        # nunca negativo


def test_no_se_puede_comenzar_dos_veces():
    p = Partida(encuesta_competitiva())
    p.comenzar(100.0, 1)
    with pytest.raises(ValueError):
        p.comenzar(101.0, 1)


def test_los_segundos_de_la_pregunta_pisan_los_de_la_encuesta():
    enc = Encuesta(id=1, nombre="x", modalidad=MODALIDAD_COMPETENCIA,
                   puntaje_base=500, segundos=30,
                   preguntas=[pregunta(1, segundos=5)])
    p = Partida(enc)
    p.comenzar(0.0, 1)
    assert p.cierra_en == 5.0


# ------------------------------------------------------------------- votos
def test_voto_valido_se_acepta_una_sola_vez_por_pulsador():
    p = Partida(encuesta_competitiva())
    p.comenzar(100.0, 2)

    assert p.registrar_voto("p1", "A", seq=1, instante=101.0) is None
    # Gana la primera pulsación: el cambio de opinión se descarta.
    assert p.registrar_voto("p1", "B", seq=2, instante=102.0) == YA_VOTO
    assert p.votos_de_actual()["p1"].opcion == "A"


def test_opcion_fuera_de_las_de_la_pregunta_se_descarta():
    p = Partida(encuesta_competitiva())          # preguntas de 2 opciones
    p.comenzar(100.0, 1)
    assert p.registrar_voto("p1", "C", seq=1, instante=101.0) == OPCION_INVALIDA
    assert p.registrar_voto("p1", "Z", seq=2, instante=101.0) == OPCION_INVALIDA


def test_voto_en_la_sala_de_espera_queda_afuera():
    p = Partida(encuesta_competitiva())
    assert p.registrar_voto("p1", "A", seq=1, instante=99.0) == FUERA_DE_VENTANA


def test_reenvio_con_la_misma_secuencia_se_descarta():
    p = Partida(encuesta_competitiva())
    p.comenzar(100.0, 1)
    assert p.registrar_voto("p1", "A", seq=7, instante=101.0) is None
    assert p.registrar_voto("p1", "A", seq=7, instante=101.1) == DUPLICADO


def test_sin_secuencia_no_hay_deduplicacion_pero_sigue_ganando_el_primero():
    p = Partida(encuesta_competitiva())
    p.comenzar(100.0, 1)
    assert p.registrar_voto("p1", "A", seq=None, instante=101.0) is None
    assert p.registrar_voto("p1", "A", seq=None, instante=101.1) == YA_VOTO


def test_un_pulsador_que_reinicia_su_contador_vuelve_a_votar():
    """Regresión del error de deduplicación (fase 0).

    El NodeMCU numera desde 1 cada vez que arranca. Si la lista de secuencias
    vistas durara toda la partida, sus votos quedarían descartados como
    duplicados para siempre y el pulsador aparecería mudo.
    """
    p = Partida(encuesta_competitiva(n_preguntas=3))
    p.comenzar(100.0, 1)

    assert p.registrar_voto("p1", "A", seq=1, instante=101.0) is None
    p.cerrar(130.0, presentes=1)
    p.siguiente(131.0, presentes=1)

    # Se reinició el pulsador: vuelve a mandar seq=1.
    assert p.registrar_voto("p1", "A", seq=1, instante=132.0) is None
    assert p.votos_de_actual()["p1"].opcion == "A"


def test_la_deduplicacion_sigue_valiendo_dentro_de_la_misma_pregunta():
    """La corrección de la fase 0 no debe aflojar la protección real."""
    p = Partida(encuesta_competitiva(n_preguntas=2))
    p.comenzar(100.0, 2)

    assert p.registrar_voto("p1", "A", seq=1, instante=101.0) is None
    assert p.registrar_voto("p2", "B", seq=1, instante=101.1) is None  # otro pulsador
    assert p.registrar_voto("p1", "A", seq=1, instante=101.2) == DUPLICADO


# ------------------------------------------------------------------ cierres
def test_vencio_solo_cuando_paso_el_tiempo_con_pregunta_abierta():
    p = Partida(encuesta_competitiva(segundos=10))
    assert p.vencio(99999.0) is False            # en la sala de espera, no
    p.comenzar(100.0, 1)
    assert p.vencio(109.9) is False
    assert p.vencio(110.0) is True


def test_cerrar_en_competencia_muestra_resultados_y_reparte():
    p = Partida(encuesta_competitiva(n_preguntas=2, puntaje_base=500))
    p.comenzar(100.0, 2)
    p.registrar_voto("p1", "A", 1, 101.0)
    p.registrar_voto("p2", "B", 1, 102.0)
    p.cerrar(130.0, presentes=2)

    assert p.estado == RESULTADOS
    assert p.cierra_en is None                   # el reloj no debe seguir corriendo
    assert p.puntajes["p1"] == 500
    assert p.puntajes["p2"] == 0

    r = p.resultados[-1]
    assert r.conteo == {"A": 1, "B": 1}
    assert r.respondieron == 2
    assert r.correctas == 1
    assert r.esperados == 2
    assert [a.pulsador for a in p.ultimos_aciertos] == ["p1"]


def test_en_anonima_no_hay_pantalla_intermedia():
    p = Partida(encuesta_anonima(n_preguntas=2))
    p.comenzar(100.0, 1)
    p.registrar_voto("p1", "C", 1, 101.0)
    p.cerrar(130.0, presentes=1)

    # Pasó directo a la pregunta 2, sin pasar por RESULTADOS.
    assert p.estado == PREGUNTA_ABIERTA
    assert p.pregunta_actual().orden == 2
    assert p.resultados[-1].conteo == {"A": 0, "B": 0, "C": 1, "D": 0}


def test_cerrar_sin_pregunta_abierta_es_un_error():
    p = Partida(encuesta_competitiva())
    with pytest.raises(ValueError):
        p.cerrar(100.0, 1)


def test_siguiente_solo_desde_resultados():
    p = Partida(encuesta_competitiva())
    p.comenzar(100.0, 1)
    with pytest.raises(ValueError):
        p.siguiente(101.0, 1)


def test_la_ultima_pregunta_termina_en_resumen():
    p = Partida(encuesta_competitiva(n_preguntas=2))
    p.comenzar(100.0, 1)
    p.cerrar(130.0, 1)
    p.siguiente(131.0, 1)
    p.cerrar(161.0, 1)
    p.siguiente(162.0, 1)

    assert p.estado == RESUMEN
    assert p.cierra_en is None
    assert len(p.resultados) == 2


def test_los_aciertos_se_recortan_al_podio_de_la_pregunta():
    p = Partida(encuesta_competitiva(n_preguntas=1))
    p.comenzar(100.0, 5)
    for i in range(1, 6):
        p.registrar_voto(f"p{i}", "A", i, 100.0 + i)
    p.cerrar(130.0, 5)

    assert len(p.ultimos_aciertos) == 3
    assert [a.posicion for a in p.ultimos_aciertos] == [1, 2, 3]


# ---------------------------------------------------------------- proyección
def test_el_leaderboard_ignora_pulsadores_desconocidos():
    p = Partida(encuesta_competitiva(n_preguntas=1))
    p.comenzar(100.0, 2)
    p.registrar_voto("conocido", "A", 1, 101.0)
    p.registrar_voto("fantasma", "A", 1, 102.0)
    p.cerrar(130.0, 2)

    numeros = {"conocido": 3}
    filas = p.leaderboard(lambda pid: numeros.get(pid))

    assert filas == [{"numero": 3, "puntaje": 500}]


def test_el_resumen_marca_la_pregunta_mas_facil_y_la_mas_dificil():
    p = Partida(encuesta_competitiva(n_preguntas=2))
    p.comenzar(100.0, 2)
    p.registrar_voto("p1", "A", 1, 101.0)       # 1 de 1 correcta: 100 %
    p.cerrar(130.0, 2)
    p.siguiente(131.0, 2)
    p.registrar_voto("p1", "B", 2, 132.0)       # 0 de 1 correcta: 0 %
    p.cerrar(161.0, 2)
    p.siguiente(162.0, 2)

    r = p.resumen(lambda pid: 1)
    assert r["mas_facil"] == 1
    assert r["mas_dificil"] == 2
    assert r["participantes"] == 2
    assert len(r["preguntas"]) == 2
    assert r["podio"] == [(1, 500)]


def test_el_resumen_de_una_anonima_no_tiene_podio():
    p = Partida(encuesta_anonima(n_preguntas=1))
    p.comenzar(100.0, 1)
    p.registrar_voto("p1", "A", 1, 101.0)
    p.cerrar(130.0, 1)

    assert p.estado == RESUMEN
    r = p.resumen(lambda pid: 1)
    assert r["podio"] == []
    assert r["mas_facil"] is None               # ninguna pregunta puntúa
    assert r["mas_dificil"] is None
