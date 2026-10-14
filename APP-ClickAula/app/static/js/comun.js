/* Utilidades compartidas: conexión SSE, llamadas a la API y piezas de UI
   que usan tanto el panel como la vista de proyección. */

const LETRAS = ["A", "B", "C", "D"];
const SIMBOLOS = { A: "▲", B: "◆", C: "●", D: "■" };

function $(id) { return document.getElementById(id); }

function mostrar(id, visible) {
  const el = $(id);
  if (el) el.classList.toggle("oculto", !visible);
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  return d.innerHTML;
}

function nn(n) { return String(n).padStart(2, "0"); }

async function api(url, metodo = "GET", cuerpo = null) {
  const opciones = { method: metodo, headers: { "Content-Type": "application/json" } };
  if (cuerpo) opciones.body = JSON.stringify(cuerpo);
  const r = await fetch(url, opciones);
  let datos = null;
  try { datos = await r.json(); } catch (e) { /* respuesta sin cuerpo */ }
  if (!r.ok) throw new Error((datos && datos.error) || `Error ${r.status}`);
  return datos;
}

/* ------------------------------------------------------------------ SSE */
/* El servidor empuja el estado completo en cada cambio. Si se corta la
   conexión, EventSource reintenta solo; igual forzamos una recarga del
   estado al volver para no quedar con datos viejos. */
function escucharEstado(alRecibir) {
  let fuente = null;

  function conectar() {
    fuente = new EventSource("/api/stream");
    fuente.onmessage = (ev) => {
      try { alRecibir(JSON.parse(ev.data)); } catch (e) { console.error(e); }
    };
    fuente.onerror = () => {
      marcarConexion(false);
      fuente.close();
      setTimeout(conectar, 1500);
    };
    fuente.onopen = () => marcarConexion(true);
  }

  conectar();
  return () => fuente && fuente.close();
}

function marcarConexion(ok) {
  const el = $("estado-mqtt");
  if (el && !ok) { el.textContent = "sin conexión"; el.className = "chip caido"; }
}

function pintarEncabezado(s) {
  const m = $("estado-mqtt");
  if (m) {
    const ok = s.mqtt ? s.mqtt.conectado : true;
    m.textContent = ok ? "broker conectado" : "broker caído";
    m.className = "chip " + (ok ? "vivo" : "caido");
  }
  const p = $("estado-pulsadores");
  if (p) {
    const enLinea = (s.pulsadores || []).filter((x) => x.online).length;
    p.textContent = `${enLinea} pulsador${enLinea === 1 ? "" : "es"} en línea`;
    p.className = "chip " + (enLinea ? "vivo" : "");
  }
}

/* ----------------------------------------------------- piezas reusables */
function grillaPulsadores(pulsadores, marcarVoto) {
  if (!pulsadores || !pulsadores.length) {
    return '<div class="vacio">Ningún pulsador detectado todavía.</div>';
  }
  return pulsadores.map((p) => {
    const clases = ["pulsador"];
    if (!p.online) clases.push("caido");
    if (marcarVoto && p.voto) clases.push("voto");
    return `<div class="${clases.join(" ")}">
      <div class="num">${nn(p.numero)}</div>
      <div class="est">${p.voto && marcarVoto ? "votó" : (p.online ? "en línea" : "caído")}</div>
    </div>`;
  }).join("");
}

/* Barras de distribución. `conteo` puede ser null mientras la pregunta está
   abierta: en ese caso se dibujan las opciones sin números. */
function barrasOpciones(opciones, conteo, correcta, total) {
  const base = total || Object.values(conteo || {}).reduce((a, b) => a + b, 0) || 0;
  return opciones.map((texto, i) => {
    const letra = LETRAS[i];
    const cant = conteo ? (conteo[letra] || 0) : 0;
    const pct = base ? (cant / base) * 100 : 0;
    const ok = correcta === letra;
    return `<div class="barra-op ${ok ? "es-correcta" : ""}">
      <span class="marca marca-${letra.toLowerCase()}">${letra}</span>
      <span class="pista">
        <span class="relleno relleno-${letra.toLowerCase()}" style="width:${pct}%"></span>
        <span class="txt">${esc(texto)}${ok ? " <strong>· correcta</strong>" : ""}</span>
      </span>
      <span class="cant">${conteo ? cant : ""}</span>
    </div>`;
  }).join("");
}

function tablaPosiciones(leaderboard) {
  if (!leaderboard || !leaderboard.length) {
    return '<div class="vacio">Todavía nadie sumó puntos.</div>';
  }
  return `<table><thead><tr><th>#</th><th>Pulsador</th><th class="num">Puntos</th></tr></thead>
    <tbody>${leaderboard.map((f, i) => `<tr>
      <td>${i + 1}</td><td>Pulsador ${nn(f.numero)}</td>
      <td class="num">${f.puntaje}</td></tr>`).join("")}</tbody></table>`;
}

function podioHTML(podio) {
  if (!podio || !podio.length) return "";
  const medallas = ["🥇", "🥈", "🥉"];
  const orden = [1, 0, 2]; // 2.º, 1.º, 3.º para que el ganador quede al centro
  return orden.filter((i) => podio[i]).map((i) => {
    const [numero, pts] = podio[i];
    return `<div class="puesto p${i + 1}"><div class="caja">
      <div class="medalla">${medallas[i]}</div>
      <div class="quien">Pulsador ${nn(numero)}</div>
      <div class="pts">${pts} pts</div></div></div>`;
  }).join("");
}

/* Cuenta regresiva local: el servidor manda los milisegundos restantes en
   cada snapshot y el navegador sólo interpola. La autoridad sigue siendo el
   servidor, que cierra la pregunta aunque no haya ninguna pestaña abierta. */
function crearReloj(elemento) {
  let finEn = null;
  let timer = null;
  let vacio = false;

  function pintar() {
    if (finEn === null) { elemento.textContent = vacio ? "" : "—"; return; }
    const restante = Math.max(0, finEn - Date.now());
    const seg = Math.ceil(restante / 1000);
    elemento.textContent = seg;
    elemento.classList.toggle("poco", seg <= 5);
  }

  return {
    sincronizar(restanteMs) {
      vacio = false;
      finEn = restanteMs === null || restanteMs === undefined ? null : Date.now() + restanteMs;
      pintar();
      if (!timer) timer = setInterval(pintar, 200);
    },
    /* detener() deja un guión; limpiar() no deja nada y apaga el intervalo,
       que es lo que quiere la proyección al salir de una pregunta. */
    detener(dejarVacio) {
      vacio = !!dejarVacio;
      finEn = null;
      if (vacio && timer) { clearInterval(timer); timer = null; }
      pintar();
    },
  };
}
