# Bitácora del proyecto ClickAula

## Introducción

Esta bitácora recoge los avances, investigaciones y actividades realizadas durante el desarrollo del proyecto ClickAula. Su objetivo es dejar constancia del trabajo realizado y facilitar el seguimiento de la evolución del proyecto.

## Entradas

### 01/09/2026

Investigamos sobre el diseño del protocolo de mensajería MQTT (árbol de temas, formato de los mensajes, niveles de QoS, mensajes retenidos y de última voluntad)

Investigamos sobre los requerimientos de alimentación del pulsador (consumo del ESP8266 en reposo y en transmisión, y dimensionamiento de un regulador dedicado de 5 V a 3.3 V)


### 06/09/2026
 
Investigamos sobre el entorno de desarrollo de la aplicación con Docker (Mosquitto como contenedor y un simulador de pulsadores)

Se avanzo con la creaion del documento "Plan de Proyecto" y su powerpoint.

### 09/09/2026

Se entregó el documento "Plan de Proyecto" junto con su presentación. El documento quedó versionado en la carpeta `Entregas/` del repositorio y el video de documentación en la carpeta compartida de Drive.

### 15/09/2026

Investigamos acerca de los servicios de la Raspberry Pi que van a proveer la red WiFi a los pulsadores y se encontraron posibles trabas a resolver: 
- Existen reportes de la Raspberry Pi 3/3B+ congelandose alrededor de los 20 dispositivos conectados, no es una limitacion de codigo sino de HW (driver brcmfac), se puede solucionar con adaptador de red externo.
- Raspberry Pi OS Bookworm paso a NetworkManager, por lo cual 'dhcpcd.conf' ya no se lee. Se puede usar NetworkManager o hostapd + dnsmasq clasico sacando 'wlan0' de NetworkManager y manejarlo a mano.
- El lease deberia ser corto (aprox. 1hs) para que los pulsadores que se desconectan vuelvan a recibir la misma IP y no pidan una nueva.
- Vamos a necesitar una estrategia para medir en que channel se va a crear la red WiFi para tener la mejor calidad de conexion posible. Medir canales 1, 6 y 11 (Los unicos que no se solapan en 2.4GHz)
- Vamos a tener que definir bien el orden de arranque de los servicios para que funcionen (hostapd, dnsmasq, mosquitto)