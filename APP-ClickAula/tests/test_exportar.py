"""Exportación de resultados a CSV.

Se prueba el texto del archivo, no la ruta web: el armado es una función pura y
los errores que importan son de formato, no de HTTP.
"""
import csv
import io

from app import exportar


def ejecucion(modalidad="competencia", podio=None, preguntas=None):
    return {
        "id": 1,
        "encuesta_id": 1,
        "nombre_encuesta": "Repaso de Redes — Módulo 1",
        "modalidad": modalidad,
        "fecha": "2026-10-12T14:35:02",
        "participantes": 6,
        "preguntas": preguntas if preguntas is not None else [
            {
                "orden": 1,
                "enunciado": "¿Qué capa fragmenta los paquetes?",
                "opciones": ["Enlace", "Red", "Transporte", "Aplicación"],
                "correcta": "B",
                "conteo": {"A": 1, "B": 3, "C": 2, "D": 0},
                "esperados": 6,
                "respondieron": 6,
                "correctas": 3,
            },
            {
                "orden": 2,
                "enunciado": "¿TCP garantiza el orden de llegada?",
                "opciones": ["Sí", "No"],
                "correcta": "A",
                "conteo": {"A": 4, "B": 0},
                "esperados": 6,
                "respondieron": 4,
                "correctas": 4,
            },
        ],
        "podio": podio if podio is not None else [
            {"puesto": 1, "pulsador_numero": 4, "puntaje": 1850},
            {"puesto": 2, "pulsador_numero": 1, "puntaje": 1800},
        ],
    }


def leer(texto):
    """Parsea el CSV como lo haría una planilla, descartando la marca UTF-8."""
    assert texto.startswith("﻿"), "falta la marca UTF-8 que necesita Excel"
    return list(csv.reader(io.StringIO(texto[1:]), delimiter=";"))


# ------------------------------------------------------------------ formato
def test_el_separador_es_punto_y_coma():
    texto = exportar.csv_preguntas(ejecucion())
    primera = texto[1:].splitlines()[0]
    assert ";" in primera
    # Un enunciado con coma no debe partir la fila.
    assert len(leer(texto)[0]) == len(exportar.ENCABEZADO_PREGUNTAS)


def test_los_decimales_van_con_coma():
    filas = leer(exportar.csv_preguntas(ejecucion()))
    pct = filas[1][-1]
    assert pct == "50,0"          # 3 de 6
    assert "." not in pct


def test_el_enunciado_con_punto_y_coma_se_entrecomilla():
    preg = {
        "orden": 1, "enunciado": "Elegí una; sólo una",
        "opciones": ["Sí", "No"], "correcta": "A",
        "conteo": {"A": 1, "B": 0}, "esperados": 1,
        "respondieron": 1, "correctas": 1,
    }
    filas = leer(exportar.csv_preguntas(ejecucion(preguntas=[preg])))
    assert filas[1][1] == "Elegí una; sólo una"
    assert len(filas[1]) == len(exportar.ENCABEZADO_PREGUNTAS)


# ------------------------------------------------------------------ contenido
def test_una_fila_por_pregunta_mas_el_encabezado():
    filas = leer(exportar.csv_preguntas(ejecucion()))
    assert filas[0] == exportar.ENCABEZADO_PREGUNTAS
    assert len(filas) == 3


def test_la_fila_lleva_los_textos_de_las_opciones_y_los_votos():
    filas = leer(exportar.csv_preguntas(ejecucion()))
    fila = filas[1]
    cols = dict(zip(exportar.ENCABEZADO_PREGUNTAS, fila))

    assert cols["Pregunta"] == "1"
    assert cols["Opción A"] == "Enlace"
    assert cols["Opción D"] == "Aplicación"
    assert cols["Correcta"] == "B"
    assert cols["Votos B"] == "3"
    assert cols["Respondieron"] == "6"
    assert cols["Sin responder"] == "0"


