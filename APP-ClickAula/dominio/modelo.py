"""Modelo del dominio: los objetos con los que razona el sistema.

Sin dependencias de infraestructura (R1). Son estructuras de datos y
constantes; la lógica vive en `partida.py`, `puntaje.py` y `pulsadores.py`.
"""
from dataclasses import dataclass, field

# --- opciones -------------------------------------------------------------
OPCIONES = ["A", "B", "C", "D"]

# Color del botón físico correspondiente a cada opción.
COLOR_OPCION = {"A": "rojo", "B": "azul", "C": "amarillo", "D": "verde"}

# --- modalidades ----------------------------------------------------------
MODALIDAD_COMPETENCIA = "competencia"
MODALIDAD_ANONIMA = "anonima"

# --- estados de la partida ------------------------------------------------
SIN_PARTIDA = "SIN_PARTIDA"
LOBBY = "LOBBY"
PREGUNTA_ABIERTA = "PREGUNTA_ABIERTA"
RESULTADOS = "RESULTADOS"
RESUMEN = "RESUMEN"

# --- motivos por los que se descarta un voto ------------------------------
# Son parte del contrato con quien lee los registros: no cambiar los textos
# sin actualizar CLAUDE.md y contrato.md.
DUPLICADO = "duplicado"
FUERA_DE_VENTANA = "fuera_de_ventana"
OPCION_INVALIDA = "opcion_invalida"
YA_VOTO = "ya_voto"


@dataclass(frozen=True)
class Pregunta:
    orden: int
    enunciado: str
    opciones: list          # textos de 2 a 4 opciones
    correcta: str | None    # "A".."D", o None si no puntúa
    segundos: int | None    # None = usa el de la encuesta

    def admite(self, opcion):
        """¿Esta pregunta tiene esa opción?"""
        return opcion in OPCIONES[: len(self.opciones)]


@dataclass(frozen=True)
class Encuesta:
    id: int
    nombre: str
    modalidad: str
    puntaje_base: int
    segundos: int
    preguntas: list         # list[Pregunta], en orden

    @property
    def competitiva(self):
        return self.modalidad == MODALIDAD_COMPETENCIA

    def duracion_de(self, pregunta):
        return pregunta.segundos or self.segundos


@dataclass(frozen=True)
class Voto:
    pulsador: str
    opcion: str
    recibido_en: float      # instante monotónico que asigna el servicio


@dataclass
class Pulsador:
    id: str
    numero: int
    online: bool
    ultimo_latido: float


@dataclass
class ResultadoPregunta:
    """Lo que queda de una pregunta una vez cerrada. Solo agregados (R6)."""
    orden: int
    enunciado: str
    opciones: list
    correcta: str | None
    conteo: dict            # {"A": 3, "B": 1, ...}
    esperados: int
    respondieron: int
    correctas: int

    @property
    def porcentaje_acierto(self):
        if not self.respondieron:
            return 0.0
        return self.correctas / self.respondieron * 100

    def como_dict(self):
        return {
            "orden": self.orden,
            "enunciado": self.enunciado,
            "opciones": self.opciones,
            "correcta": self.correcta,
            "conteo": self.conteo,
            "esperados": self.esperados,
            "respondieron": self.respondieron,
            "correctas": self.correctas,
        }


@dataclass
class Acierto:
    """Una respuesta correcta, con su posición en el orden de llegada."""
    posicion: int
    pulsador: str
    puntos: int
