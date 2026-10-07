#!/usr/bin/env python3
"""Analiza el formato de una entrega en PDF (Taller de Proyecto II, UNLP).

Usa solo poppler (pdftohtml, pdftotext), sin dependencias de Python.
Imprime un informe en Markdown con lo que se puede verificar mecánicamente
(fuente, tamaño, interlineado, justificado, estructura, epígrafes, lenguaje)
y marca como "a revisar" lo que necesita criterio humano.

Uso:  analizar_pdf.py entrega.pdf [--json]
"""
import collections
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import unicodedata
import xml.etree.ElementTree as ET

ZOOM = 3  # pdftohtml redondea tamaños a entero y capea el zoom en 3: precisión ≈0,3 pt

FUENTES_OK = {"Arial", "Times New Roman", "Libertinus"}
TAM_OK = 12.0
TOL_TAM = 0.6


# ---------- utilidades ----------

def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def familia(nombre):
    n = re.sub(r"^[A-Z]{6}\+", "", nombre)  # prefijo de subset
    base = re.split(r"[-,]", n)[0]
    base = re.sub(r"(PSMT|PS|MT|Regular|Bold|Italic|BoldItalic|BoldMT|ItalicMT)+$", "", base)
    if re.search(r"timesnewroman|times", base, re.I):
        return "Times New Roman"
    if re.search(r"^arial", base, re.I):
        return "Arial"
    if re.search(r"liberationserif", base, re.I):
        return "Liberation Serif (equivalente a Times)"
    if re.search(r"liberationsans", base, re.I):
        return "Liberation Sans (equivalente a Arial)"
    if re.search(r"^libertinus", base, re.I):
        return "Libertinus"
    if re.search(r"^carlito", base, re.I):
        return "Carlito (equivalente a Calibri)"
    return base


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


# ---------- extracción ----------

def extraer(pdf):
    tmp = tempfile.mkdtemp(prefix="fmt_")
    out = os.path.join(tmp, "doc")
    subprocess.run(["pdftohtml", "-xml", "-zoom", str(ZOOM), "-q", pdf, out],
                   check=True, capture_output=True)
    root = ET.parse(out + ".xml").getroot()
    paginas = []
    fuentes = {}  # los fontspec se declaran una vez y se reutilizan en páginas posteriores
    for pg in root.findall("page"):
        for fs in pg.findall("fontspec"):
            fuentes[fs.get("id")] = {"size": int(fs.get("size")) / ZOOM,
                                     "familia": familia(fs.get("family"))}
        textos, imagenes = [], []
        for t in pg.findall("text"):
            txt = "".join(t.itertext())
            if not txt.strip():
                continue
            f = fuentes[t.get("font")]
            textos.append({
                "top": int(t.get("top")) / ZOOM, "left": int(t.get("left")) / ZOOM,
                "w": int(t.get("width")) / ZOOM, "h": int(t.get("height")) / ZOOM,
                "size": f["size"], "familia": f["familia"],
                "bold": t.find("b") is not None or t.find(".//b") is not None,
                "txt": txt,
            })
        for im in pg.findall("image"):
            imagenes.append({"top": int(im.get("top")) / ZOOM, "left": int(im.get("left")) / ZOOM,
                             "w": int(im.get("width")) / ZOOM, "h": int(im.get("height")) / ZOOM})
        paginas.append({"n": int(pg.get("number")), "alto": int(pg.get("height")) / ZOOM,
                        "ancho": int(pg.get("width")) / ZOOM, "textos": textos, "imagenes": imagenes})
    shutil.rmtree(tmp, ignore_errors=True)
    return paginas


def lineas(pagina):
    """Agrupa fragmentos en líneas visuales (mismo top ±2pt)."""
    frs = sorted(pagina["textos"], key=lambda t: (round(t["top"]), t["left"]))
    out = []
    for t in frs:
        if out and abs(out[-1]["top"] - t["top"]) <= 2:
            L = out[-1]
            L["frag"].append(t)
            L["right"] = max(L["right"], t["left"] + t["w"])
            L["txt"] += t["txt"]
        else:
            out.append({"top": t["top"], "left": t["left"], "right": t["left"] + t["w"],
                        "frag": [t], "txt": t["txt"]})
    for L in out:
        principal = max(L["frag"], key=lambda f: len(f["txt"]))
        L["size"], L["familia"], L["bold"] = principal["size"], principal["familia"], all(f["bold"] for f in L["frag"] if f["txt"].strip())
        L["txt"] = L["txt"].strip()
    return out


# ---------- análisis ----------

