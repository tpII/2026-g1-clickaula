/* Editor de encuestas: alta y edición de preguntas con sus opciones. */
let preguntas = [];

function nueva() {
  return { enunciado: "", opciones: ["", "", "", ""], correcta: null, segundos: null };
}

function esAnonima() { return $("modalidad").value === "anonima"; }

function pintar() {
  const cont = $("preguntas");
  if (!preguntas.length) {
    cont.innerHTML = '<div class="vacio">Agregá la primera pregunta.</div>';
    return;
  }
  cont.innerHTML = preguntas.map((p, i) => `
    <div class="pregunta-edit" data-i="${i}">
      <div class="cabecera">
        <span class="n">${i + 1}.</span>
        <input type="text" data-campo="enunciado" placeholder="Escribí la pregunta"
               value="${esc(p.enunciado)}" maxlength="300">
        <button data-accion="subir" ${i === 0 ? "disabled" : ""} title="Subir">↑</button>
        <button data-accion="bajar" ${i === preguntas.length - 1 ? "disabled" : ""} title="Bajar">↓</button>
        <button data-accion="duplicar" title="Duplicar">⧉</button>
        <button data-accion="borrar" class="peligro" title="Borrar">✕</button>
      </div>
      ${p.opciones.map((o, j) => `
        <div class="opcion-edit">
          <span class="marca marca-${LETRAS[j].toLowerCase()}">${LETRAS[j]}</span>
          <input type="text" data-campo="opcion" data-j="${j}" maxlength="160"
                 placeholder="${j < 2 ? "Opción obligatoria" : "Opción (podés dejarla vacía)"}"
                 value="${esc(o)}">
          <label class="correcta ${esAnonima() ? "oculto" : ""}">
            <input type="radio" name="correcta-${i}" data-campo="correcta" data-j="${j}"
                   ${p.correcta === LETRAS[j] ? "checked" : ""}> correcta
          </label>
        </div>`).join("")}
      <div class="campos" style="margin-top:8px">
        <div style="max-width:220px">
          <label>Segundos (vacío = el de la encuesta)</label>
          <input type="number" data-campo="segundos" min="5" max="300"
                 value="${p.segundos == null ? "" : p.segundos}">
        </div>
        <div style="display:flex;align-items:flex-end">
          <button data-accion="sin-correcta" class="${esAnonima() ? "oculto" : ""}">
            Sin respuesta correcta</button>
        </div>
      </div>
    </div>`).join("");
}

$("preguntas").addEventListener("input", (ev) => {
  const caja = ev.target.closest(".pregunta-edit");
  if (!caja) return;
  const i = Number(caja.dataset.i);
  const campo = ev.target.dataset.campo;
  if (campo === "enunciado") preguntas[i].enunciado = ev.target.value;
  else if (campo === "opcion") preguntas[i].opciones[Number(ev.target.dataset.j)] = ev.target.value;
  else if (campo === "segundos") preguntas[i].segundos = ev.target.value ? Number(ev.target.value) : null;
  else if (campo === "correcta") preguntas[i].correcta = LETRAS[Number(ev.target.dataset.j)];
});

$("preguntas").addEventListener("click", (ev) => {
  const b = ev.target.closest("button[data-accion]");
  if (!b) return;
  const i = Number(b.closest(".pregunta-edit").dataset.i);
  const a = b.dataset.accion;
  if (a === "borrar") preguntas.splice(i, 1);
  else if (a === "duplicar") preguntas.splice(i + 1, 0, JSON.parse(JSON.stringify(preguntas[i])));
  else if (a === "subir") [preguntas[i - 1], preguntas[i]] = [preguntas[i], preguntas[i - 1]];
  else if (a === "bajar") [preguntas[i + 1], preguntas[i]] = [preguntas[i], preguntas[i + 1]];
  else if (a === "sin-correcta") preguntas[i].correcta = null;
  pintar();
});

$("agregar").addEventListener("click", () => { preguntas.push(nueva()); pintar(); });

$("modalidad").addEventListener("change", () => {
  const anon = esAnonima();
  $("campo-puntaje").classList.toggle("oculto", anon);
  $("nota-anonima").classList.toggle("oculto", !anon);
  if (anon) preguntas.forEach((p) => { p.correcta = null; });
  pintar();
});

function aviso(msg) {
  const a = $("aviso");
  a.textContent = msg;
  a.classList.toggle("oculto", !msg);
  if (msg) window.scrollTo({ top: 0, behavior: "smooth" });
}

$("guardar").addEventListener("click", async () => {
  aviso("");
  const cuerpo = {
    nombre: $("nombre").value,
    modalidad: $("modalidad").value,
    segundos: Number($("segundos").value),
    puntaje_base: Number($("puntaje").value),
    preguntas: preguntas.map((p) => ({
      enunciado: p.enunciado,
      opciones: p.opciones.filter((o) => o.trim()),
      correcta: p.correcta,
      segundos: p.segundos,
    })),
  };
  try {
    if (window.ENCUESTA_ID) await api("/api/encuestas/" + window.ENCUESTA_ID, "PUT", cuerpo);
    else await api("/api/encuestas", "POST", cuerpo);
    location.href = "/";
  } catch (e) { aviso(e.message); }
});

/* --- arranque --- */
preguntas = (window.PREGUNTAS_INICIALES || []).map((p) => {
  const ops = p.opciones.slice();
  while (ops.length < 4) ops.push("");
  return { enunciado: p.enunciado, opciones: ops, correcta: p.correcta, segundos: p.segundos };
});
if (!preguntas.length) preguntas.push(nueva());
$("modalidad").dispatchEvent(new Event("change"));
escucharEstado(pintarEncabezado);
