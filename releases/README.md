# Releases

A release is a set of component versions that has run together on a robot,
one file per release: `releases/<year>.<month>.<n>.toml`. Fetch one with
`python3 scripts/fetch.py --release releases/<file>.toml`.

```toml
version = "2026.12.0"
date = "2026-12-01"

[components.rl]
commit = "<sha>"

[components.robotd]
commit = "<sha>"
binary_sha256 = "<sha256 of the robotd that ran>"

[components.studio]
commit = "<sha>"

[[policies]]
skill = "walk"
task = "Mjlab-VelStand-Flat-MicroDuck-HD1910"
onnx_sha256 = "<sha256>"

[robot]
board = "Radxa Zero 3W V1.12J"
imu = "<board and firmware>"
checked = ["what was run on the robot, and where it is recorded"]
```

There is no release yet.