def analizar_fuentes(paginas):
    chars = collections.Counter()
    for p in paginas:
        for t in p["textos"]:
            chars[(t["familia"], round(t["size"] * 2) / 2)] += len(t["txt"].strip())
    total = sum(chars.values()) or 1
    (fam, size), n = chars.most_common(1)[0]
    otras = [{"familia": f, "size": s, "pct": round(100 * c / total, 1)}
             for (f, s), c in chars.most_common() if c / total >= 0.01 and (f, s) != (fam, size)]
    return {"cuerpo": {"familia": fam, "size": size, "pct": round(100 * n / total, 1)},
            "fuente_ok": fam in FUENTES_OK or "equivalente" in fam,
            "fuentes_permitidas": sorted(FUENTES_OK),
            "tamano_ok": abs(size - TAM_OK) <= TOL_TAM,
            "otras": otras,
            "familias_no_permitidas": sorted({f for (f, s), c in chars.items()
                                              if c / total >= 0.01 and f != fam and f not in FUENTES_OK and "equivalente" not in f})}


def clasificar_interlineado(ratio):
    # Word/Docs/LibreOffice: "simple" ≈ 1,15–1,2×, "múltiple 1,15" ≈ 1,32×, LaTeX \linespread{1.15} ≈ 1,39×,
    # "1,5" real ≈ 1,5× (Typst) a 1,72× (Word), "doble" ≈ 2,3×. Corte en 1,45 para que 1,15 y 1,39 caigan en simple.
    if ratio < 1.45:
        return "simple"
    if ratio < 1.95:
        return "1,5"
    return "doble"


def analizar_interlineado(paginas, cuerpo):
    deltas = []
    por_pagina = {}
    for p in paginas:
        ls = [L for L in lineas(p) if L["familia"] == cuerpo["familia"]
              and abs(L["size"] - cuerpo["size"]) <= TOL_TAM and len(L["txt"]) > 40]
        ds = []
        for a, b in zip(ls, ls[1:]):
            d = b["top"] - a["top"]
            if 8 <= d <= 45 and abs(a["left"] - b["left"]) <= 3:
                ds.append(d)
        if ds:
            deltas += ds
            if len(ds) >= 6:  # con menos líneas el espacio entre párrafos domina la mediana
                por_pagina[p["n"]] = statistics.median(ds)
    if not deltas:
        return {"error": "no se encontraron párrafos de cuerpo suficientes"}
    med = statistics.median(deltas)
    ratio = med / cuerpo["size"]
    clases = collections.Counter(clasificar_interlineado(d / cuerpo["size"]) for d in deltas)
    tot = sum(clases.values())
    return {"salto_pt": round(med, 1), "ratio": round(ratio, 2), "clase": clasificar_interlineado(ratio),
            "nota": "LaTeX 12 pt: simple = 14,5 pt; \\onehalfspacing (setspace) = 18 pt; \\linespread{1.15} = 16,7 pt" if ratio < 1.45 else "",
            "distribucion": {k: round(100 * v / tot) for k, v in clases.most_common()},
            "paginas_fuera": sorted(n for n, m in por_pagina.items()
                                    if clasificar_interlineado(m / cuerpo["size"]) != "1,5")}


def analizar_justificado(paginas, cuerpo):
    rights, dobles, n_lineas, por_pagina = [], 0, 0, {}
    for p in paginas:
        ls = [L for L in lineas(p) if L["familia"] == cuerpo["familia"]
              and abs(L["size"] - cuerpo["size"]) <= TOL_TAM]
        if len(ls) < 4:
            continue
        maxr = max(L["right"] for L in ls)
        deltas = [b["top"] - a["top"] for a, b in zip(ls, ls[1:]) if 8 <= b["top"] - a["top"] <= 45]
        salto = statistics.median(deltas) if deltas else 20
        largas = []
        for i, L in enumerate(ls):
            if (L["right"] - L["left"]) <= 0.75 * (maxr - min(x["left"] for x in ls)):
                continue
            if RE_VINETA.match(L["txt"]):
                continue  # las viñetas no se justifican
            sig = ls[i + 1] if i + 1 < len(ls) else None
            ultima = sig is None or sig["top"] - L["top"] > 1.4 * salto or abs(sig["left"] - L["left"]) > 3 or RE_VINETA.match(sig["txt"])
            if ultima:
                continue  # la última línea de un párrafo justificado queda corta
            largas.append(L)
        al = 0
        for L in largas:
            n_lineas += 1
            rights.append(maxr - L["right"])
            al += maxr - L["right"] <= 2.5
            if "  " in L["txt"].strip():
                dobles += 1
        if len(largas) >= 4:
            por_pagina[p["n"]] = round(100 * al / len(largas))
    if n_lineas < 5:
        return {"error": "pocas líneas largas para evaluar"}
    alineadas = sum(1 for r in rights if r <= 2.5) / n_lineas
    estado = "sí" if alineadas >= 0.75 else ("parcial" if alineadas >= 0.45 or dobles / n_lineas >= 0.3 else "no")
    return {"lineas_evaluadas": n_lineas, "pct_borde_derecho_alineado": round(100 * alineadas),
            "pct_con_espacios_dobles": round(100 * dobles / n_lineas), "justificado": estado,
            "paginas_dudosas": sorted(n for n, v in por_pagina.items() if v < 75)}


