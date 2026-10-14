"""Servicio de sesión: orquestación, reloj y forma del snapshot (R3)."""
import pytest
from conftest import encuesta_anonima, encuesta_competitiva

from dominio.modelo import (LOBBY, PREGUNTA_ABIERTA, RESULTADOS, RESUMEN,
                            SIN_PARTIDA)

# Contrato con el frontend: estas claves son las que leen los .js de
# app/static/. Cambiarlas rompe el panel y la proyección.
CLAVES_SNAPSHOT = {
    "estado", "encuesta", "competitivo", "pregunta", "restante_ms",
    "esperados", "recibidos", "pulsadores", "conteo", "top_pregunta",
    "leaderboard", "resumen",
}


# ------------------------------------------------------------------ snapshot
def test_sin_partida_el_snapshot_tiene_la_forma_completa(armar):
    srv = armar(encuesta_competitiva())
    snap = srv.snapshot()

    assert set(snap) == CLAVES_SNAPSHOT
    assert snap["estado"] == SIN_PARTIDA
    assert snap["encuesta"] is None
    assert snap["pregunta"] is None
    assert snap["restante_ms"] is None
    assert snap["competitivo"] is False
    assert snap["pulsadores"] == []
    assert snap["leaderboard"] == []
    assert snap["top_pregunta"] == []
    assert snap["resumen"] is None


def test_con_pregunta_abierta_el_snapshot_conserva_la_forma(armar, reloj):
    srv = armar(encuesta_competitiva(segundos=30))
    srv.visto("p1")
    srv.iniciar(1)
    srv.comenzar()
    snap = srv.snapshot()

    assert set(snap) == CLAVES_SNAPSHOT
    assert snap["estado"] == PREGUNTA_ABIERTA
    assert snap["encuesta"] == {"id": 1, "nombre": "Competencia de prueba",
                                "modalidad": "competencia", "puntaje_base": 500}
    assert snap["competitivo"] is True
    assert snap["pregunta"]["orden"] == 1
    assert snap["pregunta"]["total"] == 3
    assert snap["pregunta"]["segundos"] == 30
    assert snap["restante_ms"] == 30000
    assert snap["esperados"] == 1
    assert snap["recibidos"] == 0
    assert snap["pulsadores"] == [{"id": "p1", "numero": 1, "online": True,
                                   "voto": False}]


def test_con_la_pregunta_abierta_no_se_filtra_la_respuesta_correcta(armar):
    srv = armar(encuesta_competitiva())
    srv.visto("p1")
    srv.iniciar(1)
    srv.comenzar()

    assert srv.snapshot()["pregunta"]["correcta"] is None
    # El modo espía (sólo en desarrollo) sí la revela: lo usa el simulador.
    assert srv.snapshot(espia=True)["pregunta"]["correcta"] == "A"


def test_al_cerrar_se_revela_la_correcta_y_aparece_el_conteo(armar, reloj):
    srv = armar(encuesta_competitiva())
    srv.visto("p1")
    srv.iniciar(1)
    srv.comenzar()
    srv.votar("p1", "A", seq=1)
    srv.cerrar_ahora()
    snap = srv.snapshot()

    assert snap["estado"] == RESULTADOS
    assert snap["pregunta"]["correcta"] == "A"
    assert snap["conteo"] == {"A": 1, "B": 0}
    assert snap["restante_ms"] is None
    assert snap["top_pregunta"] == [{"numero": 1, "puntos": 500, "posicion": 1}]
    assert snap["leaderboard"] == [{"numero": 1, "puntaje": 500}]
    assert snap["pulsadores"][0]["voto"] is True


def test_el_leaderboard_queda_vacio_en_una_anonima(armar):
    srv = armar(encuesta_anonima())
    srv.visto("p1")
    srv.iniciar(2)
    srv.comenzar()
    srv.votar("p1", "C", seq=1)
    snap = srv.snapshot()

    assert snap["competitivo"] is False
    assert snap["leaderboard"] == []


# ------------------------------------------------------------------ comandos
def test_iniciar_una_encuesta_que_no_existe_es_un_conflicto(armar):
    srv = armar(encuesta_competitiva())
    with pytest.raises(ValueError):
        srv.iniciar(999)


def test_los_comandos_fuera_de_orden_no_rompen_nada(armar):
    srv = armar(encuesta_competitiva())
    with pytest.raises(ValueError):
        srv.comenzar()
    with pytest.raises(ValueError):
        srv.cerrar_ahora()
    with pytest.raises(ValueError):
        srv.siguiente()
    with pytest.raises(ValueError):
        srv.finalizar()
    assert srv.snapshot()["estado"] == SIN_PARTIDA


def test_iniciar_deja_la_partida_en_la_sala_de_espera(armar):
    srv = armar(encuesta_competitiva())
    srv.iniciar(1)
    assert srv.snapshot()["estado"] == LOBBY


def test_abortar_libera_el_servicio(armar):
    srv = armar(encuesta_competitiva())
    srv.iniciar(1)
    srv.comenzar()
    srv.abortar()
    assert srv.snapshot()["estado"] == SIN_PARTIDA
    assert srv.partida is None


