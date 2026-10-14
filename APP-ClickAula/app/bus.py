"""Bus de eventos hacia los navegadores, sobre Server-Sent Events.

Cada pestaña abierta (panel o proyección) tiene su propia cola. Publicamos
siempre el estado completo: con treinta pulsadores el snapshot es chico y así
evitamos toda una familia de errores de desincronización.
"""
import json
import queue
import threading

_clientes = set()
_lock = threading.Lock()


def suscribir():
    q = queue.Queue(maxsize=100)
    with _lock:
        _clientes.add(q)
    return q


def desuscribir(q):
    with _lock:
        _clientes.discard(q)


def publicar(snapshot):
    dato = json.dumps(snapshot, ensure_ascii=False)
    with _lock:
        muertos = []
        for q in _clientes:
            try:
                q.put_nowait(dato)
            except queue.Full:
                muertos.append(q)
        for q in muertos:
            _clientes.discard(q)


def cantidad_clientes():
    with _lock:
        return len(_clientes)