RE_TOC = re.compile(r"^(?P<t>.+?)\s*(?:(?:\s*[.…]){2,}|\s{2,})\s*(?P<p>\d{1,3})\s*$")
RE_INVISIBLE = re.compile("[\u2060\u200b\ufeff\u00a0]")
RE_NUMERADO = re.compile(r"^(\d+(\.\d+)*\.?|[a-z]\)|[IVX]+\.)\s+")
RE_VINETA = re.compile(r"^\s*([•●▪◦‣\-–*]|\d{1,2}[.)]|[a-z][.)])\s")
RE_CAPTION = re.compile(r"^(Figura|Fig\.|Tabla|Imagen|Gr[aá]fico|Cuadro|Ilustraci[oó]n)\s*(\d+)", re.I)


def texto_paginas(pdf, n):
    return [run(["pdftotext", "-layout", "-f", str(i), "-l", str(i), pdf, "-"]) for i in range(1, n + 1)]


def analizar_estructura(paginas, cuerpo, textos_pag):
    heads = []
    for p in paginas:
        for L in lineas(p):
            t = L["txt"]
            if not (2 <= len(t) <= 120) or RE_CAPTION.match(t) or "http" in t:
                continue
            # filas de tabla: varios fragmentos en la misma línea separados por huecos grandes
            frs = sorted(L["frag"], key=lambda f: f["left"])
            if any(b["left"] - (a["left"] + a["w"]) > 25 for a, b in zip(frs, frs[1:]) if a["txt"].strip() and b["txt"].strip()):
                continue
            grande = L["size"] >= cuerpo["size"] + 1.5
            negrita_sola = L["bold"] and L["size"] >= cuerpo["size"] - 0.6 and not t.endswith((".", ",", ";"))
            if (grande or negrita_sola) and len(t.split()) <= 14:
                heads.append({"pag": p["n"], "txt": t, "size": round(L["size"], 1), "bold": L["bold"]})

    # texto repetido en 3+ páginas es encabezado o pie de página, no un título
    repetidos = {k for k, v in collections.Counter(norm(h["txt"]) for h in heads).items() if v >= 3}
    heads = [h for h in heads if norm(h["txt"]) not in repetidos]

    def buscar(patron):
        return [h for h in heads if re.search(patron, norm(h["txt"]))]

    toc_heads = buscar(r"^(indice|tabla de contenido|contenido)s?( general)?$")
    idx_fig = buscar(r"^(indice|lista|tabla) de (figuras|ilustraciones|imagenes)")
    idx_tab = buscar(r"^(indice|lista|tabla) de tablas")
    biblio = buscar(r"^(bibliografia|referencias)( bibliograficas)?$")
    anexo = buscar(r"^(anexos?|apendices?)( [a-z0-9]+)?( |$)")

    # entradas del índice: líneas con número de página al final, en páginas con encabezado de índice
    toc_pags = sorted({h["pag"] for h in toc_heads + idx_fig + idx_tab})
    entradas = []
    for n in toc_pags:
        for raw in textos_pag[n - 1].splitlines():
            m = RE_TOC.match(RE_INVISIBLE.sub(" ", raw).strip())
            if m and len(m.group("t")) > 2 and not m.group("t").strip().isdigit():
                entradas.append({"pag_indice": n, "titulo": m.group("t").strip(), "pag_declarada": int(m.group("p"))})

    # cotejo índice ↔ títulos
    cuerpo_heads = [h for h in heads if h["pag"] not in toc_pags and h["pag"] > 1]  # la carátula no va al índice
    def key(s):
        return norm(RE_NUMERADO.sub("", s))
    faltan_en_doc, pag_distinta, ok, pares = [], [], [], []
    for e in entradas:
        if RE_CAPTION.match(e["titulo"]):
            continue
        k = key(e["titulo"])
        cand = [h for h in cuerpo_heads if key(h["txt"]) == k or (len(k) > 12 and (k in key(h["txt"]) or key(h["txt"]) in k))]
        if not cand:
            faltan_en_doc.append(e)
        else:
            pares.append((e, sorted({h["pag"] for h in cand})))
    # la numeración impresa puede arrancar después de carátula e índice: se admite un desfasaje constante
    offsets = collections.Counter(min(p) - e["pag_declarada"] for e, p in pares)
    desfasaje = offsets.most_common(1)[0][0] if offsets else 0
    for e, pags in pares:
        if any(p == e["pag_declarada"] + desfasaje for p in pags):
            ok.append(e)
        else:
            pag_distinta.append({**e, "pag_real": pags})
    claves_idx = {key(e["titulo"]) for e in entradas}
    sin_indice = [h for h in cuerpo_heads if h["size"] >= cuerpo["size"] + 1.5
                  and key(h["txt"]) not in claves_idx
                  and not any(key(h["txt"]) in c or c in key(h["txt"]) for c in claves_idx if len(c) > 12)
                  and not re.search(r"^(indice|bibliografia|referencias|anexo|apendice)", norm(h["txt"]))]

    return {
        "caratula": {"pag1_lineas": [L["txt"] for L in lineas(paginas[0])][:12],
                     "pag1_parece_caratula": len(lineas(paginas[0])) <= 25 and not any(
                         len(L["txt"]) > 100 for L in lineas(paginas[0]))},
        "indice": {"presente": bool(toc_heads), "paginas": sorted({h["pag"] for h in toc_heads}),
                   "entradas": len([e for e in entradas if not RE_CAPTION.match(e["titulo"])])},
        "indice_figuras": {"presente": bool(idx_fig), "paginas": sorted({h["pag"] for h in idx_fig})},
        "indice_tablas": {"presente": bool(idx_tab), "paginas": sorted({h["pag"] for h in idx_tab})},
        "bibliografia": {"presente": bool(biblio), "paginas": sorted({h["pag"] for h in biblio})},
        "anexo": {"presente": bool(anexo), "paginas": sorted({h["pag"] for h in anexo})},
        "titulos_detectados": [{"pag": h["pag"], "txt": h["txt"], "size": h["size"]} for h in cuerpo_heads],
        "cotejo_indice": {"ok": len(ok), "desfasaje_paginas": desfasaje, "entradas_sin_titulo_en_doc": faltan_en_doc,
                          "pagina_distinta": pag_distinta,
                          "titulos_sin_entrada_en_indice": [{"pag": h["pag"], "txt": h["txt"]} for h in sin_indice]},
        "_entradas": entradas,
    }


