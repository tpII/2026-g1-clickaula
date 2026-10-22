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

### 19/09/2026

Se avanzó con el armado del entorno de simulación que va a reemplazar al hardware mientras se construyen los pulsadores. Se está levantando el broker Mosquitto en contenedor —donde surgió que por defecto sólo escucha en localhost y rechaza conexiones anónimas, así que hay que declarar el listener y habilitarlas de forma explícita— junto con un simulador que reproduce el comportamiento previsto del pulsador: presencia retenida con latido, mensaje de última voluntad, y votos con QoS 1 y número de secuencia. La idea es poder variar la cantidad de nodos, el porcentaje de acierto y la demora de respuesta, para ensayar desde 2 pulsadores hasta un aula completa.

### 21/09/2026

En una primera prueba contra el simulador apareció un punto a revisar en la deduplicación de votos: como el número de secuencia de cada pulsador arranca de cero cuando el nodo se reinicia, existe el riesgo de que la aplicación lo confunda con un reenvío de QoS 1 y descarte votos válidos. Con hardware real podría dispararse ante cualquier reinicio por batería o reset accidental. Queda por definir si conviene acotar la ventana de deduplicación a la pregunta en curso o agregar un identificador de arranque al mensaje.

### 25/09/2026

Antes de automatizar nada se probó el contrato de mensajería a mano, por línea de comandos, publicando con `mosquitto_pub` y observando todo el tráfico con `mosquitto_sub -t 'aula/#' -v`. Se dio de alta un pulsador publicando su presencia retenida y se lo vio aparecer en la sala de espera, se emitieron votos con QoS 1 y número de secuencia, y se verificaron los cuatro motivos de descarte previstos: voto sin pregunta abierta, opción que esa pregunta no tiene, segundo voto del mismo pulsador y reenvío con la misma secuencia. También se simuló la caída de un nodo publicando `online:false`, que es exactamente lo que hace el broker con el mensaje de última voluntad. La conclusión es que el contrato se puede ejercitar completo sin una sola línea de firmware, lo que deja al grupo de hardware con una referencia concreta contra la cual programar.

### 28/09/2026

Quedó andando el entorno de simulación sobre Docker: tres contenedores —broker Mosquitto, aplicación y pulsadores simulados— que se levantan con un único comando. Los pulsadores se conectan solos, aparecen en la sala de espera y votan dentro de la ventana, y el tablero refleja cada voto en el momento en que llega. Se corroboró la sincronización entre las partes: la pregunta se abre y se cierra por temporizador del lado del servidor, los votos que llegan fuera de esa ventana se descartan, el cierre ocurre aunque no haya ninguna pantalla abierta, y la grilla muestra en vivo qué pulsadores ya respondieron. Se ensayaron las dos modalidades de punta a punta con 8 pulsadores y se escaló hasta 30 para una primera prueba de carga, sin pérdida de votos. Queda pendiente el ajuste de deduplicación anotado el 23/09.

### 29/09/2026

Dejamos sentada una diferencia real entre el simulador y un pulsador de verdad. El simulador sabe cuándo hay una pregunta abierta porque le pregunta a la aplicación por HTTP cada segundo y medio. Un NodeMCU no puede hacer eso: es publicador puro, no recibe nada. El pulsador real aprieta y publica siempre, y es la app la que descarta lo que llega fuera de ventana.

### 30/09/2026

Definimos el hardware necesario para el proyecto y realizamos el pedido a la catedra

### 01/10/2026

Nos fue entregado el hardware y se realizó una demostracion presencial acerca del conexionado y las decisiones sobre el broker, que es quien toma las decisiones con respecto a los mensajes (no asi el pulsador).

### 05/10/2026

Se elaboro el informe de avance volcando todo lo realizado y adjuntado en la bitacora 

### 08/10/2026

Se mostro una demo de la aplicacion y simulacion en la clase presencial, se evaluaron distintos cambios en la base de datos y mejoras sobre el stack utilizado, tambien se acordo la elaboracion de un video que demuestre el funcionamiento de la app y la simulacion


### 08/10/2026

Después de hablar con el profesor sobre el desarrollo, investigamos cómo se estructuran habitualmente las aplicaciones de este tipo. Nos quedamos con el patrón de puertos y adaptadores, que se usa justamente cuando la parte valiosa y frágil del sistema —las reglas de juego y la máquina de estados— tiene que quedar aislada de todo lo que puede fallar: la red, el intermediario, el disco y el navegador. El objetivo concreto es que cuando lleguen los pulsadores reales, la aplicación ya esté probada por separado y los problemas que aparezcan sean de hardware y no nuestros.

### 10/10/2026

Escribimos el documento de reglas del proyecto, que fija el stack, las doce reglas que no se rompen y el estado de cada parte, de modo que cualquiera del equipo pueda tomar trabajo sin tener que reconstruir las conversaciones anteriores. En paralelo reprodujimos y corregimos un error que veníamos arrastrando: la aplicación descartaba votos como duplicados cuando un pulsador se reiniciaba. La causa es que el contador de secuencia del nodo vuelve a empezar en 1 al arrancar, y la aplicación lo interpretaba como el reenvío de un mensaje viejo, dejando a ese pulsador mudo por el resto de la sesión. Con hardware real se habría disparado ante cualquier reinicio por batería.

### 12/10/2026

