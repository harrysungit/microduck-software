"""Read-only probe: which requests does a DXL 2.0 IMU board at ID 200 answer? Writes no register.

robotd's Feetech bus (fanhao375/Microduck-kissqy, `feetech.rs` `identify_imu`) identifies a DXL2
IMU with READ address 0, 3 bytes (model and firmware version), then reads its data with READ
address 124, 12 bytes. Some boards sold with their own firmware answer neither; the servo-web
DXL2 support in fanhao375/microduck-replica (PR #47) reads them with PING and a single-ID
SYNC_READ of address 124, 12 bytes. This probe sends each of the four requests once and prints
the answer, so you know which path a board needs.

Usage (needs pyserial):
  python3 dxl2_imu_probe.py --port /dev/cu.usbserial-XXXX      # a computer and a USB bus adapter
  python3 dxl2_imu_probe.py --port /dev/ttyS2                   # on the robot, with robotd stopped
Only one master may drive the bus: with an external adapter, unplug the HAT's bus connector or
make sure the robot's main program is stopped.
"""
import argparse
import struct
import sys
import time

HEADER = b"\xff\xff\xfd\x00"
PING, READ, SYNC_READ = 0x01, 0x02, 0x82
BROADCAST = 0xFE
ERRORS = {1: "Result Fail", 2: "Instruction Error", 3: "CRC Error", 4: "Data Range Error",
          5: "Data Length Error", 6: "Data Limit Error", 7: "Access Error"}


def crc16(data):
    crc = 0
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ (0x8005 if crc & 0x8000 else 0)) & 0xFFFF
    return crc


def packet(device_id, instruction, params=b""):
    body = (bytes([instruction]) + bytes(params)).replace(b"\xff\xff\xfd", b"\xff\xff\xfd\xfd")
    frame = HEADER + bytes([device_id]) + struct.pack("<H", len(body) + 2) + body
    return frame + struct.pack("<H", crc16(frame))


def parse_status(buf):
    """Return (id, error, params) of the first valid status packet in buf, or None."""
    start = buf.find(HEADER)
    while start >= 0:
        frame = buf[start:]
        if len(frame) >= 7:
            length = int.from_bytes(frame[5:7], "little")
            total = 7 + length
            if 4 <= length <= 1024 and len(frame) >= total:
                raw = frame[:total]
                if crc16(raw[:-2]) == int.from_bytes(raw[-2:], "little"):
                    body = raw[7:-2].replace(b"\xff\xff\xfd\xfd", b"\xff\xff\xfd")
                    if len(body) >= 2 and body[0] == 0x55:
                        return raw[4], body[1], bytes(body[2:])
        start = buf.find(HEADER, start + 1)
    return None


def transact(ser, tx, timeout=0.08):
    ser.reset_input_buffer()
    ser.write(tx)
    ser.flush()
    deadline = time.monotonic() + timeout
    buf = b""
    while time.monotonic() < deadline:
        buf += ser.read(256)
        if len(buf) > len(tx):           # a half-duplex adapter may echo the request first
            got = parse_status(buf[len(tx):] if buf.startswith(tx) else buf)
            if got:
                return got, buf
    got = parse_status(buf[len(tx):] if buf.startswith(tx) else buf)
    return got, buf


def describe(got):
    if not got:
        return "no answer (timeout)"
    sid, err, params = got
    if err & 0x7F:
        return f"ID {sid} status error 0x{err:02x} ({ERRORS.get(err & 0x7F, 'unknown')})"
    return f"ID {sid} answered, {len(params)} bytes: {params.hex(' ')}"


def self_test():
    """Dynamixel Protocol 2.0 e-Manual examples: PING to ID 1, and its status reply
    (model number 1030 = 0x0406, firmware version 38 = 0x26)."""
    assert packet(1, PING) == bytes.fromhex("fffffd0001030001194e"), packet(1, PING).hex()
    assert parse_status(bytes.fromhex("fffffd000107005500060426655d")) == (1, 0, b"\x06\x04\x26")


def main():
    ap = argparse.ArgumentParser(description="Read-only probe of a DXL2 IMU board at ID 200")
    ap.add_argument("--port", required=True)
    ap.add_argument("--baud", type=int, default=1_000_000)
    ap.add_argument("--id", type=int, default=200)
    a = ap.parse_args()
    self_test()
    import serial
    ser = serial.Serial(a.port, a.baud, timeout=0.005)
    tests = [
        ("PING", packet(a.id, PING)),
        ("READ address 0, 3 bytes (robotd's identity)", packet(a.id, READ, struct.pack("<HH", 0, 3))),
        ("READ address 124, 12 bytes (robotd's data)", packet(a.id, READ, struct.pack("<HH", 124, 12))),
        ("SYNC_READ address 124, 12 bytes (servo-web's data)",
         packet(BROADCAST, SYNC_READ, struct.pack("<HH", 124, 12) + bytes([a.id]))),
    ]
    for name, tx in tests:
        got, raw = transact(ser, tx)
        print(f"{name:<52} -> {describe(got)}")
        time.sleep(0.05)
    ser.close()


if __name__ == "__main__":
    sys.exit(main())
