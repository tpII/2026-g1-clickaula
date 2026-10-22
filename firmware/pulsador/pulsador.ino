// Firmware del pulsador ClickAula — contrato de mensajería, versión 1.
//
// Publicador puro (R9): no se suscribe a nada ni recibe nada. Pulsa y publica;
// es el servidor el que decide si el voto cuenta.
//
// Placa:      NodeMCU 1.0 (ESP-12E Module), núcleo ESP8266 para Arduino 3.x.
// Biblioteca: "MQTT" de Joel Gaehwiler (arduino-mqtt, de 256dpi). Se usa en
//             lugar de PubSubClient porque ésa no puede publicar en QoS 1, y
//             el contrato pide QoS 1 para los votos (CLAUDE.md, sección 6).

#include <ESP8266WiFi.h>
#include <MQTT.h>

// La clave del WiFi no va al repositorio: vive en secretos.h, que cada uno
// arma a partir de secretos.ejemplo.h.
#if __has_include("secretos.h")
#include "secretos.h"
#else
#error "Falta secretos.h: copiá secretos.ejemplo.h como secretos.h y completá la red del aula."
#endif

const char*    BROKER = "192.168.4.1";   // IP fija de la Pi, ver raspberry/
const uint16_t PUERTO = 1883;

// D1 D2 D6 D7. No usar D0, D3, D4 ni D8: el ESP8266 los lee al arrancar para
// elegir el modo, y un botón apretado ahí lo deja en modo programación.
const uint8_t PINES[4]  = {5, 4, 12, 13};
const char    OPCION[4] = {'A', 'B', 'C', 'D'};

const uint32_t ANTIRREBOTE_MS = 50;
const uint32_t LATIDO_MS      = 5000;
const uint32_t REINTENTO_MS   = 2000;   // entre intentos de conectar al broker

// Cuánto se sigue intentando entregar un voto que no salió. El voto no lleva
// el número de pregunta: el servidor lo asigna a la que esté abierta cuando
// llega. En modalidad anónima la pregunta siguiente se abre apenas cierra la
// anterior, así que un voto entregado tarde puede caer en la pregunta
// equivocada. Por eso la ventana es corta: alcanza para un corte de un
// instante, no para guardar votos durante una caída larga.
const uint32_t VIDA_VOTO_MS   = 1500;
const uint8_t  MAX_PENDIENTES = 8;

const char* PRESENCIA_VIVO  = "{\"online\":true}";
const char* PRESENCIA_CAIDO = "{\"online\":false}";

char id[7];
char topicVoto[32];
char topicPresencia[32];

WiFiClient  red;
MQTTClient  mqtt(128);   // los mensajes del contrato rondan los 30 bytes

uint32_t seq = 0;
uint32_t ultimoLatido = 0;
uint32_t ultimoIntento = 0;
bool     yaIntento = false;

// Antirrebote por nivel sostenido: un cambio cuenta recién cuando el pin se
// mantiene igual 50 ms seguidos. Un pico de ruido en el cable no vota.
bool     nivelEstable[4];
bool     nivelLeido[4];
uint32_t desdeCambio[4];

struct Voto {
  char     opcion;
  uint32_t seq;
  uint32_t creado;
};
Voto    pendientes[MAX_PENDIENTES];
uint8_t cantPendientes = 0;

void quitarPrimero() {
  for (uint8_t i = 1; i < cantPendientes; i++) pendientes[i - 1] = pendientes[i];
  cantPendientes--;
}

void encolarVoto(char opcion, uint32_t ahora) {
  // El pulsador no filtra nada, ni siquiera un segundo voto: "gana la primera
  // pulsación" es una regla del servidor, no de este nodo.
  seq++;
  if (cantPendientes == MAX_PENDIENTES) {
    Serial.printf("[voto] cola llena, se pierde seq=%lu\n",
                  (unsigned long)pendientes[0].seq);
    quitarPrimero();
  }
  pendientes[cantPendientes++] = {opcion, seq, ahora};
  Serial.printf("[voto] %c seq=%lu\n", opcion, (unsigned long)seq);
}