def test_finalizar_archiva_el_resumen_y_libera_el_servicio(armar, historial):
    srv = armar(encuesta_competitiva(n_preguntas=1))
    srv.visto("p1")
    srv.iniciar(1)
    srv.comenzar()
    srv.votar("p1", "A", seq=1)
    srv.cerrar_ahora()
    srv.siguiente()
    assert srv.snapshot()["estado"] == RESUMEN

    ej_id = srv.finalizar()

    assert ej_id == 1
    assert len(historial.guardados) == 1
    guardado = historial.guardados[0]
    assert guardado["nombre_encuesta"] == "Competencia de prueba"
    assert guardado["podio"] == [(1, 500)]
    assert srv.snapshot()["estado"] == SIN_PARTIDA


# --------------------------------------------------------------------- votos
def test_un_voto_sin_partida_queda_fuera_de_ventana(armar):
    srv = armar(encuesta_competitiva())
    assert srv.votar("p1", "A", seq=1) == "fuera_de_ventana"
    # Pero el pulsador quedó registrado: ya mandó señales de vida.
    assert srv.snapshot()["pulsadores"][0]["numero"] == 1


def test_el_primer_mensaje_de_un_pulsador_le_asigna_numero(armar):
    srv = armar(encuesta_competitiva())
    srv.visto("abc")
    srv.visto("def")
    assert [p["numero"] for p in srv.snapshot()["pulsadores"]] == [1, 2]


def test_un_pulsador_que_reinicia_sigue_votando_en_la_partida_siguiente(armar):
    """Regresión del error reportado: 'en la encuesta anónima no me votan'.

    Pasaba al reiniciar el simulador entre dos partidas: volvía a numerar sus
    mensajes desde 1 y la aplicación los descartaba como reenvíos de los de la
    partida anterior.
    """
    srv = armar(encuesta_competitiva(n_preguntas=1), encuesta_anonima(n_preguntas=3))
    srv.visto("p1")

    # Primera partida: usa las secuencias 1 y 2.
    srv.iniciar(1)
    srv.comenzar()
    assert srv.votar("p1", "A", seq=1) is None
    srv.cerrar_ahora()
    srv.siguiente()
    srv.finalizar()

    # Se reinicia el pulsador y arranca otra partida: vuelve a numerar desde 1.
    srv.iniciar(2)
    srv.comenzar()
    for seq, opcion in enumerate(["A", "B", "C"], start=1):
        assert srv.votar("p1", opcion, seq=seq) is None, f"se descartó seq={seq}"
        if srv.snapshot()["estado"] == PREGUNTA_ABIERTA:
            srv.cerrar_ahora()

    resultados = srv.partida.resultados
    assert [r.respondieron for r in resultados] == [1, 1, 1]


def test_los_descartes_no_empujan_snapshot_pero_los_votos_si(armar, avisos):
    srv = armar(encuesta_competitiva())
    srv.visto("p1")
    srv.iniciar(1)
    srv.comenzar()

    antes = len(avisos.snapshots)
    assert srv.votar("p1", "A", seq=1) is None
    assert len(avisos.snapshots) == antes + 1

    antes = len(avisos.snapshots)
    assert srv.votar("p1", "A", seq=1) == "duplicado"
    assert len(avisos.snapshots) == antes


# --------------------------------------------------------------------- reloj
def test_el_reloj_cierra_la_pregunta_al_vencer_el_tiempo(armar, reloj):
    srv = armar(encuesta_competitiva(segundos=10))
    srv.visto("p1")
    srv.iniciar(1)
    srv.comenzar()

    reloj.avanzar(9.9)
    srv.tic()
    assert srv.snapshot()["estado"] == PREGUNTA_ABIERTA

    reloj.avanzar(0.2)
    srv.tic()
    assert srv.snapshot()["estado"] == RESULTADOS


def test_el_cierre_por_tiempo_no_necesita_ningun_navegador(armar, reloj, avisos):
    """La autoridad es el servidor: el cierre ocurre sin pestañas abiertas."""
    srv = armar(encuesta_anonima(n_preguntas=1, segundos=5))
    srv.visto("p1")
    srv.iniciar(2)
    srv.comenzar()
    avisos.snapshots.clear()

    reloj.avanzar(6)
    srv.tic()

    assert srv.snapshot()["estado"] == RESUMEN
    assert avisos.snapshots, "el cierre por tiempo tiene que avisar a la proyección"


def test_el_reloj_da_por_caidos_a_los_que_dejan_de_latir(armar, reloj):
    srv = armar(encuesta_competitiva(), timeout_presencia_s=15.0)
    srv.visto("p1")

    reloj.avanzar(10)
    srv.tic()
    assert srv.snapshot()["pulsadores"][0]["online"] is True

    reloj.avanzar(10)
    srv.tic()
    assert srv.snapshot()["pulsadores"][0]["online"] is False


def test_los_esperados_se_fijan_con_los_presentes_al_abrir(armar, reloj):
    srv = armar(encuesta_competitiva(n_preguntas=2))
    srv.visto("p1")
    srv.visto("p2")
    srv.iniciar(1)
    srv.comenzar()
    assert srv.snapshot()["esperados"] == 2

    # Se cae uno antes de la segunda pregunta.
    srv.visto("p2", online=False)
    srv.cerrar_ahora()
    srv.siguiente()
    assert srv.snapshot()["esperados"] == 1


def test_un_tic_sin_cambios_no_molesta_a_los_navegadores(armar, avisos):
    srv = armar(encuesta_competitiva())
    srv.visto("p1")
    avisos.snapshots.clear()
    srv.tic()
    assert avisos.snapshots == []