def analizar_epigrafes(paginas, estructura, textos_pag):
    toc_pags = set(estructura["indice"]["paginas"] + estructura["indice_figuras"]["paginas"]
                   + estructura["indice_tablas"]["paginas"])
    caps = []
    for p in paginas:
        ls = lineas(p)
        for i, L in enumerate(ls):
            m = RE_CAPTION.match(L["txt"])
            if not m or p["n"] in toc_pags:
                continue
            tipo = "Tabla" if m.group(1).lower() in ("tabla", "cuadro") else "Figura"
            info = {"pag": p["n"], "tipo": tipo, "num": int(m.group(2)), "txt": L["txt"][:90]}
            if tipo == "Figura":
                arriba = [im for im in p["imagenes"] if im["top"] + im["h"] <= L["top"] + 5 and L["top"] - (im["top"] + im["h"]) < 120]
                abajo = [im for im in p["imagenes"] if im["top"] >= L["top"] - 5 and im["top"] - L["top"] < 120]
                info["imagen_arriba"], info["imagen_abajo"] = bool(arriba), bool(abajo)
                info["debajo_de_figura"] = bool(arriba) and not (abajo and not arriba)
                if not arriba and not abajo:
                    info["debajo_de_figura"] = None  # figura vectorial o en otra página: revisar a mano
            else:
                def filas(rango):
                    tops = collections.Counter(round(f["top"]) for L2 in rango for f in L2["frag"])
                    lefts = collections.defaultdict(set)
                    for L2 in rango:
                        for f in L2["frag"]:
                            lefts[round(f["top"])].add(round(f["left"] / 10))
                    return sum(1 for t in tops if len(lefts[t]) >= 2)
                arriba = filas([x for x in ls[max(0, i - 12):i] if L["top"] - x["top"] < 220])
                abajo = filas([x for x in ls[i + 1:i + 13] if x["top"] - L["top"] < 220])
                info["filas_tabla_arriba"], info["filas_tabla_abajo"] = arriba, abajo
                info["debajo_de_tabla"] = arriba > abajo if (arriba or abajo) else None
            caps.append(info)

    # tablas por geometría: 3+ líneas seguidas con 2+ columnas (fragmentos en la misma fila con hueco > 25 pt)
    tablas_geom = []
    for p in paginas:
        if p["n"] in toc_pags:
            continue
        ls = lineas(p)
        racha, inicio = 0, None
        for L in ls + [None]:
            multicol = False
            if L is not None:
                frs = sorted(L["frag"], key=lambda f: f["left"])
                multicol = any(b["left"] - (a["left"] + a["w"]) > 25 for a, b in zip(frs, frs[1:])
                               if a["txt"].strip() and b["txt"].strip())
            if multicol:
                racha += 1
                inicio = inicio if inicio is not None else L["top"]
            else:
                if racha >= 3:
                    tablas_geom.append({"pag": p["n"], "top": inicio, "filas": racha})
                racha, inicio = 0, None
    # figuras/tablas sin epígrafe: imágenes grandes (> 100×60 pt) o bloques-tabla sin «Figura/Tabla N» a menos de 120 pt
    def hay_epigrafe(pag, top, alto, tipo):
        return any(c["pag"] == pag and c["tipo"] == tipo and -120 <= (c["_top"] - (top + alto)) <= 120 for c in caps)
    for c in caps:
        c["_top"] = next((L["top"] for L in lineas(paginas[c["pag"] - 1]) if L["txt"][:90] == c["txt"]), 0)
    imagenes_sin = [{"pag": p["n"], "top": round(im["top"])} for p in paginas if p["n"] not in toc_pags and p["n"] > 1
                    for im in p["imagenes"] if im["w"] > 100 and im["h"] > 60 and not hay_epigrafe(p["n"], im["top"], im["h"], "Figura")]
    tablas_sin = [t for t in tablas_geom if not hay_epigrafe(t["pag"], t["top"], t["filas"] * 15, "Tabla")]
    for c in caps:
        c.pop("_top", None)

    # correlación con índices de figuras/tablas
    entradas = [e for e in estructura["_entradas"] if RE_CAPTION.match(e["titulo"])]
    idx = {}
    for e in entradas:
        m = RE_CAPTION.match(e["titulo"])
        tipo = "Tabla" if m.group(1).lower() in ("tabla", "cuadro") else "Figura"
        idx[(tipo, int(m.group(2)))] = e
    cotejo = []
    for c in caps:
        e = idx.get((c["tipo"], c["num"]))
        cotejo.append({"tipo": c["tipo"], "num": c["num"], "pag": c["pag"], "en_indice": e is not None,
                       "pag_indice_ok": (e["pag_declarada"] == c["pag"]) if e else None})
    en_idx_sin_epigrafe = [f"{t} {n} (p. {e['pag_declarada']})" for (t, n), e in idx.items()
                           if not any(c["tipo"] == t and c["num"] == n for c in caps)]

    # referencias desde el texto ("como muestra la Figura 2"), excluyendo la línea del epígrafe
    texto_total = "\n".join(textos_pag)
    for c in caps:
        patron = re.compile(r"\b(%s)\s*%d\b" % (r"Figura|Fig\.|Imagen|Gr[aá]fico|Ilustraci[oó]n" if c["tipo"] == "Figura" else r"Tabla|Cuadro", c["num"]), re.I)
        c["referencias_en_texto"] = sum(1 for m in patron.finditer(texto_total)
                                        if not RE_CAPTION.match(texto_total[texto_total.rfind("\n", 0, m.start()) + 1:m.end() + 60].strip()))

    def secuencia(tipo):
        nums = [c["num"] for c in caps if c["tipo"] == tipo]
        return nums == list(range(1, len(nums) + 1))
    return {"epigrafes": caps, "cotejo_indice": cotejo, "en_indice_sin_epigrafe": en_idx_sin_epigrafe,
            "tablas_detectadas": len(tablas_geom), "tablas_sin_epigrafe": tablas_sin,
            "imagenes_grandes_sin_epigrafe": imagenes_sin,
            "numeracion_figuras_correlativa": secuencia("Figura"),
            "numeracion_tablas_correlativa": secuencia("Tabla"),
            "imagenes_por_pagina": {p["n"]: len(p["imagenes"]) for p in paginas if p["imagenes"]}}


