#!/usr/bin/env bash
# Casos de borde: cierre por tiempo, votos fuera de ventana, doble voto,
# duplicado por QoS 1, opción inválida y caída de un pulsador.
set -u
cd "$(dirname "$0")"
rm -rf /tmp/eb && mkdir -p /tmp/eb
printf 'listener 1883 127.0.0.1\nallow_anonymous true\n' > /tmp/eb/m.conf
mosquitto -c /tmp/eb/m.conf > /tmp/eb/broker.log 2>&1 & BROKER=$!
sleep 1
rm -f data/prueba.db*
DB_PATH=$PWD/data/prueba.db CLICKAULA_DEV=1 python3 run.py > /tmp/eb/app.log 2>&1 & APP=$!
sleep 3
trap 'kill $APP $BROKER 2>/dev/null' EXIT

E() { echo; echo "── $1"; }
estado() { curl -s localhost:5000/api/estado; }
voto()  { mosquitto_pub -t "aula/voto/$1" -q 1 -m "{\"opcion\":\"$2\",\"seq\":$3}"; }
pres()  { mosquitto_pub -t "aula/presencia/$1" -r -m "{\"online\":$2}"; }

# Encuesta corta: 5 s por pregunta, una pregunta de 2 opciones.
curl -s -X POST localhost:5000/api/encuestas -H 'Content-Type: application/json' -d '{
  "nombre":"Bordes","modalidad":"competencia","segundos":5,"puntaje_base":500,
  "preguntas":[
    {"enunciado":"Solo dos opciones","opciones":["Si","No"],"correcta":"A"},
    {"enunciado":"Cuatro opciones","opciones":["a","b","c","d"],"correcta":"D"}]}' > /tmp/eb/enc.json
ENC=$(python3 -c "import json;print(json.load(open('/tmp/eb/enc.json'))['id'])")

E "presencia: 3 pulsadores se anuncian"
pres px1 true; pres px2 true; pres px3 true; sleep 1
estado | python3 -c "import json,sys;s=json.load(sys.stdin);print('  en linea:',sum(p['online'] for p in s['pulsadores']),'de',len(s['pulsadores']))"

E "voto ANTES de abrir la partida -> debe descartarse"
voto px1 A 1; sleep 0.7
grep -o "descartado: fuera_de_ventana" /tmp/eb/app.log | tail -1 | sed 's/^/  ok: /'

curl -s -X POST localhost:5000/api/partida/iniciar -H 'Content-Type: application/json' \
     -d "{\"encuesta_id\":$ENC}" > /dev/null
E "voto en la SALA DE ESPERA -> debe descartarse"
voto px1 A 2; sleep 0.7
grep -c "fuera_de_ventana" /tmp/eb/app.log | sed 's/^/  descartes acumulados: /'

curl -s -X POST localhost:5000/api/partida/comenzar > /dev/null
E "P1 tiene 2 opciones: voto a la D -> opcion_invalida"
voto px1 D 3; sleep 0.7
grep -o "descartado: opcion_invalida" /tmp/eb/app.log | tail -1 | sed 's/^/  ok: /'

E "px1 vota A (correcta), despues intenta B -> gana la primera pulsacion"
voto px1 A 4; sleep 0.4
voto px1 B 5; sleep 0.7
grep -o "descartado: ya_voto" /tmp/eb/app.log | tail -1 | sed 's/^/  ok: /'

E "reenvio del MISMO mensaje (mismo seq) desde px2 -> duplicado"
voto px2 A 10; sleep 0.4
voto px2 A 10; sleep 0.7
grep -o "descartado: duplicado" /tmp/eb/app.log | tail -1 | sed 's/^/  ok: /'

E "CIERRE AUTOMATICO: la pregunta dura 5 s y nadie la cierra a mano"
echo "  esperando el vencimiento..."
sleep 6
estado | python3 -c "
import json,sys;s=json.load(sys.stdin)
print('  estado:',s['estado'],'(esperado RESULTADOS)')
print('  conteo P1:',s['conteo'],'-> px1 cuenta una sola vez')
print('  top:',[(t['posicion'],t['numero'],t['puntos']) for t in s['top_pregunta']])"

curl -s -X POST localhost:5000/api/partida/siguiente > /dev/null
E "P2: un pulsador se cae (ultima voluntad) mientras esta abierta"
pres px3 false; sleep 1
estado | python3 -c "
import json,sys;s=json.load(sys.stdin)
print('  en linea:',sum(p['online'] for p in s['pulsadores']),
      '| esperados fijados al abrir:',s['esperados'])"
voto px1 D 20; voto px2 D 21; sleep 6
estado | python3 -c "
import json,sys;s=json.load(sys.stdin)
print('  estado:',s['estado'],'| conteo:',s['conteo'],'| recibidos:',s['recibidos'])"

E "resumen y guardado"
curl -s -X POST localhost:5000/api/partida/siguiente > /dev/null; sleep 0.4
estado | python3 -c "
import json,sys;s=json.load(sys.stdin)
print('  estado:',s['estado'],'| podio:',s['resumen']['podio'])"
curl -s -X POST localhost:5000/api/partida/finalizar | sed 's/^/  /'

E "trazas de error"
grep -iE "traceback|exception" /tmp/eb/app.log | head -5 || true
echo "  (vacio = sin errores)"
