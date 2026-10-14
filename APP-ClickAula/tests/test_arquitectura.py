"""Tests que custodian las reglas de CLAUDE.md.

No prueban comportamiento: prueban que la estructura siga siendo la acordada.
Son los que avisan cuando alguien, con la mejor intención, mete un `import
sqlite3` en el dominio para resolver algo rápido.
"""
import ast
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# R1: el dominio no conoce infraestructura. Lo único que puede importar es la
# biblioteca estándar de estructuras de datos, y a sí mismo.
PERMITIDO_EN_DOMINIO = {
    "collections", "dataclasses", "typing", "enum", "abc",
    "itertools", "functools", "math", "operator",
}

# Nadie del lado de las reglas puede importar esto.
PROHIBIDO_EN_SERVICIOS = {
    "flask", "sqlite3", "paho", "requests", "app", "werkzeug", "jinja2",
}


def _archivos(paquete):
    return sorted((RAIZ / paquete).glob("*.py"))


def _importes(archivo):
    """Devuelve (modulo_raiz, es_relativo) de cada import del archivo."""
    arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                yield alias.name.split(".")[0], False
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level:                      # from . import x
                yield (nodo.module or "").split(".")[0], True
            else:
                yield (nodo.module or "").split(".")[0], False


def test_r1_el_dominio_no_importa_infraestructura():
    for archivo in _archivos("dominio"):
        for modulo, relativo in _importes(archivo):
            if relativo:
                continue                        # import dentro del propio dominio
            assert modulo in PERMITIDO_EN_DOMINIO or modulo == "dominio", (
                f"{archivo.name} importa '{modulo}', que no es parte del dominio. "
                "Si hace falta algo de afuera, va por un puerto "
                "(dominio/puertos.py)."
            )


def test_r2_el_dominio_no_consulta_el_reloj():
    """El instante entra como parámetro. Sin esto no se puede probar nada rápido."""
    for archivo in _archivos("dominio"):
        texto = archivo.read_text(encoding="utf-8")
        for sospechoso in ("time.monotonic", "time.time", "datetime.now",
                           "import time", "import datetime"):
            assert sospechoso not in texto, (
                f"{archivo.name} usa '{sospechoso}': el tiempo tiene que entrar "
                "por parámetro (R2)."
            )


def test_los_servicios_no_conocen_flask_ni_la_base():
    for archivo in _archivos("servicios"):
        for modulo, _ in _importes(archivo):
            assert modulo not in PROHIBIDO_EN_SERVICIOS, (
                f"servicios/{archivo.name} importa '{modulo}'. Los servicios "
                "hablan con puertos, no con adaptadores."
            )


def test_el_dominio_se_puede_importar_sin_nada_instalado():
    """Ni Flask ni paho: el dominio tiene que cargar con Python pelado."""
    import importlib

    for nombre in ("modelo", "partida", "puntaje", "pulsadores", "puertos"):
        importlib.import_module(f"dominio.{nombre}")


def test_no_quedaron_restos_del_motor_viejo():
    """El motor monolítico se reemplazó por dominio + servicios."""
    assert not (RAIZ / "app" / "engine.py").exists()
    assert not (RAIZ / "app" / "scoring.py").exists()
