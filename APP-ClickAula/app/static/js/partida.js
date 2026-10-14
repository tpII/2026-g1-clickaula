/* Panel del coordinador durante la partida. */
const reloj = crearReloj($("p-reloj"));
let ultimo = null;

function seccion(estado) {
  mostrar("sin-partida", estado === "SIN_PARTIDA");
  mostrar("lobby", estado === "LOBBY");
  mostrar("jugando", estado === "PREGUNTA_ABIERTA");
  mostrar("resultados", estado === "RESULTADOS");
  mostrar("resumen", estado === "RESUMEN");
}

function pintar(s) {
  ultimo = s;
  pintarEncabezado(s);
  seccion(s.estado);

  if (s.estado === "LOBBY") {
    $("lobby-nombre").textContent = s.encuesta.nombre;
    $("lobby-detalle").textContent =
      (s.competitivo ? "Competencia por puntaje" : "Encuesta anónima") +
      ` · ${s.pregunta ? s.pregunta.total : ""} preguntas`;
    $("lobby-cant").textContent = s.pulsadores.filter((p) => p.online).length;
    $("lobby-grilla").innerHTML = grillaPulsadores(s.pulsadores, false);
    $("btn-comenzar").disabled = !s.pulsadores.some((p) => p.online);
  }

  if (s.estado === "PREGUNTA_ABIERTA") {
    const p = s.pregunta;
    $("p-orden").textContent = p.orden;
    $("p-total").textContent = p.total;
    $("p-enunciado").textContent = p.enunciado;
    $("p-votos").textContent = `${s.recibidos}/${s.esperados}`;
    $("p-opciones").innerHTML = barrasOpciones(p.opciones, null, null, 0);
    $("p-grilla").innerHTML = grillaPulsadores(s.pulsadores, true);
    reloj.sincronizar(s.restante_ms);
  } else {
    reloj.detener();
  }

  if (s.estado === "RESULTADOS") {
    const p = s.pregunta;
    $("r-orden").textContent = p.orden;
    $("r-enunciado").textContent = p.enunciado;
    $("r-barras").innerHTML = barrasOpciones(p.opciones, s.conteo, p.correcta, s.recibidos);
    $("r-top").innerHTML = s.top_pregunta.length
      ? `<table><thead><tr><th>#</th><th>Pulsador</th><th class="num">Ganó</th></tr></thead><tbody>` +
        s.top_pregunta.map((t) => `<tr><td>${t.posicion}</td>
          <td>Pulsador ${nn(t.numero)}</td><td class="num">+${t.puntos}</td></tr>`).join("") +
        "</tbody></table>"
      : '<div class="vacio">Nadie acertó esta pregunta.</div>';
    $("r-leaderboard").innerHTML = tablaPosiciones(s.leaderboard);
    $("btn-siguiente").textContent =
      p.orden >= p.total ? "Ver resultados finales →" : "Siguiente pregunta →";
  }

  if (s.estado === "RESUMEN") pintarResumen(s.resumen, s.competitivo);
}

function pintarResumen(r, competitivo) {
  if (!r) return;
  $("res-titulo").textContent = "Resultados · " + r.nombre_encuesta;
  $("res-sub").textContent =
    `${competitivo ? "Competencia" : "Encuesta anónima"} · ${r.participantes} participantes · ` +
    `${r.preguntas.length} preguntas`;

  mostrar("res-podio-caja", competitivo && r.podio.length > 0);
  if (competitivo) $("res-podio").innerHTML = podioHTML(r.podio);

  const busca = (orden) => r.preguntas.find((p) => p.orden === orden);
  const facil = r.mas_facil ? busca(r.mas_facil) : null;
  const dificil = r.mas_dificil ? busca(r.mas_dificil) : null;
  mostrar("res-extremos-caja", !!facil);
  if (facil) {
    const pct = (p) => (p.respondieron ? Math.round(p.correctas / p.respondieron * 100) : 0);
    $("res-extremos").innerHTML = `
      <div class="fila"><div class="crece"><div class="titulo">Más fácil</div>
        <div class="sutil">${facil.orden}. ${esc(facil.enunciado)}</div></div>
        <strong>${pct(facil)}% de aciertos</strong></div>
      <div class="fila"><div class="crece"><div class="titulo">Más difícil</div>
        <div class="sutil">${dificil.orden}. ${esc(dificil.enunciado)}</div></div>
        <strong>${pct(dificil)}% de aciertos</strong></div>`;
  }

  $("res-desglose").innerHTML = r.preguntas.map((p) => `
    <div style="padding:14px 0;border-bottom:1px solid var(--borde)">
      <div class="titulo">${p.orden}. ${esc(p.enunciado)}</div>
      <div class="sutil" style="margin-bottom:10px">
        ${p.respondieron} de ${p.esperados} respondieron${p.correcta
          ? ` · ${p.correctas} correctas (${p.respondieron
              ? Math.round(p.correctas / p.respondieron * 100) : 0}%)` : ""}</div>
      <div class="barras">${barrasOpciones(p.opciones, p.conteo, p.correcta, p.respondieron)}</div>
    </div>`).join("");
}

/* ------------------------------------------------------------- acciones */
async function comando(url, boton) {
  if (boton) boton.disabled = true;
  try { await api(url, "POST"); }
  catch (e) { alert(e.message); }
  finally { if (boton) boton.disabled = false; }
}

$("btn-comenzar").addEventListener("click", (e) => comando("/api/partida/comenzar", e.target));
$("btn-cerrar").addEventListener("click", (e) => comando("/api/partida/cerrar", e.target));
$("btn-siguiente").addEventListener("click", (e) => comando("/api/partida/siguiente", e.target));
$("btn-abortar").addEventListener("click", async () => {
  if (confirm("¿Cancelar la partida?")) { await comando("/api/partida/abortar"); location.href = "/"; }
});
$("btn-descartar").addEventListener("click", async () => {
  if (confirm("¿Descartar estos resultados sin guardarlos en el historial?")) {
    await comando("/api/partida/abortar"); location.href = "/";
  }
});
$("btn-guardar").addEventListener("click", async (e) => {
  e.target.disabled = true;
  try {
    const r = await api("/api/partida/finalizar", "POST");
    location.href = "/historial/" + r.resultado;
  } catch (err) { alert(err.message); e.target.disabled = false; }
});

escucharEstado(pintar);