# ---------- lenguaje ----------

PRONOMBRES = r"\b(yo|nosotros|nosotras|nuestro|nuestra|nuestros|nuestras|conmigo|vos|ustedes|tú|tuyo|tuya|tuyos|tuyas)\b"
VOSEO = r"\b(tenés|podés|querés|sabés|hacés|decís|sos|mirá|fijate|acordate|andá|vení|hacé|tené|usá|pensá|imaginá|vas a ver|te das cuenta|tenes|podes|queres|sabes|haces|puedes|tienes|quieres|debes|ves)\b"
PRIMERA_SING = r"\b(creo|pienso|considero|propongo|quiero|voy a|opino|espero|me parece|mi proyecto|mi trabajo|mi propuesta)\b"
EXCL_AMOS = {"gramos", "kilogramos", "miligramos", "tramos", "ramos", "reclamos", "minimos", "maximos", "optimos",
             "ultimos", "proximos", "mismos", "decimos", "intimos", "legitimos", "infimos", "pesimos", "primos",
             "remos", "programos", "cosmos", "dinamos", "diagramos", "ambos", "lemos", "monimos", "anonimos",
             "sinonimos", "antonimos", "homonimos", "autonomos", "economos", "tomos", "atomos", "aromas", "ramas",
             "textos", "extremos", "supremos", "internos", "externos", "modernos", "eternos", "cuadernos", "gobiernos",
             "cremos", "temos", "domos", "trimos"}
