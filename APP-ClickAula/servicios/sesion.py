"""Orquestador de la sesión de aula.

Es la única pieza que junta las tres cosas que el dominio deliberadamente no
tiene: el reloj, el candado y los repositorios. El dominio decide *qué* pasa;
este servicio decide *cuándo* se le pregunta y *a quién* se le avisa.

Responsabilidades:

* traducir los mensajes crudos de los pulsadores en comandos de dominio;
* sostener el hilo reloj que cierra las preguntas al vencer el tiempo, sin
  depender de que haya una pestaña abierta;
* serializar todo con un candado reentrante, porque entran en paralelo el hilo
  de MQTT, el del reloj y los de las peticiones web;
* armar el snapshot que se empuja a los navegadores.

El reloj entra por constructor (`reloj=`) para que los tests puedan correr una
partida entera sin esperar un solo segundo.
"""
import threading

from dominio.modelo import (MODALIDAD_COMPETENCIA, PREGUNTA_ABIERTA,
                            RESULTADOS, RESUMEN, SIN_PARTIDA)
from dominio.partida import Partida
from dominio.pulsadores import RegistroPulsadores


class ServicioSesion:
    def __init__(self, encuestas, pulsadores, historial, notificador,
                 reloj, tick_s=0.2, timeout_presencia_s=15.0):
        self._encuestas = encuestas
        self._pulsadores = pulsadores
        self._historial = historial
        self._notificador = notificador
        self._reloj = reloj
        self._tick_s = tick_s

        self._lock = threading.RLock()
        self.partida = None
        self.registro = RegistroPulsadores(timeout_presencia_s)

        self._parar = threading.Event()
        self._hilo = None

    # ------------------------------------------------------------ hilo reloj
    def arrancar(self):
        if self._hilo is not None:
            return
        self._hilo = threading.Thread(target=self._loop, daemon=True, name="reloj")
        self._hilo.start()

    def detener(self):
        self._parar.set()

    def _loop(self):
        while not self._parar.wait(self._tick_s):
            try:
                self.tic()
            except Exception as e:      # el reloj nunca debe morir
                print("[reloj] error:", e, flush=True)

    def tic(self, instante=None):
        """Un paso del reloj. Público para que los tests lo invoquen a mano."""
        instante = self._reloj() if instante is None else instante
        cambio = False
        with self._lock:
            if self.partida is not None and self.partida.vencio(instante):
                self.partida.cerrar(instante, self.registro.en_linea())
                cambio = True
            if self.registro.marcar_caidos(instante):
                cambio = True
        if cambio:
            self._emitir()

    # -------------------------------------------------------------- presencia
    def visto(self, pulsador_id, online=True, retenido=False):
        """Latido o mensaje cualquiera de un pulsador."""
        instante = self._reloj()
        aviso = False
        with self._lock:
            if not self.registro.conoce(pulsador_id):
                # El número lo asigna la persistencia, no el dominio.
                numero = self._pulsadores.numero_de(pulsador_id)
                self.registro.alta(pulsador_id, numero, instante,
                                   online=online, retenido=retenido)
                aviso = True
            else:
                aviso = self.registro.visto(pulsador_id, instante,
                                            online=online, retenido=retenido)
        if aviso:
            self._emitir()

    # ------------------------------------------------------------------ votos
    def votar(self, pulsador_id, opcion, seq=None):
        """Procesa un voto crudo. Devuelve el motivo del descarte, o None."""
        self.visto(pulsador_id)
        with self._lock:
            if self.partida is None:
                return "fuera_de_ventana"
            motivo = self.partida.registrar_voto(
                pulsador_id, opcion, seq, self._reloj())
        if motivo:
            return motivo
        self._emitir()
        return None

    # --------------------------------------------------------------- comandos
    def iniciar(self, encuesta_id):
        enc = self._encuestas.obtener(encuesta_id)
        if enc is None or not enc.preguntas:
            raise ValueError("la encuesta no existe o no tiene preguntas")
        with self._lock:
            self.partida = Partida(enc)
        self._emitir()

    def comenzar(self):
        with self._lock:
            if self.partida is None:
                raise ValueError("no hay una partida en la sala de espera")
            self.partida.comenzar(self._reloj(), self.registro.en_linea())
        self._emitir()

    def cerrar_ahora(self):
        with self._lock:
            if self.partida is None:
                raise ValueError("no hay una pregunta abierta")
            self.partida.cerrar(self._reloj(), self.registro.en_linea())
        self._emitir()

    def siguiente(self):
        with self._lock:
            if self.partida is None:
                raise ValueError("no se está mostrando el resultado de una pregunta")
            self.partida.siguiente(self._reloj(), self.registro.en_linea())
        self._emitir()

    def finalizar(self):
        """Archiva la ejecución y deja el servicio libre para otra encuesta."""
        with self._lock:
            if self.partida is None or self.partida.estado != RESUMEN:
                raise ValueError("la partida todavía no terminó")
            resumen = self.partida.resumen(self.registro.numero_de)
            ej_id = self._historial.guardar(resumen)
            self.partida = None
        self._emitir()
        return ej_id

    def abortar(self):
        with self._lock:
            self.partida = None
        self._emitir()

    # --------------------------------------------------------------- snapshot
    def snapshot(self, espia=False):
        """Estado completo para los navegadores.

        La forma de este diccionario es un contrato con el frontend: las
        claves y los tipos no se cambian sin tocar los `.js` de `app/static/`.
        """
        with self._lock:
            instante = self._reloj()
            p = self.partida

            if p is None:
                return self._snapshot_vacio()

            enc = p.encuesta
            preg = p.pregunta_actual()
            caja = p.votos_de_actual()
            competitivo = enc.modalidad == MODALIDAD_COMPETENCIA

            datos_preg = None
            if preg is not None:
                revelar = p.estado in (RESULTADOS, RESUMEN) or espia
                datos_preg = {
                    "orden": preg.orden,
                    "total": p.total_preguntas,
                    "enunciado": preg.enunciado,
                    "opciones": preg.opciones,
                    "correcta": preg.correcta if revelar else None,
                    "segundos": enc.duracion_de(preg),
                }

            ultimo = p.resultados[-1] if p.resultados else None
            mostrar_conteo = ultimo is not None and p.estado in (RESULTADOS, RESUMEN)

            return {
                "estado": p.estado,
                "encuesta": {
                    "id": enc.id,
                    "nombre": enc.nombre,
                    "modalidad": enc.modalidad,
                    "puntaje_base": enc.puntaje_base,
                },
                "competitivo": competitivo,
                "pregunta": datos_preg,
                "restante_ms": p.restante_ms(instante),
                "esperados": p.esperados,
                "recibidos": len(caja),
                "pulsadores": self._listado_pulsadores(caja),
                "conteo": ultimo.conteo if mostrar_conteo else None,
                "top_pregunta": self._top_pregunta(p),
                "leaderboard": p.leaderboard(self.registro.numero_de) if competitivo else [],
                "resumen": (p.resumen(self.registro.numero_de)
                            if p.estado == RESUMEN else None),
            }

    def _snapshot_vacio(self):
        return {
            "estado": SIN_PARTIDA,
            "encuesta": None,
            "competitivo": False,
            "pregunta": None,
            "restante_ms": None,
            "esperados": 0,
            "recibidos": 0,
            "pulsadores": self._listado_pulsadores({}),
            "conteo": None,
            "top_pregunta": [],
            "leaderboard": [],
            "resumen": None,
        }

    def _listado_pulsadores(self, caja):
        return [{"id": x.id, "numero": x.numero, "online": x.online,
                 "voto": x.id in caja}
                for x in self.registro.listado()]

    def _top_pregunta(self, p):
        if p.estado != RESULTADOS:
            return []
        filas = []
        for a in p.ultimos_aciertos:
            numero = self.registro.numero_de(a.pulsador)
            if numero is not None:
                filas.append({"numero": numero, "puntos": a.puntos,
                              "posicion": a.posicion})
        return filas

    # ---------------------------------------------------------------- interno
    def _emitir(self):
        self._notificador.publicar(self.snapshot())


# Estados reexportados para que quien use el servicio no tenga que importar
# el dominio sólo para comparar un string.
__all__ = ["ServicioSesion", "SIN_PARTIDA", "PREGUNTA_ABIERTA",
           "RESULTADOS", "RESUMEN"]
