/* Vista de proyección: sólo muestra, no controla nada. */
const relojProy = crearReloj($("px-reloj"));

/* Entre pregunta y pregunta, en modo competencia, alternamos el resultado de
   la pregunta con la tabla de posiciones para que se vea el avance. */
let alternador = null;

function ocultarTodo() {
  ["px-espera", "px-pregunta", "px-resultados", "px-leaderboard", "px-final"]
    .forEach((id) => mostrar(id, false));
}

function pararAlternador() {
  if (alternador) { clearInterval(alternador); alternador = null; }
}

function pintar(s) {
  ocultarTodo();
  pararAlternador();

  $("px-encuesta").textContent = s.encuesta ? s.encuesta.nombre : "ClickAula";
  $("px-progreso").textContent = s.pregunta ? `${s.pregunta.orden} / ${s.pregunta.total}` : "";
  $("px-votos").textContent = s.estado === "PREGUNTA_ABIERTA"
    ? `${s.recibidos} / ${s.esperados}` : "";

  const enJuego = s.estado === "PREGUNTA_ABIERTA";
  if (enJuego) relojProy.sincronizar(s.restante_ms); else relojProy.detener(true);

  /* La grilla de pulsadores acompaña salvo en el cierre final. */
  const conGrilla = ["LOBBY", "PREGUNTA_ABIERTA"].includes(s.estado);
  $("px-grilla").classList.toggle("oculto", !conGrilla);
  if (conGrilla) $("px-grilla").innerHTML = grillaPulsadores(s.pulsadores, enJuego);

  if (s.estado === "SIN_PARTIDA" || s.estado === "LOBBY") {
    mostrar("px-espera", true);
    $("px-grilla-espera").innerHTML = "";
    return;
  }

  if (enJuego) {
    mostrar("px-pregunta", true);
    $("px-enunciado").textContent = s.pregunta.enunciado;
    $("px-opciones").innerHTML = s.pregunta.opciones.map((t, i) => {
      const l = LETRAS[i];
      return `<div class="op-proy op-${l.toLowerCase()}">
        <span class="simbolo">${SIMBOLOS[l]}</span><span>${esc(t)}</span></div>`;
    }).join("");
    return;
  }

  if (s.estado === "RESULTADOS") {
    const mostrarBarras = () => {
      ocultarTodo();
      mostrar("px-resultados", true);
      $("px-r-enunciado").textContent = s.pregunta.enunciado;
      $("px-r-barras").innerHTML =
        barrasOpciones(s.pregunta.opciones, s.conteo, s.pregunta.correcta, s.recibidos);
    };
    const mostrarTabla = () => {
      ocultarTodo();
      mostrar("px-leaderboard", true);
      $("px-lb-cuerpo").innerHTML = s.leaderboard.slice(0, 8).map((f, i) =>
        `<tr><td>${i + 1}</td><td>Pulsador ${nn(f.numero)}</td>
         <td class="num">${f.puntaje}</td></tr>`).join("");
    };
    mostrarBarras();
    if (s.leaderboard.length) {
      let enBarras = true;
      alternador = setInterval(() => {
        enBarras = !enBarras;
        enBarras ? mostrarBarras() : mostrarTabla();
      }, 6000);
    }
    return;
  }

  if (s.estado === "RESUMEN") {
    mostrar("px-final", true);
    const r = s.resumen;
    $("px-final-titulo").textContent = s.competitivo ? "¡Terminamos!" : "Gracias por participar";
    $("px-podio").innerHTML = s.competitivo ? podioHTML(r.podio) : "";
    const busca = (o) => r.preguntas.find((p) => p.orden === o);
    const pct = (p) => (p.respondieron ? Math.round(p.correctas / p.respondieron * 100) : 0);
    $("px-extremos").innerHTML = r.mas_facil
      ? `Más fácil: ${esc(busca(r.mas_facil).enunciado)} (${pct(busca(r.mas_facil))}%)<br>
         Más difícil: ${esc(busca(r.mas_dificil).enunciado)} (${pct(busca(r.mas_dificil))}%)`
      : `${r.participantes} participantes · ${r.preguntas.length} preguntas`;
  }
}

escucharEstado(pintar);
