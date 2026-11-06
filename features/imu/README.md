# IMU compatibility

The walking policies read the trunk IMU's gyro and projected gravity every
control step (see [microduck-rl's DEPLOY.md](https://github.com/harrysungit/microduck-rl/blob/main/docs/DEPLOY.md)).
On an HD-1910 robot the IMU sits either on the servo bus as ID 200, or on the
main board's I²C. Which boards the runtime can read depends on how it
identifies them.

## Which boards work

Runtime: the HD-1910 build of robotd in
[fanhao375/Microduck-kissqy](https://github.com/fanhao375/Microduck-kissqy)
(`microduck-hd1910/firmware/duck-control/src/feetech.rs`, `identify_imu`), and
our branch of it (`components.toml`, component `robotd`).

| IMU | Bus protocol | How robotd identifies and reads it | Where it works | Tested by us |
|---|---|---|---|---|
| Feetech-protocol board at ID 200 (FT6 firmware, or fanhao375's own `imu_to_dxl` board) | Feetech | Feetech READ of the identity at address 0, then the IMU block in the servos' sync read | fanhao375's runtime | No |
| DXL2 board that answers READ | Dynamixel 2.0 | READ address 0, 3 bytes (model, firmware), then READ address 124, 12 bytes (gyro, then a quaternion) | fanhao375's runtime, `imu_protocol = "auto"` or `"dxl2"` | No |
| DXL2 board with seller firmware that rejects that READ (status 0x04, Data Range Error) | Dynamixel 2.0 | PING for the identity (it answers the same 3 bytes), then a single-ID SYNC_READ of address 124, 12 bytes | **Our branch only** | Yes: the probe below shows the pattern, and robotd's HOME check passes its IMU item |
| Qinmo board | Feetech, configured profile | PING, then the profile's own data layout; never probed as DXL2 | fanhao375's newer runtime, `imu_profile = "qinmo"` | No |
| I²C module on the main board (BNO085 or LSM6DSV16X) | I²C | Separate branch of fanhao375's runtime (`hd1910-v167-trunk-imu-i2c`) | fanhao375's branch | No |

Pollen's own robot uses its `imu_to_dxl` board on a Dynamixel bus with the
official runtime; that path is not for Feetech servos.

## Tools

Both are read-only.

- **[dxl2_imu_probe.py](dxl2_imu_probe.py)**: sends PING, READ 0/3, READ
  124/12 and SYNC_READ 124/12 to ID 200 once each and prints the answers. Run
  it first on an unknown DXL2 board: a board that answers READ works with the
  stock runtime; one that rejects READ but answers PING and SYNC_READ needs our
  branch. Needs pyserial and the bus to itself (robotd stopped).

  ```bash
  python3 features/imu/dxl2_imu_probe.py --port /dev/ttyS2
  ```

- **[imu_axis_check.py](imu_axis_check.py)**: on the robot, subscribes to
  robotd's `robot.state` stream over `/run/robotd.sock` and prints projected
  gravity, gyro and yaw while you tilt and turn the robot by hand. Checks the
  mounting (which way is forward, left, up) and the gyro scale against the
  IMU's own quaternion. No motion, nothing written.

  ```bash
  sudo python3 features/imu/imu_axis_check.py
  ```

A board can identify correctly and still be mounted rotated: run the axis
check before trusting any policy with it.