void enviarPendientes() {
  while (cantPendientes > 0 && millis() - pendientes[0].creado > VIDA_VOTO_MS) {
    Serial.printf("[voto] vencido sin entregar, seq=%lu\n",
                  (unsigned long)pendientes[0].seq);
    quitarPrimero();
  }

  while (cantPendientes > 0 && mqtt.connected()) {
    const Voto& v = pendientes[0];
    char payload[40];
    snprintf(payload, sizeof(payload), "{\"opcion\":\"%c\",\"seq\":%lu}",
             v.opcion, (unsigned long)v.seq);

    // En QoS 1 publish() espera el PUBACK del broker. Si no llega, el voto
    // queda en la cola y se reintenta con el mismo seq: si en realidad había
    // llegado, el servidor lo descarta como duplicado.
    if (!mqtt.publish(topicVoto, payload, false, 1)) {
      Serial.printf("[voto] sin confirmación, reintento (error %d)\n",
                    (int)mqtt.lastError());
      return;
    }
    quitarPrimero();
  }
}

void publicarPresencia() {
  mqtt.publish(topicPresencia, PRESENCIA_VIVO, true, 0);
}

void atenderConexion(uint32_t ahora) {
  if (mqtt.connected()) return;
  // El WiFi lo reintenta el núcleo por su cuenta (setAutoReconnect); acá sólo
  // se espera a que vuelva, sin bloquear la lectura de botones.
  if (WiFi.status() != WL_CONNECTED) return;
  if (yaIntento && ahora - ultimoIntento < REINTENTO_MS) return;

  yaIntento = true;
  ultimoIntento = ahora;
  Serial.printf("[mqtt] conectando a %s… ", BROKER);

  // connect() bloquea mientras espera al broker. Un botón apretado y soltado
  // durante ese lapso se pierde, pero sin broker tampoco se podría enviar.
  if (mqtt.connect(id)) {
    Serial.println("ok");
    publicarPresencia();
    ultimoLatido = millis();
  } else {
    Serial.printf("falló (error %d, código %d)\n",
                  (int)mqtt.lastError(), (int)mqtt.returnCode());
  }
}

void leerBotones(uint32_t ahora) {
  for (uint8_t i = 0; i < 4; i++) {
    bool nivel = digitalRead(PINES[i]);
    if (nivel != nivelLeido[i]) {
      nivelLeido[i] = nivel;
      desdeCambio[i] = ahora;
      continue;
    }
    if (nivel != nivelEstable[i] && ahora - desdeCambio[i] >= ANTIRREBOTE_MS) {
      nivelEstable[i] = nivel;
      if (nivel == LOW) encolarVoto(OPCION[i], ahora);   // LOW = apretado
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println();

  snprintf(id, sizeof(id), "%06x", ESP.getChipId());
  snprintf(topicVoto, sizeof(topicVoto), "aula/voto/%s", id);
  snprintf(topicPresencia, sizeof(topicPresencia), "aula/presencia/%s", id);
  Serial.printf("[pulsador] id %s\n", id);

  // El nivel de arranque se toma como reposo: un botón que ya está apretado
  // al encender no emite un voto.
  for (uint8_t i = 0; i < 4; i++) {
    pinMode(PINES[i], INPUT_PULLUP);
    nivelEstable[i] = nivelLeido[i] = digitalRead(PINES[i]);
    desdeCambio[i] = 0;
  }

  WiFi.persistent(false);       // no reescribir la flash en cada arranque
  WiFi.mode(WIFI_STA);
  // Con el ahorro de energía la radio sólo escucha en cada beacon, y cada
  // PUBACK llega con cientos de milisegundos de demora mientras publish()
  // espera bloqueado.
  WiFi.setSleepMode(WIFI_NONE_SLEEP);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_CLAVE);

  mqtt.begin(BROKER, PUERTO, red);
  // Keepalive de 10 s: si el nodo muere sin avisar, el broker publica la
  // última voluntad a los 15 s, el mismo plazo con que la aplicación lo da
  // por caído. Sesión limpia: no hay suscripciones que conservar.
  mqtt.setOptions(10, true, 1000);
  // Tiene que declararse antes de connect(): viaja dentro del CONNECT.
  mqtt.setWill(topicPresencia, PRESENCIA_CAIDO, true, 0);
  // Sin onMessage ni subscribe: este nodo no recibe nada (R9).
}

void loop() {
  uint32_t ahora = millis();

  leerBotones(ahora);
  atenderConexion(ahora);
  mqtt.loop();
  enviarPendientes();

  if (mqtt.connected() && millis() - ultimoLatido >= LATIDO_MS) {
    ultimoLatido = millis();
    publicarPresencia();
  }
}
