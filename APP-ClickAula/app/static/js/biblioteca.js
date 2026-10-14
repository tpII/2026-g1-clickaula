/* Biblioteca de encuestas: ejecutar y borrar. */
document.querySelectorAll("[data-ejecutar]").forEach((b) => {
  b.addEventListener("click", async () => {
    b.disabled = true;
    try {
      await api("/api/partida/iniciar", "POST", { encuesta_id: Number(b.dataset.ejecutar) });
      location.href = "/partida";
    } catch (e) {
      alert("No se pudo iniciar: " + e.message);
      b.disabled = false;
    }
  });
});

document.querySelectorAll("[data-borrar]").forEach((b) => {
  b.addEventListener("click", async () => {
    if (!confirm(`¿Borrar la encuesta «${b.dataset.nombre}»?\n\nLas ejecuciones ya guardadas en el historial se conservan.`)) return;
    try {
      await api("/api/encuestas/" + b.dataset.borrar, "DELETE");
      location.reload();
    } catch (e) { alert("No se pudo borrar: " + e.message); }
  });
});

/* Encabezado en vivo (broker y pulsadores conectados). */
escucharEstado(pintarEncabezado);
