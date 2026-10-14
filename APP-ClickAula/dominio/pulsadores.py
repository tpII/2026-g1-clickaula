"""Registro de los pulsadores conocidos y su presencia.

El tiempo entra siempre como parámetro (R2): este módulo nunca consulta el
reloj. Eso permite probar los vencimientos de presencia sin esperarlos.
"""
from .modelo import Pulsador

# Sin latido en esta ventana, el pulsador se da por caído.
TIMEOUT_PRESENCIA_S = 15.0


class RegistroPulsadores:
    def __init__(self, timeout_s=TIMEOUT_PRESENCIA_S):
        self._timeout = timeout_s
        self._pulsadores = {}

    # ------------------------------------------------------------ consultas
    def conoce(self, pulsador_id):
        return pulsador_id in self._pulsadores

    def numero_de(self, pulsador_id):
        p = self._pulsadores.get(pulsador_id)
        return p.numero if p else None

    def en_linea(self):
        return sum(1 for p in self._pulsadores.values() if p.online)

    def listado(self):
        """Ordenado por número, que es como se muestra en pantalla."""
        return sorted(self._pulsadores.values(), key=lambda p: p.numero)

    # --------------------------------------------------------------- altas
    def alta(self, pulsador_id, numero, instante, online=True, retenido=False):
        """Registra un pulsador nuevo. El número lo asigna la persistencia."""
        self._pulsadores[pulsador_id] = Pulsador(
            id=pulsador_id,
            numero=numero,
            online=online,
            ultimo_latido=self._latido(instante, retenido),
        )
        return True

    def visto(self, pulsador_id, instante, online=True, retenido=False):
        """Latido o señal de vida. Devuelve True si cambió el estado en línea.

        `retenido` marca los mensajes que el intermediario guardó de una
        sesión anterior: registran al pulsador pero no lo dan por vivo, así no
        aparecen como presentes equipos que ya no están en el aula.
        """
        p = self._pulsadores.get(pulsador_id)
        if p is None:
            return False
        cambio = p.online != online
        p.online = online
        latido = self._latido(instante, retenido)
        p.ultimo_latido = max(p.ultimo_latido, latido) if retenido else latido
        return cambio

    def _latido(self, instante, retenido):
        # Un mensaje retenido nace casi vencido: expira en el próximo tic
        # salvo que llegue un latido de verdad.
        return instante - self._timeout + 2 if retenido else instante

    # ------------------------------------------------------------ vencidos
    def marcar_caidos(self, instante):
        """Da por caídos los que no laten hace rato. True si cambió alguno."""
        cambio = False
        for p in self._pulsadores.values():
            if p.online and instante - p.ultimo_latido > self._timeout:
                p.online = False
                cambio = True
        return cambio
