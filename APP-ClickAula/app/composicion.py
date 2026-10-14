"""Armado de la aplicación: acá se eligen las implementaciones concretas.

Es el único lugar del programa donde se nombra a la vez un puerto y su
adaptador. El resto del código recibe el servicio ya armado y no sabe que
detrás hay SQLite ni Server-Sent Events.

En la fase 3 esto se convierte en la fábrica de la aplicación Flask; por ahora
es un módulo con una instancia, que es lo que el servidor y el cliente MQTT
necesitan compartir.
"""
import time

from servicios.sesion import ServicioSesion

from . import config, repositorios

sesion = ServicioSesion(
    encuestas=repositorios.RepoEncuestas(),
    pulsadores=repositorios.RepoPulsadores(),
    historial=repositorios.RepoHistorial(),
    notificador=repositorios.NotificadorSSE(),
    # El reloj monotónico no salta si alguien cambia la hora de la máquina.
    reloj=time.monotonic,
    tick_s=config.TICK_S,
    timeout_presencia_s=config.PRESENCIA_TIMEOUT_S,
)