RE_1PL = re.compile(r"\b([a-záéíóúñ]{2,}?(?:ábamos|íamos|aremos|eremos|iremos|amos|emos|imos))\b", re.I)


def analizar_lenguaje(textos_pag, pags_excluir):
    hallazgos = []
    for n, texto in enumerate(textos_pag, 1):
        if n in pags_excluir:
            continue
        plano = re.sub(r"\s+", " ", texto)
        for etiqueta, patron in (("pronombre 1ª/2ª persona", PRONOMBRES), ("voseo/tuteo", VOSEO), ("1ª persona singular", PRIMERA_SING)):
            for m in re.finditer(patron, plano, re.I):
                hallazgos.append({"pag": n, "tipo": etiqueta, "palabra": m.group(0),
                                  "contexto": plano[max(0, m.start() - 60):m.end() + 60].strip()})
        for m in RE_1PL.finditer(plano):
            w = norm(m.group(1))
            if w in EXCL_AMOS or len(w) < 5 or re.search(r"[áéíóú]", m.group(1)[:-4]) and not m.group(1).lower().endswith(("ábamos", "íamos")):
                continue
            hallazgos.append({"pag": n, "tipo": "verbo 1ª persona plural (candidato)", "palabra": m.group(1),
                              "contexto": plano[max(0, m.start() - 60):m.end() + 60].strip()})
        for m in re.finditer(r"\b[a-záéíóúñ]{3,}(ás|és|ís)\b", plano):
            w = norm(m.group(0))
            if w in {"ademas", "despues", "traves", "ingles", "frances", "interes", "pais", "quizas", "jamas", "atras",
                     "detras", "compas", "anis", "cortes", "portugues", "japones", "holandes", "escoces", "danes",
                     "marques", "revés", "reves", "estres", "envés", "enves", "traves", "demas", "paris", "paises",
                     "reles", "cafes", "bebes", "chales", "carnes", "cipres", "burgues", "vienes", "cortes", "montes"} or len(w) < 4:
                continue
            hallazgos.append({"pag": n, "tipo": "posible voseo (terminación -ás/-és/-ís)", "palabra": m.group(0),
                              "contexto": plano[max(0, m.start() - 60):m.end() + 60].strip()})
    return hallazgos


# ---------- informe ----------

def si(b):
    return "✅" if b else "❌"


