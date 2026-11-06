"""HD-1910 servo protection: show it, and optionally turn on the voltage, overheat and over-current unload conditions.

Read-only by default: PING each servo and print register 19 (unload conditions), 20 (LED alarm
conditions), 65 (current status), 13 (temperature limit), 14/15 (voltage limits) and 55 (lock).
--apply writes: register 19 only (also 20 with --led), adding BIT0 voltage, BIT2 overheat and BIT3
over-current (13 together) to the value already there; other bits stay as they are. The EEPROM
lock (55) is opened before the write and closed after it, then the value is read back.

Bits from the HD-1910 memory table (fanhao375/microduck-replica,
tools/FeeTech_HD1910M_Servo/src/registers.rs): BIT0 voltage, BIT1 magnetic encoder, BIT2
overheat, BIT3 over-current; 1 turns a condition on. fanhao375/microduck-replica reports a
factory value of 4 (overheat only), and a servo that burned out with over-current and voltage
protection off.

Needs pyserial and the `feetech` bus module of Microduck Studio: run `python3 scripts/fetch.py`
first (it is then found under components/studio/), or put feetech.py next to this file.

  python3 tools/hd1910_protection.py --port /dev/cu.usbserial-XXXX            # show
  python3 tools/hd1910_protection.py --port /dev/cu.usbserial-XXXX --apply    # turn the three on

Only one master may drive the bus: close Studio and anything else holding the port, and stop the
robot's main program (or unplug the HAT's bus connector). After --apply, power-cycle and run again
without it to check the setting survived.
"""
import argparse
import sys
from pathlib import Path

STUDIO = Path(__file__).resolve().parents[1] / "components/studio/software/studio"
if (STUDIO / "studio/bus/feetech.py").is_file():
    sys.path.insert(0, str(STUDIO))
    from studio.bus import feetech  # noqa: E402
else:
    import feetech  # noqa: E402  # feetech.py next to this file

WANT = 1 | 4 | 8            # 13: voltage + overheat + over-current
BITS = {1: "voltage", 2: "encoder", 4: "overheat", 8: "over-current"}
UNLOAD, LED_ALARM, STATUS, LOCK = 19, 20, 65, 55


def bits_text(v):
    on = [name for bit, name in BITS.items() if v & bit]
    if v & ~0x0F:
        on.append(f"other bits {v & ~0x0F}")
    return ", ".join(on) if on else "none"


def parse_ids(text):
    ids = []
    for part in text.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            ids.extend(range(int(a), int(b) + 1))
        elif part:
            ids.append(int(part))
    return ids


def read_row(bus, sid):
    return {
        "unload": bus.read_u8(sid, UNLOAD),
        "led": bus.read_u8(sid, LED_ALARM),
        "status": bus.read_u8(sid, STATUS),
        "max_temp": bus.read_u8(sid, 13),
        "max_v": bus.read_u8(sid, 14) / 10,
        "min_v": bus.read_u8(sid, 15) / 10,
        "lock": bus.read_u8(sid, LOCK),
    }


def write_eeprom_u8(bus, sid, addr, value):
    """Unlock, write, lock again; return the value read back. The lock is in finally, so a failed write still relocks."""
    bus.unlock(sid)
    try:
        bus.write_u8(sid, addr, value)
    finally:
        bus.lock(sid)
    return bus.read_u8(sid, addr)


def check_one(bus, sid, apply, led):
    """Handle one servo; return its number of problems."""
    if bus.ping(sid) is None:
        print(f"#{sid:<3} no answer: not powered, not connected, or a different ID")
        return 1
    row = read_row(bus, sid)
    missing = [BITS[b] for b in (1, 4, 8) if not row["unload"] & b]
    print(f"#{sid:<3} unload 19 = {row['unload']:>3} ({bits_text(row['unload'])})"
          f"  LED 20 = {row['led']:>3} ({bits_text(row['led'])})"
          f"  status 65 = {row['status']} ({bits_text(row['status'])})"
          f"  max {row['max_temp']} °C  {row['min_v']:.1f}-{row['max_v']:.1f} V"
          + (f"  <- off: {', '.join(missing)}" if missing else ""))
    if row["lock"] != 1:
        print(f"     note: lock 55 = {row['lock']}, factory value is 1")
    if not apply:
        return 1 if missing else 0
    problems = 0
    targets = [(UNLOAD, row["unload"])] + ([(LED_ALARM, row["led"])] if led else [])
    for addr, cur in targets:
        new = cur | WANT
        if new == cur:
            continue
        got = write_eeprom_u8(bus, sid, addr, new)
        lock = bus.read_u8(sid, LOCK)
        ok = got == new and lock == 1
        problems += 0 if ok else 1
        print(f"     write {addr}: {cur} -> {new}, read back {got}, lock {lock}  {'OK' if ok else 'FAILED'}")
    return problems


def main(argv=None, bus=None):
    ap = argparse.ArgumentParser(description="HD-1910 servo protection (read-only by default)")
    ap.add_argument("--port", help="serial port, e.g. /dev/cu.usbserial-XXXX, COM5, /dev/ttyS2")
    ap.add_argument("--baud", type=int, default=1_000_000)
    ap.add_argument("--ids", default="10-14,20-24,30-34")
    ap.add_argument("--apply", action="store_true", help="add the voltage, overheat and over-current bits to register 19, kept across power cycles")
    ap.add_argument("--led", action="store_true", help="with --apply: add the same three bits to the LED alarm, register 20")
    a = ap.parse_args(argv)
    if a.led and not a.apply:
        ap.error("--led needs --apply")
    if bus is None:
        if not a.port:
            ap.error("--port is required")
        bus = feetech.FeetechBus(a.port, a.baud)
    problems = 0
    for sid in parse_ids(a.ids):
        try:
            problems += check_one(bus, sid, a.apply, a.led)
        except feetech.BusError as e:
            print(f"#{sid:<3} bus error: {type(e).__name__}: {e}")
            problems += 1
    if a.apply:
        print("Done: power-cycle, then run again without --apply to check the setting survived." if not problems
              else f"{problems} write(s) did not succeed; see the lines marked FAILED or no answer.")
    else:
        print("All three protections are on." if not problems
              else f"{problems} servo(s) without all three, or not answering. Add --apply to turn them on.")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
