#!/usr/bin/env bash
# Prueba de extremo a extremo: broker + app + simulador, partida completa.
set -u
cd "$(dirname "$0")"
rm -rf /tmp/e2e && mkdir -p /tmp/e2e
cat > /tmp/e2e/m.conf <<'EOF'
listener 1883 127.0.0.1
allow_anonymous true
EOF

mosquitto -c /tmp/e2e/m.conf > /tmp/e2e/broker.log 2>&1 &
BROKER=$!
sleep 1

rm -f data/clickaula.db*
CLICKAULA_DEV=1 python3 run.py > /tmp/e2e/app.log 2>&1 &
APP=$!
sleep 3

limpiar() { kill $SIM $APP $BROKER 2>/dev/null; wait 2>/dev/null; }
trap limpiar EXIT

echo "### salud"
curl -s localhost:5000/api/salud; echo

echo "### sembrar"
python3 sim/sembrar.py

echo "### 6 pulsadores simulados"
python3 sim/simulador.py --n 6 --acierto 0.7 --min-demora 0.3 --max-demora 3 \
        > /tmp/e2e/sim.log 2>&1 &
SIM=$!
sleep 4
curl -s localhost:5000/api/estado | python3 -c "
import json,sys; s=json.load(sys.stdin)
print('  estado:',s['estado'],'| pulsadores:',len(s['pulsadores']),
      '| en linea:',sum(p['online'] for p in s['pulsadores']))"

echo
echo "########## MODALIDAD COMPETITIVA (encuesta 1, 5 preguntas) ##########"
curl -s -X POST localhost:5000/api/partida/iniciar -H 'Content-Type: application/json' \
     -d '{"encuesta_id":1}' > /dev/null
curl -s -X POST localhost:5000/api/partida/comenzar > /dev/null

for i in 1 2 3 4 5; do
  sleep 4                                    # los simulados votan
  curl -s -X POST localhost:5000/api/partida/cerrar > /dev/null   # cierre manual
  sleep 0.6
  curl -s localhost:5000/api/estado | python3 -c "
import json,sys
s=json.load(sys.stdin)
p=s['pregunta']
print(f\"  P{p['orden']}: correcta={p['correcta']} conteo={s['conteo']} \"
      f\"recibidos={s['recibidos']}/{s['esperados']} \"
      f\"top={[(t['posicion'],t['numero'],t['puntos']) for t in s['top_pregunta']]}\")"
  curl -s -X POST localhost:5000/api/partida/siguiente > /dev/null
  sleep 0.4
done

echo
echo "### resumen final"
curl -s localhost:5000/api/estado | python3 -c "
import json,sys
s=json.load(sys.stdin)
assert s['estado']=='RESUMEN', s['estado']
r=s['resumen']
print('  podio:', r['podio'])
print('  mas facil: P%s   mas dificil: P%s' % (r['mas_facil'], r['mas_dificil']))
print('  leaderboard:', [(f['numero'],f['puntaje']) for f in s['leaderboard']])
tot=sum(p['puntaje'] for p in s['leaderboard'])
print('  total repartido:', tot)"
curl -s -X POST localhost:5000/api/partida/finalizar; echo

echo
echo "########## MODALIDAD ANONIMA (encuesta 2, 3 preguntas) ##########"
curl -s -X POST localhost:5000/api/partida/iniciar -H 'Content-Type: application/json' \
     -d '{"encuesta_id":2}' > /dev/null
curl -s -X POST localhost:5000/api/partida/comenzar > /dev/null
echo "  (sin cerrar a mano: se cierran solas a los 25 s configurados... forzamos)"
for i in 1 2 3; do
  sleep 4
  curl -s -X POST localhost:5000/api/partida/cerrar > /dev/null
  sleep 0.6
  curl -s localhost:5000/api/estado | python3 -c "
import json,sys
s=json.load(sys.stdin)
print('  estado tras cerrar:', s['estado'],
      '| pregunta ahora:', s['pregunta']['orden'] if s['pregunta'] else None)"
done
curl -s localhost:5000/api/estado | python3 -c "
import json,sys
s=json.load(sys.stdin)
r=s['resumen']
print('  RESUMEN anonima -> podio:', r['podio'], '| preguntas:', len(r['preguntas']))
for p in r['preguntas']: print('   P%s %s' % (p['orden'], p['conteo']))"
curl -s -X POST localhost:5000/api/partida/finalizar; echo

echo
echo "### historial"
curl -s localhost:5000/api/salud > /dev/null
python3 - <<'PY'
import sqlite3
c = sqlite3.connect("data/clickaula.db"); c.row_factory = sqlite3.Row
for f in c.execute("SELECT * FROM ejecucion"):
    print(f"  ejecucion {f['id']}: {f['nombre_encuesta']} ({f['modalidad']}) "
          f"{f['participantes']} participantes")
print("  filas ejecucion_pregunta:", c.execute("SELECT COUNT(*) n FROM ejecucion_pregunta").fetchone()["n"])
print("  filas ejecucion_podio:", c.execute("SELECT COUNT(*) n FROM ejecucion_podio").fetchone()["n"])
PY

echo
echo "### exportacion a CSV"
# La ejecucion 1 es la competitiva (tiene podio) y la 2 la anonima (no).
for ruta in "1/preguntas" "1/podio" "2/preguntas"; do
  cod=$(curl -s -o /tmp/e2e/exp.csv -w '%{http_code}' \
        "localhost:5000/historial/${ruta}.csv")
  lineas=$(wc -l < /tmp/e2e/exp.csv)
  # file -i reporta utf-8 solo si la marca de orden de bytes esta presente.
  bom=$(head -c3 /tmp/e2e/exp.csv | od -An -tx1 | tr -d ' ')
  echo "  ${ruta}.csv -> HTTP $cod | $lineas filas | BOM: $([ "$bom" = "efbbbf" ] && echo si || echo NO)"
done
echo "  2/podio.csv (anonima, no debe descargar) -> HTTP $(curl -s -o /dev/null -w '%{http_code}' localhost:5000/historial/2/podio.csv)"
echo "  muestra de 1/preguntas.csv:"
curl -s localhost:5000/historial/1/preguntas.csv | head -3 | sed 's/^/    /'

echo
echo "### errores en el log de la app"
grep -iE "error|traceback|exception" /tmp/e2e/app.log | grep -v "GET /api" | head -10 || echo "  ninguno"
echo "### descartes registrados (esperable: ya_voto / fuera_de_ventana)"
grep -c "descartado" /tmp/e2e/app.log