def informe(pdf, r):
    f, i, j, e, ep, l = r["fuentes"], r["interlineado"], r["justificado"], r["estructura"], r["epigrafes"], r["lenguaje"]
    pi = r["pdfinfo"]
    out = [f"# Análisis mecánico de formato — `{os.path.basename(pdf)}`", "",
           f"Generado con: {pi['Creator'] or '?'} / {pi['Producer'] or '?'} · creado {pi['CreationDate'] or 'sin metadato (Google Docs no lo escribe)'} · modificado {pi['ModDate'] or 'sin metadato'}"
           + (f" · título «{pi['Title']}»" if pi['Title'] else "") + (f" · autor {pi['Author']}" if pi['Author'] else ""),
           f"Páginas: {r['paginas']}. Texto de cuerpo detectado: **{f['cuerpo']['familia']} {f['cuerpo']['size']} pt** "
           f"({f['cuerpo']['pct']}% de los caracteres).", "",
           "## 1. Tipografía y párrafo",
           f"- {si(f['fuente_ok'])} Fuente del cuerpo permitida ({' / '.join(f['fuentes_permitidas'])}): {f['cuerpo']['familia']}",
           f"- {si(f['tamano_ok'])} Tamaño del cuerpo 12 pt: {f['cuerpo']['size']} pt"]
    if f["familias_no_permitidas"]:
        out.append(f"- ⚠️ Otras familias con presencia ≥1 %: {', '.join(f['familias_no_permitidas'])} (ver si son código, tablas o epígrafes)")
    if f["otras"]:
        out.append("- Otras combinaciones fuente/tamaño (≥1 %): " + "; ".join(f"{o['familia']} {o['size']} pt ({o['pct']}%)" for o in f["otras"]))
    if "error" in i:
        out.append(f"- ⚠️ Interlineado: {i['error']}")
    else:
        out.append(f"- {si(i['clase'] == '1,5')} Interlineado 1,5: salto entre líneas {i['salto_pt']} pt = {i['ratio']}× el tamaño → **{i['clase']}**. Distribución: {i['distribucion']}")
        if i.get("nota"):
            out.append(f"  - Referencia: {i['nota']}")
        if i["paginas_fuera"]:
            out.append(f"  - Páginas cuyo interlineado predominante no es 1,5: {i['paginas_fuera']}")
    if "error" in j:
        out.append(f"- ⚠️ Justificado: {j['error']}")
    else:
        icono = {"sí": "✅", "parcial": "❓", "no": "❌"}[j["justificado"]]
        out.append(f"- {icono} Texto justificado ({j['justificado']}): {j['pct_borde_derecho_alineado']}% de las líneas largas terminan en el margen derecho; {j['pct_con_espacios_dobles']}% muestran espaciado variable entre palabras ({j['lineas_evaluadas']} líneas evaluadas)")
        if j["paginas_dudosas"]:
            out.append(f"  - Páginas con párrafos que no parecen justificados: {j['paginas_dudosas']}")

    out += ["", "## 2. Estructura",
            f"- {si(e['caratula']['pag1_parece_caratula'])} Carátula (página 1 con pocas líneas y sin párrafos): " + " | ".join(e["caratula"]["pag1_lineas"][:6]),
            f"- {si(e['indice']['presente'])} Índice general: páginas {e['indice']['paginas']} ({e['indice']['entradas']} entradas detectadas)",
            f"- {si(e['indice_figuras']['presente'])} Índice de figuras: páginas {e['indice_figuras']['paginas']}",
            f"- {si(e['indice_tablas']['presente'])} Índice de tablas: páginas {e['indice_tablas']['paginas']}",
            f"- {si(e['bibliografia']['presente'])} Bibliografía / Referencias: páginas {e['bibliografia']['paginas']}",
            f"- {'✅' if e['anexo']['presente'] else 'ℹ️'} Anexo (opcional): páginas {e['anexo']['paginas']}",
            "", "### Títulos y subtítulos detectados (por tamaño/negrita)"]
    for h in e["titulos_detectados"]:
        out.append(f"- p.{h['pag']} [{h['size']} pt] {h['txt']}")
    c = e["cotejo_indice"]
    out += ["", f"### Cotejo índice ↔ títulos: {c['ok']} entradas coinciden en texto y página"
            + (f" (numeración impresa desfasada {c['desfasaje_paginas']} páginas respecto del PDF: carátula/índice sin numerar)" if c['desfasaje_paginas'] else "")]
    for x in c["pagina_distinta"]:
        out.append(f"- ⚠️ «{x['titulo']}»: el índice dice p.{x['pag_declarada']} pero el título está en p.{x['pag_real']} del PDF")
    for x in c["entradas_sin_titulo_en_doc"]:
        out.append(f"- ❌ «{x['titulo']}» (índice p.{x['pag_declarada']}): no se encontró un título con ese texto en el cuerpo")
    if e["indice"]["presente"]:
        for x in c["titulos_sin_entrada_en_indice"]:
            out.append(f"- ⚠️ Título «{x['txt']}» (p.{x['pag']}) no aparece en el índice")

    out += ["", "## 3. Figuras y tablas",
            f"- Imágenes rasterizadas por página (sin contar logos repetidos en 3+ páginas): {ep['imagenes_por_pagina'] or 'ninguna (si hay figuras, son vectoriales: revisar a mano)'}",
            f"- {si(ep['numeracion_figuras_correlativa'])} Numeración de figuras correlativa",
            f"- {si(ep['numeracion_tablas_correlativa'])} Numeración de tablas correlativa"]
    n_img = sum(v for v in ep["imagenes_por_pagina"].values())
    out.append(f"- Tablas detectadas por geometría (3+ filas con 2+ columnas): {ep['tablas_detectadas']}"
               + (f"; {'✅ todas' if not ep['tablas_sin_epigrafe'] else '❌ ' + str(len(ep['tablas_sin_epigrafe']))} sin epígrafe «Tabla N» cerca"
                  + (": " + ", ".join(f"p.{t['pag']}" for t in ep['tablas_sin_epigrafe']) if ep['tablas_sin_epigrafe'] else "") if ep['tablas_detectadas'] else ""))
    if ep["imagenes_grandes_sin_epigrafe"]:
        out.append(f"- ❓ Imágenes grandes (> 100×60 pt) sin epígrafe «Figura N» cerca (pueden ser logos de plantilla o figuras sin rotular): "
                   + ", ".join(f"p.{i['pag']}" for i in ep["imagenes_grandes_sin_epigrafe"]))
    if not ep["epigrafes"]:
        out.append(f"- ❌ No se encontró ningún epígrafe «Figura N» / «Tabla N» en el documento"
                   + (f", aunque hay {n_img} imágenes (parte pueden ser logos o adornos)" if n_img else ""))
    for cp in ep["epigrafes"]:
        if cp["tipo"] == "Figura":
            pos = {True: "✅ debajo de una imagen", False: "❌ la imagen está debajo del epígrafe", None: "❓ no hay imagen rasterizada cerca: revisar"}[cp["debajo_de_figura"]]
        else:
            pos = {True: "✅ parece estar debajo de la tabla", False: "❌ la tabla parece estar debajo del epígrafe", None: "❓ no se detectó tabla cerca: revisar"}[cp["debajo_de_tabla"]]
        refs = cp.get("referencias_en_texto", 0)
        out.append(f"- p.{cp['pag']} «{cp['txt']}» → {pos}; "
                   + (f"referenciada {refs} vez/veces desde el texto" if refs else "❌ el texto nunca la referencia por número"))
    for ct in ep["cotejo_indice"]:
        if not ct["en_indice"]:
            out.append(f"- ❌ {ct['tipo']} {ct['num']} (p.{ct['pag']}) no figura en el índice de {ct['tipo'].lower()}s")
        elif ct["pag_indice_ok"] is False:
            out.append(f"- ⚠️ {ct['tipo']} {ct['num']}: el índice declara otra página (real: p.{ct['pag']})")
    for s in ep["en_indice_sin_epigrafe"]:
        out.append(f"- ❌ {s} está en el índice pero no se encontró su epígrafe en el cuerpo")

    out += ["", f"## 4. Lenguaje — {len(l)} candidatos (cada uno necesita lectura del contexto)"]
    for h in l:
        out.append(f"- p.{h['pag']} [{h['tipo']}] **{h['palabra']}** — …{h['contexto']}…")
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    pdf = sys.argv[1]
    info = {}
    for linea in run(["pdfinfo", pdf]).splitlines():
        if ":" in linea:
            k, v = linea.split(":", 1)
            info[k.strip()] = v.strip()
    if not info.get("Creator") and "Google Docs" in info.get("Producer", ""):
        info["Creator"] = "Google Docs"
    elif not info.get("Creator") and "Microsoft" in info.get("Producer", ""):
        info["Creator"] = "Microsoft Word"
    paginas = extraer(pdf)
    # logos y adornos de plantilla: la misma imagen (posición y tamaño) en 3+ páginas no es una figura
    firmas = collections.Counter((round(im["top"]), round(im["left"]), round(im["w"]), round(im["h"]))
                                 for p in paginas for im in p["imagenes"])
    for p in paginas:
        p["imagenes"] = [im for im in p["imagenes"]
                         if firmas[(round(im["top"]), round(im["left"]), round(im["w"]), round(im["h"]))] < 3]
    textos = texto_paginas(pdf, len(paginas))
    fuentes = analizar_fuentes(paginas)
    cuerpo = fuentes["cuerpo"]
    estructura = analizar_estructura(paginas, cuerpo, textos)
    excluir = set(estructura["indice"]["paginas"] + estructura["indice_figuras"]["paginas"]
                  + estructura["indice_tablas"]["paginas"] + estructura["bibliografia"]["paginas"] + [1])
    r = {"archivo": pdf, "paginas": len(paginas), "fuentes": fuentes,
         "pdfinfo": {k: info.get(k, "") for k in ("Creator", "Producer", "CreationDate", "ModDate", "Title", "Author")},
         "interlineado": analizar_interlineado(paginas, cuerpo),
         "justificado": analizar_justificado(paginas, cuerpo),
         "estructura": estructura, "epigrafes": analizar_epigrafes(paginas, estructura, textos),
         "lenguaje": analizar_lenguaje(textos, excluir)}
    estructura.pop("_entradas", None)
    if "--json" in sys.argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(informe(pdf, r))


if __name__ == "__main__":
    main()
