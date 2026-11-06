#!/usr/bin/env python3
"""Read-only check of what the walking policy sees from the trunk IMU. Run it on the duck.

It only subscribes to robotd's `robot.state` stream: no motion, nothing written. Relax the robot
(relax the motors, e.g. from Studio), hold it in your hands, run

    sudo python3 imu_axis_check.py

and tilt the robot as below. robotd's trunk frame is x forward, y left, z up; the projected
gravity g leans toward whichever side is lower:

    upright              g ≈ ( 0.00,  0.00, -1.00)
    nose down 30°        g ≈ (+0.50,  0.00, -0.87)
    nose up 30°          g ≈ (-0.50,  0.00, -0.87)
    left side down 30°   g ≈ ( 0.00, +0.50, -0.87)
    right side down 30°  g ≈ ( 0.00, -0.50, -0.87)

Gyro (rad/s) while moving: nose going down → +y; turning left, seen from above → +z; right
side going down → +x.

The yaw columns compare the turn since start, upright on a table: the gyro integrated here
against the IMU's own quaternion. Turn the robot about 90° left and back; the two should agree
within about 10%. A steady ratio such as 4x or 0.25x means the gyro is scaled wrong.
"""
import argparse
import json
import math
import socket
import time


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def yaw_of(q):
    w, x, y, z = q
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--socket", default="/run/robotd.sock")
    ap.add_argument("--seconds", type=float, default=60.0, help="how long to run (default 60)")
    args = ap.parse_args()

    sock = socket.socket(socket.AF_UNIX)
    sock.settimeout(2.0)
    sock.connect(args.socket)
    reader = sock.makefile("rb")
    # Every tick (no "hz"): the yaw integration needs each gyro sample.
    request = {"jsonrpc": "2.0", "id": 1, "method": "robot.subscribe", "params": {}}
    sock.sendall((json.dumps(request) + "\n").encode())

    print("    t   gx    gy    gz  |  gyro x  y     z    | yaw gyro° quat° | loop Hz missed fallen")
    start = time.monotonic()
    last_t = last_yaw = None
    yaw_gyro = yaw_quat = 0.0
    peak = [0.0, 0.0, 0.0]
    missed0 = None
    polls = shown = 0
    stop = None
    while time.monotonic() - start < args.seconds:
        try:
            line = reader.readline(4 << 20)
        except socket.timeout:
            stop = "no robot.state from robotd for 2 s; is its control loop running?"
            break
        if not line:
            stop = "robotd closed the connection"
            break
        msg = json.loads(line)
        if msg.get("id") == 1:
            if msg.get("error"):
                raise SystemExit(f"robot.subscribe refused: {msg['error']}")
            continue
        if msg.get("method") != "robot.state":
            continue
        polls += 1
        s = msg.get("params") or {}
        imu = s.get("imu")
        safety = s.get("safety") or {}
        loop = s.get("control_loop") or {}
        if missed0 is None:
            missed0 = loop.get("missed", 0)
        if not imu:
            if polls % 50 == 1:
                print("no IMU data in robot.state yet (imu is null)")
            continue
        t, gyro, quat = s.get("t", 0.0), imu["gyro"], imu["quat"]
        if last_t is not None and t > last_t:
            yaw_gyro += gyro[2] * (t - last_t)
            yaw = yaw_of(quat)
            yaw_quat += wrap(yaw - last_yaw)
            last_yaw = yaw
        elif last_t is None:
            last_yaw = yaw_of(quat)
        last_t = t
        peak = [max(p, abs(v)) for p, v in zip(peak, gyro)]
        if time.monotonic() - start >= shown * 0.2:
            shown += 1
            g = safety.get("gravity", [float("nan")] * 3)
            print(f"{time.monotonic() - start:5.1f} {g[0]:+.2f} {g[1]:+.2f} {g[2]:+.2f} | "
                  f"{gyro[0]:+5.2f} {gyro[1]:+5.2f} {gyro[2]:+5.2f} | "
                  f"{math.degrees(yaw_gyro):+7.1f} {math.degrees(yaw_quat):+6.1f} | "
                  f"{loop.get('hz', 0):5.1f} {loop.get('missed', 0) - missed0:5d} "
                  f"{safety.get('fallen')}", flush=True)
    if stop:
        print(stop)
    elapsed = time.monotonic() - start
    print(f"done: {polls} states in {elapsed:.0f} s; peak |gyro| x/y/z = "
          f"{peak[0]:.2f}/{peak[1]:.2f}/{peak[2]:.2f} rad/s; yaw gyro {math.degrees(yaw_gyro):+.1f}° "
          f"vs quaternion {math.degrees(yaw_quat):+.1f}°")


if __name__ == "__main__":
    main()