Reestructuramos la aplicación separando el núcleo de reglas de la infraestructura. El cambio más importante no fue mover archivos sino sacar el reloj del núcleo: ahora el instante entra como parámetro en lugar de consultarse, y eso permite probar una partida de cinco preguntas de treinta segundos en milisegundos en vez de esperarla en tiempo real. Quedó una batería de sesenta y dos pruebas automatizadas que corre en menos de un segundo, incluida una que revisa los imports del núcleo y falla si alguien mete infraestructura ahí, para que la regla no dependa de que el equipo se acuerde.

### 13/10/2026

Revisamos el alcance de lo que faltaba de la aplicación y descartamos dos cosas que estaban planificadas. El sistema de migraciones de base de datos quedaba sin uso al no haber ningún cambio de esquema pendiente, y la recuperación de la partida ante una caída de la aplicación cuesta más mantener que volver a largar la ronda, que es lo que haría el coordinador igual. Dejamos documentados como decisiones los riesgos de red que decidimos no cerrar —la aplicación escucha en toda la red del aula y el intermediario no pide credenciales—, junto con el motivo y cómo se cerrarían, para no confundir más adelante una decisión tomada con un olvido.

### 14/10/2026

Implementamos la exportación de resultados a CSV, que era lo último que faltaba de la aplicación y estaba comprometido en el Plan de Proyecto. Se descarga desde el historial, una fila por pregunta con los votos de cada opción y el porcentaje de acierto, y por separado el podio en las ejecuciones competitivas. El formato está pensado para abrirse directo en una planilla en español, con punto y coma como separador y marca de codificación, porque de otro modo el archivo se abre apilado en una sola columna y con los acentos mal. Como el histórico guarda únicamente datos agregados, el archivo no puede contener el voto individual de nadie.

### 17/10/2026

Investigamos las bibliotecas de MQTT disponibles para el ESP8266, para cerrar la decisión que teníamos pendiente del contrato de mensajería. PubSubClient, que es la más difundida y la que aparece primero en cualquier tutorial, solo puede publicar en calidad de servicio 0: soporta QoS 1 para suscribirse pero no para publicar, decidimos usar arduino-mqtt de Joel Gaehwiler, que sí espera la confirmación de entrega del intermediario. Queda definida también la plataforma de desarrollo: NodeMCU 1.0 sobre el núcleo ESP8266 para Arduino.

### 20/10/2026

Investigamos cómo montar la Raspberry Pi como punto de acceso del aula y definimos el camino a seguir: hostapd para publicar la red inalámbrica y dnsmasq únicamente como servidor DHCP, sin DNS ni puerta de enlace, porque la red no tiene salida a internet y el intermediario se alcanza por una dirección IP fija. Encontramos que la versión del sistema operativo no es indistinta: desde Bookworm la gestión de red pasó a NetworkManager y ya no se lee dhcpcd.conf, que es lo que indica la mayoría de las guías, así que hay que desacoplar explícitamente la interfaz inalámbrica de NetworkManager para que hostapd pueda tomarla. Decidimos además fijar concesiones de dirección cortas, porque los pulsadores entran y salen de la red permanentemente y con los plazos por omisión la tabla se llenaría de entradas de equipos que ya no están.

### 21/10/2026

Cerramos la investigación de la Raspberry Pi y escribimos su configuración completa. La Pi cumple dos funciones: publica la red del aula y corre el intermediario Mosquitto; la aplicación sigue corriendo en la computadora del coordinador. Un único script de instalación copia los archivos de hostapd, dnsmasq, Mosquitto y NetworkManager, agrega la clave de la red en el momento (así no queda en el repositorio) y habilita los servicios, que recién toman efecto al reiniciar para no cortar la sesión remota a mitad de la instalación. Un servicio propio fija la dirección 192.168.4.1 en la interfaz inalámbrica antes de que arranquen hostapd y dnsmasq, con lo que queda resuelto el orden de arranque anotado el 15/09. Para la Zero W usamos Raspberry Pi OS Lite de 32 bits sobre Bookworm, porque no corre 64 bits y la versión siguiente maneja la red con otras herramientas contra las que el script no está probado; el script se niega a correr en otra versión.

### 22/10/2026

Escribimos el firmware del pulsador según el contrato de mensajería. Es publicador puro: lee los cuatro botones, publica el voto con QoS 1 y un número de secuencia, y manda un latido de presencia cada cinco segundos, con mensaje de última voluntad para que el intermediario avise si el nodo se cae. Los botones usan las resistencias internas del ESP8266 y un antirrebote de 50 ms por nivel sostenido, y van en D1, D2, D6 y D7, evitando los pines que el módulo consulta al arrancar. Un voto que no se pudo entregar se reintenta durante un segundo y medio y después se descarta: como el voto no lleva el número de pregunta, entregarlo tarde podría hacerlo caer en la pregunta siguiente. La clave del WiFi vive en un archivo aparte que no se versiona, igual que las credenciales de la Pi.

### 22/10/2026

El firmware compiló sin errores y se cargó en los NodeMCU, y la Raspberry Pi quedó instalada con el script. La Pi levanta la red del aula, los pulsadores se asocian, y con `mosquitto_sub -t 'aula/#' -v` se ven llegar al intermediario los latidos de presencia y los votos de cada botón con su opción y su número de secuencia.


