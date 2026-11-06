# Board

The robot's main board is a Radxa Zero 3W. These notes and scripts cover
bringing it up and putting a runtime on it.

## System image

Start from [fanhao375/microduck-replica](https://github.com/fanhao375/microduck-replica)'s
released image, which carries the HD-1910 runtime, Studio and the updater.
It is built for the Zero 3W V1.12 (Wi-Fi chip AIC8800D80). On a **V1.12J**
board (AIC8800DS2) it needs four changes, which we made and booted:

1. The Radxa B1 bootloader in sectors 64–32767.
2. The device tree `rk3566-radxa-zero-3w-aic8800ds2.dtb`, with `fdt` in
   `/boot/extlinux/extlinux.conf` pointing at it.
3. `rk3568-dwc3-peripheral.dtbo` added to `fdtoverlays`, so the USB-C port
   works as a device.
4. Optionally, a USB network fallback: `g_cdc` at boot, `usb0` at
   192.168.77.2/24, a login on the USB serial port.

The scripts that apply these to a released image are not in this repository
yet; see the [roadmap](../docs/ROADMAP.md).

## Scripts

| Script | Where | What |
|---|---|---|
| [zero3w_check.sh](zero3w_check.sh) | board | Read-only bring-up checks: vendor kernel, V1.12J device tree, root on the SD card, USB gadget, the servo bus `/dev/ttyS2` free and without a console on it |
| [usb_network_board.sh](usb_network_board.sh) | board, as root | Switch the USB gadget from serial only to serial plus network (ECM) until the next reboot |
| [usb_network_host.sh](usb_network_host.sh) | Linux host | Share the host's internet connection with the board over that USB link (NetworkManager) |

## Replacing robotd

To run a robotd built from our branch (component `robotd` in
[components.toml](../components.toml)) on a robot that already has the
image's runtime. Lay the robot down or hold it: the servos go limp while
robotd restarts.

```bash
# on the robot, with the new binary copied to /tmp/robotd
R=/opt/robot/feetech-ft5-r5/robotd
sudo cp -p "$R" "$R.before"                                   # keep the one that was there
sudo install -o root -g root -m 0755 /tmp/robotd "$R"
sha256sum "$R"                                                # compare with the build's
sudo systemctl restart robotd
journalctl -u robotd -b | grep -E "IMU|DXL2|turns away"       # what it found at start
```

Roll back with `sudo cp "$R.before" "$R"` and a restart. The path is the one
the image's `robotd.service` override starts; check yours with
`systemctl cat robotd`.
