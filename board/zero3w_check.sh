#!/usr/bin/env bash
# Read-only Radxa Zero 3W V1.12J bring-up checks for the Armbian vendor-kernel images. Run on the board.
set -u

warnings=0
pass() { printf '[PASS] %s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*"; warnings=$((warnings + 1)); }
info() { printf '[INFO] %s\n' "$*"; }

printf 'Zero 3W V1.12J board check\n'
printf 'Host: %s\n\n' "$(hostname)"

kernel="$(uname -r)"
if [[ "$kernel" == 6.1.115-vendor-rk35xx ]]; then
  pass "Kernel: $kernel"
else
  warn "Unexpected kernel: $kernel"
fi

if [[ -r /proc/device-tree/compatible ]]; then
  compatible="$(tr '\0' '\n' </proc/device-tree/compatible)"
  if [[ "$compatible" == *radxa,zero3w-aic8800ds2* ]]; then
    pass 'V1.12J AIC8800DS2 device tree'
  else
    warn "Device tree does not identify AIC8800DS2: ${compatible//$'\n'/, }"
  fi
else
  warn 'Device-tree compatible property is unavailable'
fi

root_source="$(findmnt -n -o SOURCE / 2>/dev/null || true)"
root_type="$(findmnt -n -o FSTYPE / 2>/dev/null || true)"
root_size="$(df -h / 2>/dev/null | awk 'NR==2 {print $2}')"
info "Root: ${root_source:-unknown} ${root_type:-unknown}, size ${root_size:-unknown}"
if [[ "$root_source" == /dev/mmcblk* && "$root_type" == ext4 ]]; then
  pass 'Root filesystem is on microSD'
else
  warn 'Root filesystem is not the expected microSD ext4 partition'
fi

if [[ -c /dev/ttyGS0 ]]; then
  pass 'USB gadget serial /dev/ttyGS0 is present'
else
  warn 'USB gadget serial /dev/ttyGS0 is missing'
fi

if [[ -c /dev/ttyS2 ]]; then
  pass 'Servo UART /dev/ttyS2 is present'
  if (( EUID != 0 )); then
    warn 'Run the script as root to check all UART process owners'
  elif command -v fuser >/dev/null 2>&1; then
    occupants="$(fuser /dev/ttyS2 2>/dev/null || true)"
    if [[ -z "$occupants" ]]; then
      pass 'Servo UART has no process owner'
    else
      warn "Servo UART is held by PID(s): $occupants"
    fi
  else
    warn 'fuser is unavailable; UART occupancy not checked'
  fi
else
  warn 'Servo UART /dev/ttyS2 is missing'
fi

cmdline="$(cat /proc/cmdline 2>/dev/null || true)"
if [[ "$cmdline" == *console=ttyS2* || "$cmdline" == *console=ttyFIQ0* ]]; then
  warn "Kernel console occupies the servo UART: $cmdline"
else
  pass 'Kernel command line does not claim ttyS2 or ttyFIQ0'
fi

for port in ttyS2 ttyFIQ0; do
  state="$(systemctl is-enabled "serial-getty@${port}.service" 2>/dev/null || true)"
  if [[ "$state" == masked ]]; then
    pass "serial-getty@${port} is masked"
  else
    warn "serial-getty@${port} state: ${state:-unknown}"
  fi
done

if ip link show wlan0 >/dev/null 2>&1; then
  info 'Wi-Fi interface wlan0 is detected (connection not tested)'
else
  info 'Wi-Fi interface wlan0 is absent; optional for serial-only setup'
fi

printf '\nWarnings: %d\n' "$warnings"
printf 'SSH, HAT, servos, IMU, ToF and camera were not tested.\n'
exit 0
