#!/usr/bin/env bash
# Share a Linux host's internet connection with the Zero 3W over USB (ECM), using NetworkManager.
set -euo pipefail

matches=()
for net in /sys/class/net/*; do
  [[ -L "$net/device/driver" ]] || continue
  driver="$(basename "$(readlink -f "$net/device/driver")")"
  if [[ "$driver" == cdc_ether ]]; then matches+=("${net##*/}"); fi
done
if (( ${#matches[@]} != 1 )); then
  printf 'Expected one USB ECM interface; found %d.\n' "${#matches[@]}" >&2
  nmcli -t -f DEVICE,TYPE,STATE dev status >&2
  exit 1
fi
iface="${matches[0]}"
profile=microduck-zero3w-usb

if nmcli -t -f NAME con show | grep -Fxq "$profile"; then
  sudo nmcli con modify "$profile" connection.interface-name "$iface" \
    ipv4.method shared ipv4.addresses 192.168.77.1/24 ipv6.method disabled
else
  sudo nmcli con add type ethernet ifname "$iface" con-name "$profile" \
    ipv4.method shared ipv4.addresses 192.168.77.1/24 ipv6.method disabled
fi
sudo nmcli con up "$profile"
echo "Host USB interface: $iface"
ip -4 addr show dev "$iface"
echo 'Board address: 192.168.77.2; SSH after the board has connected: ssh root@192.168.77.2'
ping -c 2 -W 2 192.168.77.2 || true
