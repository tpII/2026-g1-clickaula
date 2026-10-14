"""Servidor web: vistas del coordinador, vista de proyección y API."""
import json
import queue

from flask import (Flask, Response, jsonify, redirect, render_template,
                   request, url_for)

from . import bus, config, db, exportar, mqtt_client
from .composicion import sesion

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False


# ============================================================ vistas (HTML)
@app.get("/")
def biblioteca():
    return render_template("biblioteca.html", encuestas=db.listar_encuestas())


@app.get("/encuestas/nueva")
def encuesta_nueva():
    return render_template("editor.html", encuesta=None,
                           puntaje_base=config.PUNTAJE_BASE_DEFECTO,
                           segundos=config.SEGUNDOS_DEFECTO)


@app.get("/encuestas/<int:enc_id>/editar")
def encuesta_editar(enc_id):
    enc = db.obtener_encuesta(enc_id)
    if not enc:
        return redirect(url_for("biblioteca"))
    return render_template("editor.html", encuesta=enc,
                           puntaje_base=enc["puntaje_base"], segundos=enc["segundos"])


@app.get("/partida")
def partida():
    return render_template("partida.html")


@app.get("/proyeccion")
def proyeccion():
    return render_template("proyeccion.html")


@app.get("/historial")
def historial():
    return render_template("historial.html", ejecuciones=db.listar_ejecuciones())


@app.get("/historial/<int:ej_id>")
def historial_detalle(ej_id):
    ej = db.obtener_ejecucion(ej_id)
    if not ej:
        return redirect(url_for("historial"))
    return render_template("historial_detalle.html", ej=ej,
                           hay_podio=bool(exportar.filas_podio(ej)))


