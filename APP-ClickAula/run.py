"""Punto de entrada: base de datos, cliente MQTT, reloj de la partida y web."""
import logging

from app import config, db, mqtt_client
from app.composicion import sesion
from app.server import app

# Rutas que el navegador consulta solas varias veces por segundo. Sin esto el
# registro se llena de 200 y 304 y tapa los mensajes que importan.
_RUIDOSAS = ("/api/estado", "/api/stream", "/api/salud", "/static/")


class _SinRuido(logging.Filter):
    def filter(self, registro):
        linea = registro.getMessage()
        if not any(r in linea for r in _RUIDOSAS):
            return True
        return not (" 200 " in linea or " 304 " in linea)


def main():
    logging.getLogger("werkzeug").addFilter(_SinRuido())
    db.init()
    sesion.arrancar()
    mqtt_client.arrancar()
    print(f"[web] http://localhost:{config.WEB_PORT}  (proyección en /proyeccion)",
          flush=True)
    # threaded=True es imprescindible: cada conexión SSE ocupa un hilo.
    app.run(host=config.WEB_HOST, port=config.WEB_PORT,
            threaded=True, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
