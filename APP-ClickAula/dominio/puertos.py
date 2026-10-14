"""Puertos: lo que el dominio necesita del mundo, descrito desde el dominio.

Son `Protocol`, no clases base: nadie los hereda. Quien quiera ser un
repositorio de encuestas sólo tiene que tener los métodos que acá se piden.
Eso permite que `servicios/` dependa de estas firmas y no de SQLite ni de
Flask, y que los tests pasen implementaciones en memoria de tres líneas.

Las implementaciones reales viven en `app/repositorios.py` (R1: acá no se
importa infraestructura).
"""
from typing import Protocol, runtime_checkable

from .modelo import Encuesta


@runtime_checkable
class RepositorioEncuestas(Protocol):
    def obtener(self, encuesta_id: int) -> Encuesta | None:
        """La encuesta armada como objeto de dominio, o None si no existe."""
        ...


@runtime_checkable
class RepositorioPulsadores(Protocol):
    def numero_de(self, pulsador_id: str) -> int:
        """Número estable del pulsador en pantalla; lo crea si es la primera vez.

        Es la persistencia la que asigna el número, no el dominio: tiene que
        sobrevivir a que se apague la aplicación.
        """
        ...


@runtime_checkable
class RepositorioHistorial(Protocol):
    def guardar(self, resumen: dict) -> int:
        """Archiva una ejecución terminada y devuelve su id."""
        ...


@runtime_checkable
class Notificador(Protocol):
    def publicar(self, snapshot: dict) -> None:
        """Empuja el estado completo a quien esté mirando.

        Nunca debe fallar hacia arriba: si un cliente se cayó, es problema del
        adaptador, no de la partida.
        """
        ...
