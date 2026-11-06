#!/bin/sh
# Temporarily switch Zero 3W from g_serial to g_cdc (USB ACM serial + ECM net).
# A reboot restores g_serial from the existing modules-load configuration.
set -eu

[ "$(id -u)" -eq 0 ] || { echo 'Run as root.' >&2; exit 1; }
[ -c /dev/ttyGS0 ] || { echo 'USB serial gadget is not active.' >&2; exit 1; }
modinfo g_cdc >/dev/null || { echo 'g_cdc module is missing.' >&2; exit 1; }

cat > /etc/systemd/network/30-microduck-usb0.network <<'NETWORK'
[Match]
Name=usb0

[Network]
Address=192.168.77.2/24
Gateway=192.168.77.1
DNS=192.168.77.1
NETWORK
chmod 644 /etc/systemd/network/30-microduck-usb0.network
systemctl enable --now systemd-networkd
networkctl reload

cat > /usr/local/sbin/microduck-usb-gadget-switch <<'SWITCH'
#!/bin/sh
set -u
exec >>/var/log/microduck-usb-gadget-switch.log 2>&1
echo "Starting USB ACM+ECM switch at $(date -Is)"
systemctl stop serial-getty@ttyGS0.service || true
sleep 1
if ! modprobe -r g_serial; then
    echo 'Could not unload g_serial; leaving the original gadget.'
    systemctl start serial-getty@ttyGS0.service || true
    exit 1
fi
if modprobe g_cdc host_addr=02:6d:69:63:72:01 dev_addr=02:6d:69:63:72:02; then
    udevadm settle || true
    systemctl start serial-getty@ttyGS0.service || true
    echo 'g_cdc loaded. USB serial and usb0 should now be available.'
    exit 0
fi
echo 'g_cdc failed; restoring g_serial.'
modprobe g_serial || true
udevadm settle || true
systemctl start serial-getty@ttyGS0.service || true
exit 1
SWITCH
chmod 755 /usr/local/sbin/microduck-usb-gadget-switch

echo 'Switch scheduled in 5 seconds. USB serial will disconnect and reconnect.'
echo 'If the new gadget does not appear, reboot to restore the original g_serial setup.'
systemd-run --on-active=5s --unit=microduck-usb-gadget-switch \
    /usr/local/sbin/microduck-usb-gadget-switch
