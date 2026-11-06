# Roadmap

Each item says what "done" means. Training has its own roadmap in
[microduck-rl](https://github.com/harrysungit/microduck-rl/blob/main/docs/ROADMAP.md).

## Runtime

- [ ] **Our robotd fixes on fanhao375's current release.** The branch in
  `components.toml` is based on fanhao375's 20261027 runtime; fanhao375 has
  released a newer one since (control.48). Done: the fixes rebased onto it,
  the DXL2 fallback kept only where the new code does not already read seller
  firmware, the tests passing, and the changes proposed to fanhao375.
- [ ] **First powered run.** Done: robotd from our branch drives all 15
  HD-1910 servos and the IMU on the robot, `zero3w_check.sh` and the IMU axis
  check pass, recorded.

## Board

- [ ] **V1.12J image scripts.** Done: a script that turns a released
  fanhao375 image into a V1.12J one (the four changes in
  [board/README.md](../board/README.md)), checking the result without root.

## Studio

- [ ] **Studio changes.** None yet. Done for each: a branch of
  harrysungit/microduck-replica, a pull request to fanhao375, and
  `components.toml` pointing at it until it is merged.

## Features

- [ ] **`features/common/`**: a client for robotd's local socket
  (`/run/robotd.sock`, the JSON-RPC stream `imu_axis_check.py` already reads)
  that features use to read state and send commands. Done: used by the first
  feature that commands the robot.

## Releases

- [ ] **First release.** Done: `releases/` names the components that ran a
  skill on the robot, with what was checked.
