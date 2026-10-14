"""Acceso a SQLite.

Un solo proceso escribe la base, así que alcanza con una conexión por hilo y
el modo WAL. No se guardan votos individuales: el histórico conserva sólo
agregados, tal como se definió con el grupo.
"""
import json
import os
import sqlite3
import threading
from datetime import datetime

from . import config

_local = threading.local()

ESQUEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS encuesta (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL,
    modalidad    TEXT NOT NULL,
    puntaje_base INTEGER NOT NULL,
    segundos     INTEGER NOT NULL,
    creada_en    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pregunta (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    encuesta_id  INTEGER NOT NULL REFERENCES encuesta(id) ON DELETE CASCADE,
    orden        INTEGER NOT NULL,
    enunciado    TEXT NOT NULL,
    opciones     TEXT NOT NULL,          -- JSON: ["texto A", "texto B", ...]
    correcta     TEXT,                   -- "A".."D" o NULL si no puntúa
    segundos     INTEGER                 -- NULL = usa el de la encuesta
);
CREATE INDEX IF NOT EXISTS ix_pregunta_encuesta ON pregunta(encuesta_id, orden);

-- Un pulsador se registra la primera vez que se lo escucha. El número es
-- estable y es lo que se muestra en pantalla ("Pulsador 03").
CREATE TABLE IF NOT EXISTS pulsador (
    id          TEXT PRIMARY KEY,
    numero      INTEGER NOT NULL UNIQUE,
    primera_vez TEXT NOT NULL,
    ultima_vez  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ejecucion (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    encuesta_id     INTEGER,
    nombre_encuesta TEXT NOT NULL,
    modalidad       TEXT NOT NULL,
    fecha           TEXT NOT NULL,
    participantes   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ejecucion_pregunta (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id  INTEGER NOT NULL REFERENCES ejecucion(id) ON DELETE CASCADE,
    orden         INTEGER NOT NULL,
    enunciado     TEXT NOT NULL,
    opciones      TEXT NOT NULL,
    correcta      TEXT,
    conteo        TEXT NOT NULL,         -- JSON: {"A": 3, "B": 1, ...}
    esperados     INTEGER NOT NULL,
    respondieron  INTEGER NOT NULL,
    correctas     INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ejpreg ON ejecucion_pregunta(ejecucion_id, orden);

CREATE TABLE IF NOT EXISTS ejecucion_podio (
    ejecucion_id     INTEGER NOT NULL REFERENCES ejecucion(id) ON DELETE CASCADE,
    puesto           INTEGER NOT NULL,
    pulsador_numero  INTEGER NOT NULL,
    puntaje          INTEGER NOT NULL,
    PRIMARY KEY (ejecucion_id, puesto)
);
"""


def conn():
    if not hasattr(_local, "c"):
        os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
        c = sqlite3.connect(config.DB_PATH, timeout=10, check_same_thread=False)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        _local.c = c
    return _local.c


def init():
    conn().executescript(ESQUEMA)
    conn().commit()


def ahora():
    return datetime.now().isoformat(timespec="seconds")


# --------------------------------------------------------------- encuestas
def listar_encuestas():
    filas = conn().execute(
        """SELECT e.*, (SELECT COUNT(*) FROM pregunta p WHERE p.encuesta_id = e.id)
                        AS n_preguntas
           FROM encuesta e ORDER BY e.creada_en DESC"""
    ).fetchall()
    return [dict(f) for f in filas]


def obtener_encuesta(enc_id):
    f = conn().execute("SELECT * FROM encuesta WHERE id=?", (enc_id,)).fetchone()
    if not f:
        return None
    enc = dict(f)
    enc["preguntas"] = [
        {**dict(p), "opciones": json.loads(p["opciones"])}
        for p in conn().execute(
            "SELECT * FROM pregunta WHERE encuesta_id=? ORDER BY orden", (enc_id,)
        )
    ]
    return enc


def guardar_encuesta(datos, enc_id=None):
    """datos: {nombre, modalidad, puntaje_base, segundos, preguntas:[...]}"""
    c = conn()
    with c:
        if enc_id:
            c.execute(
                """UPDATE encuesta SET nombre=?, modalidad=?, puntaje_base=?, segundos=?
                   WHERE id=?""",
                (datos["nombre"], datos["modalidad"], datos["puntaje_base"],
                 datos["segundos"], enc_id),
            )
            c.execute("DELETE FROM pregunta WHERE encuesta_id=?", (enc_id,))
        else:
            cur = c.execute(
                """INSERT INTO encuesta (nombre, modalidad, puntaje_base, segundos, creada_en)
                   VALUES (?,?,?,?,?)""",
                (datos["nombre"], datos["modalidad"], datos["puntaje_base"],
                 datos["segundos"], ahora()),
            )
            enc_id = cur.lastrowid
        for i, p in enumerate(datos["preguntas"], start=1):
            c.execute(
                """INSERT INTO pregunta (encuesta_id, orden, enunciado, opciones, correcta, segundos)
                   VALUES (?,?,?,?,?,?)""",
                (enc_id, i, p["enunciado"], json.dumps(p["opciones"], ensure_ascii=False),
                 p.get("correcta"), p.get("segundos")),
            )
    return enc_id


def borrar_encuesta(enc_id):
    with conn() as c:
        c.execute("DELETE FROM encuesta WHERE id=?", (enc_id,))


# --------------------------------------------------------------- pulsadores
def registrar_pulsador(pid):
    """Devuelve el número estable del pulsador, creándolo si es nuevo."""
    c = conn()
    f = c.execute("SELECT numero FROM pulsador WHERE id=?", (pid,)).fetchone()
    if f:
        c.execute("UPDATE pulsador SET ultima_vez=? WHERE id=?", (ahora(), pid))
        c.commit()
        return f["numero"]
    with c:
        mx = c.execute("SELECT COALESCE(MAX(numero),0) n FROM pulsador").fetchone()["n"]
        numero = mx + 1
        c.execute(
            "INSERT INTO pulsador (id, numero, primera_vez, ultima_vez) VALUES (?,?,?,?)",
            (pid, numero, ahora(), ahora()),
        )
    return numero


# --------------------------------------------------------------- histórico
def guardar_ejecucion(resumen):
    c = conn()
    with c:
        cur = c.execute(
            """INSERT INTO ejecucion (encuesta_id, nombre_encuesta, modalidad, fecha, participantes)
               VALUES (?,?,?,?,?)""",
            (resumen["encuesta_id"], resumen["nombre_encuesta"], resumen["modalidad"],
             ahora(), resumen["participantes"]),
        )
        ej_id = cur.lastrowid
        for p in resumen["preguntas"]:
            c.execute(
                """INSERT INTO ejecucion_pregunta
                   (ejecucion_id, orden, enunciado, opciones, correcta, conteo,
                    esperados, respondieron, correctas)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (ej_id, p["orden"], p["enunciado"],
                 json.dumps(p["opciones"], ensure_ascii=False), p["correcta"],
                 json.dumps(p["conteo"]), p["esperados"], p["respondieron"],
                 p["correctas"]),
            )
        for i, (numero, puntaje) in enumerate(resumen.get("podio", []), start=1):
            c.execute(
                """INSERT INTO ejecucion_podio (ejecucion_id, puesto, pulsador_numero, puntaje)
                   VALUES (?,?,?,?)""",
                (ej_id, i, numero, puntaje),
            )
    return ej_id


def listar_ejecuciones():
    return [dict(f) for f in conn().execute(
        "SELECT * FROM ejecucion ORDER BY fecha DESC, id DESC")]


def obtener_ejecucion(ej_id):
    f = conn().execute("SELECT * FROM ejecucion WHERE id=?", (ej_id,)).fetchone()
    if not f:
        return None
    ej = dict(f)
    ej["preguntas"] = [
        {**dict(p), "opciones": json.loads(p["opciones"]), "conteo": json.loads(p["conteo"])}
        for p in conn().execute(
            "SELECT * FROM ejecucion_pregunta WHERE ejecucion_id=? ORDER BY orden", (ej_id,))
    ]
    ej["podio"] = [dict(p) for p in conn().execute(
        "SELECT * FROM ejecucion_podio WHERE ejecucion_id=? ORDER BY puesto", (ej_id,))]
    return ej
