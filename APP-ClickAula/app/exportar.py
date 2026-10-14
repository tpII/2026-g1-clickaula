"""Exportación de resultados a CSV.

Funciones puras: entra el diccionario que devuelve `db.obtener_ejecucion` y
sale el texto del archivo. No tocan Flask ni la base, así que se prueban
directo (`tests/test_exportar.py`).

**Dos decisiones de formato que parecen raras y no lo son.**

El separador es punto y coma y los decimales llevan coma, porque Excel en
español interpreta así los CSV. Con separador de coma, un archivo con tildes y
decimales se abre todo apilado en la primera columna, y el que lo recibe
concluye que el sistema exporta mal.

El archivo arranca con la marca de orden de bytes (`\\ufeff`). Sin ella, Excel
en Windows lee el UTF-8 como si fuera Latin-1 y los enunciados aparecen con
"Ã¡" en lugar de "á".

Lo que se exporta son **sólo agregados** (R6): por pregunta, cuántos votaron
cada opción. El voto individual de un pulsador no está en la base y por lo
tanto no puede salir en el CSV, que es lo que hace que la modalidad anónima sea
anónima de verdad.
"""
import csv
import io
import re
import unicodedata

from dominio.modelo import MODALIDAD_COMPETENCIA, OPCIONES

SEPARADOR = ";"
MARCA_UTF8 = "﻿"

ENCABEZADO_PREGUNTAS = (
    ["Pregunta", "Enunciado"]
    + [f"Opción {l}" for l in OPCIONES]
    + ["Correcta"]
    + [f"Votos {l}" for l in OPCIONES]
    + ["Esperados", "Respondieron", "Sin responder", "Correctas",
       "% de acierto"]
)

ENCABEZADO_PODIO = ["Puesto", "Pulsador", "Puntaje"]


def _decimal(valor):
    """Un decimal con coma, como lo espera una planilla en español."""
    return f"{valor:.1f}".replace(".", ",")


def _porcentaje_acierto(preg):
    if not preg["correcta"] or not preg["respondieron"]:
        return ""
    return _decimal(preg["correctas"] / preg["respondieron"] * 100)


def filas_preguntas(ejecucion):
    """Una fila por pregunta. Las opciones que la pregunta no tiene van vacías."""
    filas = []
    for preg in ejecucion["preguntas"]:
        opciones = list(preg["opciones"])
        usadas = len(opciones)
        textos = opciones + [""] * (len(OPCIONES) - usadas)
        votos = [preg["conteo"].get(l, 0) if i < usadas else ""
                 for i, l in enumerate(OPCIONES)]
        filas.append(
            [preg["orden"], preg["enunciado"]]
            + textos
            + [preg["correcta"] or ""]
            + votos
            + [preg["esperados"],
               preg["respondieron"],
               max(0, preg["esperados"] - preg["respondieron"]),
               preg["correctas"] if preg["correcta"] else "",
               _porcentaje_acierto(preg)]
        )
    return filas


def filas_podio(ejecucion):
    """Vacío en la modalidad anónima: ahí no hay puntaje ni puestos."""
    if ejecucion["modalidad"] != MODALIDAD_COMPETENCIA:
        return []
    return [[p["puesto"], p["pulsador_numero"], p["puntaje"]]
            for p in ejecucion.get("podio", [])]


def _armar(encabezado, filas):
    buffer = io.StringIO()
    # lineterminator explícito: el de por defecto es "\r\n" sólo en Windows y
    # queremos el mismo archivo en las dos plataformas.
    escritor = csv.writer(buffer, delimiter=SEPARADOR, lineterminator="\r\n",
                          quoting=csv.QUOTE_MINIMAL)
    escritor.writerow(encabezado)
    escritor.writerows(filas)
    return MARCA_UTF8 + buffer.getvalue()


def csv_preguntas(ejecucion):
    return _armar(ENCABEZADO_PREGUNTAS, filas_preguntas(ejecucion))


def csv_podio(ejecucion):
    return _armar(ENCABEZADO_PODIO, filas_podio(ejecucion))


def _trozo(texto, por_defecto="encuesta"):
    """Pasa un nombre a algo que sirva de nombre de archivo en cualquier sistema."""
    plano = unicodedata.normalize("NFKD", texto or "")
    plano = plano.encode("ascii", "ignore").decode("ascii").lower()
    plano = re.sub(r"[^a-z0-9]+", "-", plano).strip("-")
    return plano[:60] or por_defecto


def nombre_archivo(ejecucion, sufijo):
    """Ej.: clickaula_repaso-de-redes_2026-10-12_preguntas.csv

    Lleva el nombre de la encuesta y la fecha porque estos archivos terminan
    todos juntos en la carpeta de descargas.
    """
    fecha = (ejecucion.get("fecha") or "")[:10] or "sin-fecha"
    return (f"clickaula_{_trozo(ejecucion.get('nombre_encuesta'))}"
            f"_{fecha}_{sufijo}.csv")