# =========================================================== descargas CSV
def _descarga_csv(texto, nombre):
    return Response(
        texto.encode("utf-8"),
        # Sólo el tipo: Flask le agrega el juego de caracteres. Pasarlo acá
        # también lo duplica en la cabecera.
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@app.get("/historial/<int:ej_id>/preguntas.csv")
def historial_csv_preguntas(ej_id):
    ej = db.obtener_ejecucion(ej_id)
    if not ej:
        return redirect(url_for("historial"))
    return _descarga_csv(exportar.csv_preguntas(ej),
                         exportar.nombre_archivo(ej, "preguntas"))


@app.get("/historial/<int:ej_id>/podio.csv")
def historial_csv_podio(ej_id):
    ej = db.obtener_ejecucion(ej_id)
    if not ej:
        return redirect(url_for("historial"))
    if not exportar.filas_podio(ej):
        # Encuesta anónima: no hay puntaje que exportar.
        return redirect(url_for("historial_detalle", ej_id=ej_id))
    return _descarga_csv(exportar.csv_podio(ej),
                         exportar.nombre_archivo(ej, "podio"))


# ==================================================================== API
def _validar_encuesta(d):
    nombre = (d.get("nombre") or "").strip()
    if not nombre:
        return "El nombre de la encuesta es obligatorio."

    modalidad = d.get("modalidad")
    if modalidad not in (config.MODALIDAD_COMPETENCIA, config.MODALIDAD_ANONIMA):
        return "Modalidad inválida."

    preguntas = d.get("preguntas") or []
    if not preguntas:
        return "La encuesta necesita al menos una pregunta."

    for i, p in enumerate(preguntas, start=1):
        if not (p.get("enunciado") or "").strip():
            return f"La pregunta {i} no tiene enunciado."
        ops = [o for o in (p.get("opciones") or []) if (o or "").strip()]
        if len(ops) < 2:
            return f"La pregunta {i} necesita al menos dos opciones."
        if len(ops) > 4:
            return f"La pregunta {i} tiene más de cuatro opciones."
        c = p.get("correcta")
        if c and c not in config.OPCIONES[: len(ops)]:
            return f"La respuesta correcta de la pregunta {i} no es una de sus opciones."
    return None


def _normalizar(d):
    modalidad = d["modalidad"]
    preguntas = []
    for p in d["preguntas"]:
        ops = [o.strip() for o in p["opciones"] if (o or "").strip()]
        preguntas.append({
            "enunciado": p["enunciado"].strip(),
            "opciones": ops,
            # En encuesta anónima nunca hay respuesta correcta.
            "correcta": None if modalidad == config.MODALIDAD_ANONIMA else (p.get("correcta") or None),
            "segundos": int(p["segundos"]) if p.get("segundos") else None,
        })
    return {
        "nombre": d["nombre"].strip(),
        "modalidad": modalidad,
        "puntaje_base": int(d.get("puntaje_base") or config.PUNTAJE_BASE_DEFECTO),
        "segundos": int(d.get("segundos") or config.SEGUNDOS_DEFECTO),
        "preguntas": preguntas,
    }


@app.get("/api/encuestas")
def api_listar():
    return jsonify(db.listar_encuestas())


@app.get("/api/encuestas/<int:enc_id>")
def api_obtener(enc_id):
    enc = db.obtener_encuesta(enc_id)
    return (jsonify(enc), 200) if enc else (jsonify({"error": "no existe"}), 404)


@app.post("/api/encuestas")
def api_crear():
    d = request.get_json(force=True)
    err = _validar_encuesta(d)
    if err:
        return jsonify({"error": err}), 400
    return jsonify({"id": db.guardar_encuesta(_normalizar(d))}), 201


@app.put("/api/encuestas/<int:enc_id>")
def api_actualizar(enc_id):
    d = request.get_json(force=True)
    err = _validar_encuesta(d)
    if err:
        return jsonify({"error": err}), 400
    return jsonify({"id": db.guardar_encuesta(_normalizar(d), enc_id)})


@app.delete("/api/encuestas/<int:enc_id>")
def api_borrar(enc_id):
    db.borrar_encuesta(enc_id)
    return jsonify({"ok": True})


def _comando(fn, *a):
    try:
        r = fn(*a)
        return jsonify({"ok": True, "resultado": r})
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@app.post("/api/partida/iniciar")
def api_iniciar():
    return _comando(sesion.iniciar, int(request.get_json(force=True)["encuesta_id"]))


@app.post("/api/partida/comenzar")
def api_comenzar():
    return _comando(sesion.comenzar)


@app.post("/api/partida/cerrar")
def api_cerrar():
    return _comando(sesion.cerrar_ahora)


@app.post("/api/partida/siguiente")
def api_siguiente():
    return _comando(sesion.siguiente)


@app.post("/api/partida/finalizar")
def api_finalizar():
    return _comando(sesion.finalizar)


@app.post("/api/partida/abortar")
def api_abortar():
    return _comando(sesion.abortar)


@app.get("/api/estado")
def api_estado():
    # ?espia=1 revela la respuesta correcta con la pregunta abierta. Sólo en
    # modo desarrollo, y sólo lo usa el simulador para poder acertar a propósito.
    espia = config.DEV and request.args.get("espia") == "1"
    snap = sesion.snapshot(espia=espia)
    snap["mqtt"] = mqtt_client.conectado()
    return jsonify(snap)


@app.get("/api/salud")
def api_salud():
    return jsonify({"ok": True, "mqtt": mqtt_client.conectado(),
                    "clientes_sse": bus.cantidad_clientes(), "dev": config.DEV})


@app.get("/api/stream")
def api_stream():
    """Server-Sent Events. Cada cambio de estado empuja el snapshot completo."""
    def gen():
        q = bus.suscribir()
        try:
            yield f"data: {json.dumps(sesion.snapshot(), ensure_ascii=False)}\n\n"
            while True:
                try:
                    dato = q.get(timeout=15)
                    yield f"data: {dato}\n\n"
                except queue.Empty:
                    yield ": ping\n\n"       # mantiene viva la conexión
        finally:
            bus.desuscribir(q)

    return Response(gen(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no",
                             "Connection": "keep-alive"})


@app.context_processor
def _inyectar():
    return {"COLOR_OPCION": config.COLOR_OPCION, "OPCIONES": config.OPCIONES}
