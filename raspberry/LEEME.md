# Raspberry Pi Zero W — punto de acceso y broker

La Pi hace dos cosas y nada más: publica la red WiFi del aula y corre
Mosquitto. No corre la aplicación ni Docker; todo va instalado con `apt`.

| Archivo | Va a parar a |
|---|---|
| `hostapd.conf` | `/etc/hostapd/hostapd.conf`, con red, canal y clave agregados |
| `dnsmasq.conf` | `/etc/dnsmasq.d/clickaula.conf` |
| `mosquitto.conf` | `/etc/mosquitto/conf.d/clickaula.conf` |
| `networkmanager.conf` | `/etc/NetworkManager/conf.d/clickaula.conf` |
| `clickaula-ip.service` | `/etc/systemd/system/` — pone 192.168.4.1 en `wlan0` |
| `instalar.sh` | copia todo lo anterior y habilita los servicios |

## 1. Preparar la tarjeta

Con Raspberry Pi Imager: **Raspberry Pi OS (other) → Raspberry Pi OS
(Legacy, 32-bit) Lite**, que es la de Debian Bookworm. La Zero W no corre 64
bits. La opción que el Imager ofrece primero ya es Trixie: con ella el WiFi de
casa lo configuran cloud-init y netplan, e `instalar.sh` no está probado contra
eso. El script se niega a correr si no es Bookworm.

En la configuración avanzada del Imager (Raspberry Pi Connect, apagado: en el
aula no hay internet):

- nombre de la máquina: **`clickaula`**;
- usuario **`clickaula`**. La contraseña no va en el repositorio: está en
  `raspberry/credenciales.md`, que no se versiona;
- la red WiFi **de casa**, que hace falta una sola vez para que `apt` baje los
  paquetes;
- SSH habilitado;
- país de la red inalámbrica: AR.

## 2. Instalar

Desde el PC, con la Pi encendida y en la red de casa:

```bash
scp -r raspberry clickaula@clickaula.local:
ssh clickaula@clickaula.local
sudo bash raspberry/instalar.sh
sudo reboot
```

El script pregunta el nombre de la red, la clave y el canal. La clave tiene
que ser la misma que después va en `firmware/pulsador/secretos.h`.

Nada cambia hasta el reinicio. Después del reinicio la Pi ya no está en la
red de casa: para volver a entrar, conectá el PC a la red del aula y
`ssh clickaula@192.168.4.1`.

## 3. Verificar

Desde la Pi:

```bash
systemctl status clickaula-ip hostapd dnsmasq mosquitto
iw dev wlan0 info                       # tiene que decir "type AP"
mosquitto_sub -t 'aula/#' -v            # el tráfico de los pulsadores
iw dev wlan0 station dump | grep -c Station   # cuántos están asociados
```

## 4. Deshacer, para volver a la red de casa

Hace falta, por ejemplo, para actualizar paquetes:

```bash
sudo systemctl disable hostapd dnsmasq clickaula-ip
sudo rm /etc/NetworkManager/conf.d/clickaula.conf
sudo reboot
```

Para volver al modo aula: `sudo bash raspberry/instalar.sh` de nuevo.
