"""Máquina de estados de una partida.

Núcleo del sistema. Es puro: no consulta el reloj, no toca la base, no
publica nada (R1, R2). El instante entra siempre como parámetro, lo que
permite probar una partida completa en milisegundos en lugar de esperar
treinta segundos por pregunta.

Quien lo orquesta es `servicios.sesion.ServicioSesion`.
"""
import collections

from . import puntaje
from .modelo import (DUPLICADO, FUERA_DE_VENTANA, LOBBY, OPCION_INVALIDA,
                     PREGUNTA_ABIERTA, RESULTADOS, RESUMEN, YA_VOTO,
                     ResultadoPregunta, Voto)


class Partida:
    def __init__(self, encuesta):
        if not encuesta.preguntas:
            raise ValueError("la encuesta no tiene preguntas")
        self.encuesta = encuesta
        self.estado = LOBBY
        self.idx = -1
        self.cierra_en = None
        self.esperados = 0
        self.votos = {}                 # orden -> {pulsador: Voto}
        self.puntajes = collections.defaultdict(int)
        self.resultados = []            # [ResultadoPregunta]
        self.ultimos_aciertos = []      # [Acierto] de la última pregunta
        # Claves (pulsador, seq) ya procesadas, para descartar los reenvíos de
        # QoS 1. Se vacía al abrir cada pregunta: un pulsador que se reinicia
        # vuelve a numerar desde 1 y, si la lista durara toda la sesión, sus
        # votos quedarían descartados como duplicados para siempre.
        self._seq_vistos = collections.deque(maxlen=200)

    # ------------------------------------------------------------ consultas
    @property
    def total_preguntas(self):
        return len(self.encuesta.preguntas)

    def pregunta_actual(self):
        if 0 <= self.idx < self.total_preguntas:
            return self.encuesta.preguntas[self.idx]
        return None

    def votos_de_actual(self):
        preg = self.pregunta_actual()
        return self.votos.get(preg.orden, {}) if preg else {}

    def restante_ms(self, instante):
        if self.cierra_en is None:
            return None
        return int(max(0, (self.cierra_en - instante) * 1000))

    def vencio(self, instante):
        return (self.estado == PREGUNTA_ABIERTA
                and self.cierra_en is not None
                and instante >= self.cierra_en)

    # ------------------------------------------------------------- comandos
    def comenzar(self, instante, presentes):
        if self.estado != LOBBY:
            raise ValueError("la partida ya comenzó")
        self._abrir(0, instante, presentes)

    def registrar_voto(self, pulsador_id, opcion, seq, instante):
        """Devuelve el motivo del descarte, o None si el voto se aceptó."""
        if seq is not None:
            clave = (pulsador_id, seq)
            if clave in self._seq_vistos:
                return DUPLICADO
            self._seq_vistos.append(clave)

        if self.estado != PREGUNTA_ABIERTA:
            return FUERA_DE_VENTANA

        preg = self.pregunta_actual()
        if not preg.admite(opcion):
            return OPCION_INVALIDA

        caja = self.votos.setdefault(preg.orden, {})
        if pulsador_id in caja:
            return YA_VOTO                   # gana la primera pulsación

        caja[pulsador_id] = Voto(pulsador=pulsador_id, opcion=opcion,
                                 recibido_en=instante)
        return None

    def cerrar(self, instante, presentes):
        if self.estado != PREGUNTA_ABIERTA:
            raise ValueError("no hay una pregunta abierta")
        preg = self.pregunta_actual()
        votos = list(self.votos.get(preg.orden, {}).values())

        self.resultados.append(self._resultado_de(preg, votos))
        self.ultimos_aciertos = []

        if self.encuesta.competitiva:
            ganados, aciertos = puntaje.repartir(
                votos, preg.correcta, self.encuesta.puntaje_base)
            for pid, pts in ganados.items():
                self.puntajes[pid] += pts
            self.ultimos_aciertos = aciertos[:3]
            self.cierra_en = None
            self.estado = RESULTADOS
        else:
            # En encuesta anónima no hay pantalla intermedia: sigue de largo.
            self._avanzar(instante, presentes)

    def siguiente(self, instante, presentes):
        if self.estado != RESULTADOS:
            raise ValueError("no se está mostrando el resultado de una pregunta")
        self._avanzar(instante, presentes)

    # ------------------------------------------------------------- internos
    def _abrir(self, idx, instante, presentes):
        self.idx = idx
        preg = self.pregunta_actual()
        self.cierra_en = instante + self.encuesta.duracion_de(preg)
        self.esperados = presentes
        self.votos.setdefault(preg.orden, {})
        self._seq_vistos.clear()            # ver la nota del constructor
        self.estado = PREGUNTA_ABIERTA

    def _avanzar(self, instante, presentes):
        if self.idx + 1 < self.total_preguntas:
            self._abrir(self.idx + 1, instante, presentes)
        else:
            self.cierra_en = None
            self.estado = RESUMEN

    def _resultado_de(self, preg, votos):
        conteo = {chr(ord("A") + i): 0 for i in range(len(preg.opciones))}
        for v in votos:
            conteo[v.opcion] = conteo.get(v.opcion, 0) + 1
        correctas = sum(1 for v in votos
                        if preg.correcta and v.opcion == preg.correcta)
        return ResultadoPregunta(
            orden=preg.orden,
            enunciado=preg.enunciado,
            opciones=preg.opciones,
            correcta=preg.correcta,
            conteo=conteo,
            esperados=self.esperados,
            respondieron=len(votos),
            correctas=correctas,
        )

    # ------------------------------------------------------------ proyección
    def leaderboard(self, numero_de):
        """`numero_de` traduce id de pulsador a su número en pantalla."""
        filas = []
        for pid, pts in sorted(self.puntajes.items(), key=lambda kv: -kv[1]):
            numero = numero_de(pid)
            if numero is not None:
                filas.append({"numero": numero, "puntaje": pts})
        return filas

    def resumen(self, numero_de):
        preguntas = self.resultados
        participantes = max([p.esperados for p in preguntas] or [0])

        puntuables = [p for p in preguntas if p.correcta]
        mas_dificil = min(puntuables, key=lambda p: p.porcentaje_acierto) \
            if puntuables else None
        mas_facil = max(puntuables, key=lambda p: p.porcentaje_acierto) \
            if puntuables else None

        podio = []
        if self.encuesta.competitiva:
            mejores = sorted(self.puntajes.items(), key=lambda kv: -kv[1])[:3]
            podio = [(numero_de(pid), pts) for pid, pts in mejores
                     if numero_de(pid) is not None]

        return {
            "encuesta_id": self.encuesta.id,
            "nombre_encuesta": self.encuesta.nombre,
            "modalidad": self.encuesta.modalidad,
            "participantes": participantes,
            "preguntas": [p.como_dict() for p in preguntas],
            "podio": podio,
            "mas_dificil": mas_dificil.orden if mas_dificil else None,
            "mas_facil": mas_facil.orden if mas_facil else None,
        }
