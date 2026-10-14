"""Adaptadores de persistencia: implementan los puertos de `dominio/puertos.py`.

Acá y sólo acá se traduce entre las filas de SQLite y los objetos del dominio.
Si mañana la base cambia, cambia este archivo; `dominio/` y `servicios/` no se
enteran.

Las vistas de biblioteca, editor e historial siguen leyendo `db` directamente:
eso es material de pantalla, no reglas de juego, y no gana nada pasando por el
dominio.
"""
from dominio.modelo import Encuesta, Pregunta

from . import bus, db


class RepoEncuestas:
    def obtener(self, encuesta_id):
        d = db.obtener_encuesta(encuesta_id)
        if not d:
            return None
        return Encuesta(
            id=d["id"],
            nombre=d["nombre"],
            modalidad=d["modalidad"],
            puntaje_base=d["puntaje_base"],
            segundos=d["segundos"],
            preguntas=[
                Pregunta(
                    orden=p["orden"],
                    enunciado=p["enunciado"],
                    opciones=p["opciones"],
                    correcta=p["correcta"],
                    segundos=p["segundos"],
                )
                for p in d["preguntas"]
            ],
        )


class RepoPulsadores:
    def numero_de(self, pulsador_id):
        return db.registrar_pulsador(pulsador_id)


class RepoHistorial:
    def guardar(self, resumen):
        return db.guardar_ejecucion(resumen)


class NotificadorSSE:
    """Empuja el snapshot al bus de Server-Sent Events.

    Se traga los errores a propósito: que un navegador se desconecte no puede
    hacer fallar el cierre de una pregunta.
    """

    def publicar(self, snapshot):
        try:
            bus.publicar(snapshot)
        except Exception as e:
            print("[sse] no se pudo publicar:", e, flush=True)
