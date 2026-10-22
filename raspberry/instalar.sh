#!/usr/bin/env bash
# Convierte una Raspberry Pi Zero W con Raspberry Pi OS Lite de 32 bits
# (Bookworm) en el punto de acceso y el broker del aula.
#
# Se corre una vez, con la Pi todavía conectada a una red con internet: apt
# necesita descargar los paquetes. Los cambios de red recién se aplican al
# reiniciar, así la sesión SSH no se corta a mitad de la instalación. Después
# del reinicio la Pi deja esa red y pasa a ser el punto de acceso.
#
# Uso:  sudo bash instalar.sh

set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PAIS="AR"

[ "$(id -u)" -eq 0 ] || { echo "Correlo con sudo." >&2; exit 1; }

# En Trixie el WiFi del Imager lo maneja netplan, y no está probado que la
# exclusión de wlan0 en NetworkManager le gane. Si pierde, la Pi queda sin
# red y sin forma de entrar por SSH.
. /etc/os-release
if [ "${VERSION_CODENAME:-}" != "bookworm" ]; then
  echo "Este script es para Bookworm y la Pi tiene ${VERSION_CODENAME:-otra versión}." >&2
  echo "Grabá «Raspberry Pi OS (Legacy, 32-bit) Lite»: ver raspberry/LEEME.md." >&2
  exit 1
fi

read -rp "Nombre de la red WiFi [ClickAula]: " SSID
SSID="${SSID:-ClickAula}"

while :; do
  read -rsp "Clave de la red (8 a 63 caracteres): " CLAVE; echo
  if [ ${#CLAVE} -ge 8 ] && [ ${#CLAVE} -le 63 ]; then break; fi
  echo "WPA2 exige entre 8 y 63 caracteres."
done

read -rp "Canal (1, 6 u 11) [6]: " CANAL
CANAL="${CANAL:-6}"
case "$CANAL" in
  1|6|11) ;;
  *) echo "Usá 1, 6 u 11: son los únicos canales de 2,4 GHz que no se pisan." >&2
     exit 1 ;;
esac

echo "==> Instalando paquetes"
apt-get update
apt-get install -y hostapd dnsmasq mosquitto mosquitto-clients

# apt arranca los servicios al instalarlos. Con la configuración de fábrica
# dnsmasq respondería DNS en la red de casa; se frenan hasta el reinicio.
systemctl stop hostapd dnsmasq mosquitto || true

echo "==> País de la radio"
# Sin país, Bookworm deja la radio bloqueada y hostapd no levanta.
raspi-config nonint do_wifi_country "$PAIS"

echo "==> Configuración"
install -m 644 "$DIR/networkmanager.conf" /etc/NetworkManager/conf.d/clickaula.conf
install -m 644 "$DIR/clickaula-ip.service" /etc/systemd/system/clickaula-ip.service
install -m 644 "$DIR/dnsmasq.conf"   /etc/dnsmasq.d/clickaula.conf
install -m 644 "$DIR/mosquitto.conf" /etc/mosquitto/conf.d/clickaula.conf

# La clave se agrega acá y no en el archivo del repositorio. Se escribe con
# printf y no con sed para que una clave con "/" o "&" no rompa nada.
{
  cat "$DIR/hostapd.conf"
  printf 'country_code=%s\n' "$PAIS"
  printf 'channel=%s\n' "$CANAL"
  printf 'ssid=%s\n' "$SSID"
  printf 'wpa_passphrase=%s\n' "$CLAVE"
} > /etc/hostapd/hostapd.conf
chmod 600 /etc/hostapd/hostapd.conf

echo "==> Servicios"
# Debian instala hostapd enmascarado hasta que haya una configuración.
systemctl unmask hostapd
systemctl daemon-reload
systemctl enable clickaula-ip hostapd dnsmasq mosquitto

cat <<FIN

Listo. Al reiniciar (sudo reboot) la Pi va a:
  - dejar de conectarse a esta red y la sesión SSH actual se pierde;
  - publicar la red "$SSID" en el canal $CANAL;
  - quedar en 192.168.4.1, con el broker en el puerto 1883.

Para volver a entrar: conectá el PC a "$SSID" y  ssh <usuario>@192.168.4.1
Para volver a la red de casa: ver raspberry/LEEME.md, "Deshacer".
FIN