def test_las_opciones_que_la_pregunta_no_tiene_quedan_vacias():
    """Sin esto, una pregunta de dos opciones mostraría 0 votos en C y D,
    que se lee como 'nadie eligió C' en lugar de 'no existía C'."""
    filas = leer(exportar.csv_preguntas(ejecucion()))
    cols = dict(zip(exportar.ENCABEZADO_PREGUNTAS, filas[2]))

    assert cols["Opción C"] == ""
    assert cols["Votos C"] == ""
    assert cols["Votos D"] == ""
    assert cols["Votos A"] == "4"


def test_los_que_no_respondieron_se_calculan():
    filas = leer(exportar.csv_preguntas(ejecucion()))
    cols = dict(zip(exportar.ENCABEZADO_PREGUNTAS, filas[2]))
    assert cols["Esperados"] == "6"
    assert cols["Respondieron"] == "4"
    assert cols["Sin responder"] == "2"


def test_una_pregunta_sin_respuesta_correcta_no_informa_acierto():
    preg = {
        "orden": 1, "enunciado": "¿Te gustó la actividad?",
        "opciones": ["Mucho", "Poco"], "correcta": None,
        "conteo": {"A": 5, "B": 1}, "esperados": 6,
        "respondieron": 6, "correctas": 0,
    }
    filas = leer(exportar.csv_preguntas(ejecucion(modalidad="anonima",
                                                  preguntas=[preg], podio=[])))
    cols = dict(zip(exportar.ENCABEZADO_PREGUNTAS, filas[1]))

    assert cols["Correcta"] == ""
    assert cols["Correctas"] == ""
    assert cols["% de acierto"] == ""
    assert cols["Votos A"] == "5"          # los votos sí se informan


def test_sin_respuestas_no_se_divide_por_cero():
    preg = {
        "orden": 1, "enunciado": "Nadie contestó", "opciones": ["Sí", "No"],
        "correcta": "A", "conteo": {"A": 0, "B": 0}, "esperados": 3,
        "respondieron": 0, "correctas": 0,
    }
    filas = leer(exportar.csv_preguntas(ejecucion(preguntas=[preg])))
    cols = dict(zip(exportar.ENCABEZADO_PREGUNTAS, filas[1]))
    assert cols["% de acierto"] == ""
    assert cols["Sin responder"] == "3"


# --------------------------------------------------------------------- podio
def test_el_podio_sale_ordenado_por_puesto():
    filas = leer(exportar.csv_podio(ejecucion()))
    assert filas[0] == exportar.ENCABEZADO_PODIO
    assert filas[1] == ["1", "4", "1850"]
    assert filas[2] == ["2", "1", "1800"]


def test_la_encuesta_anonima_no_tiene_podio():
    """Aunque la base trajera filas, en anónima no hay puntaje que publicar."""
    ej = ejecucion(modalidad="anonima")
    assert exportar.filas_podio(ej) == []


# -------------------------------------------------------- R6: sólo agregados
def test_el_csv_no_puede_contener_votos_individuales():
    """R6. El identificador del pulsador no está en la base, así que no puede
    aparecer acá; el test lo deja escrito para que siga siendo cierto."""
    ej = ejecucion()
    texto = exportar.csv_preguntas(ej) + exportar.csv_podio(ej)
    for prohibido in ("pulsador_id", "3a1f5c", "voto_de", "recibido_en"):
        assert prohibido not in texto


# ------------------------------------------------------------------- nombre
def test_el_nombre_del_archivo_es_usable_en_cualquier_sistema():
    nombre = exportar.nombre_archivo(ejecucion(), "preguntas")
    assert nombre == "clickaula_repaso-de-redes-modulo-1_2026-10-12_preguntas.csv"


def test_un_nombre_de_encuesta_imposible_no_rompe_el_archivo():
    ej = ejecucion()
    ej["nombre_encuesta"] = "???"
    ej["fecha"] = ""
    assert exportar.nombre_archivo(ej, "podio") == \
        "clickaula_encuesta_sin-fecha_podio.csv"
