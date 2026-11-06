# microduck-software

[English](README.md) | [中文](README.zh.md)

Software for a [Microduck](https://github.com/pollen-robotics/microduck)
built with Feetech HD-1910 servos: training, the robot's runtime, IMU
compatibility and the Studio web console. The hardware (CAD, bill of
materials, assembly, electronics) is
[fanhao375/microduck-replica](https://github.com/fanhao375/microduck-replica)'s;
this project is the software side.

## Components

| Component | Repository | What |
|---|---|---|
| `rl` | [harrysungit/microduck-rl](https://github.com/harrysungit/microduck-rl) | Training on top of Pollen's microduck_rl: HD-1910 tasks, ROCm, acceptance gate, sim2sim |
| `robotd` | [harrysungit/Microduck-kissqy](https://github.com/harrysungit/Microduck-kissqy) | The robot's runtime: fanhao375's HD-1910 build of the official daemon, with our fixes on a branch |
| `studio` | [fanhao375/microduck-replica](https://github.com/fanhao375/microduck-replica) | Microduck Studio, the web console on the robot (`software/studio`) |
| this repository | | IMU compatibility, board bring-up, servo tools, and every feature that is not a change to one of the above |

[components.toml](components.toml) pins each one. Fetch them into
`components/` (partial clones, only the directories used):

```bash
python3 scripts/fetch.py
```

## From training to the robot

1. **Train** a skill with `rl` (or reproduce the five accepted ones with its
   training queue).
2. **Check** it: `rl`'s acceptance gate and sim2sim. A policy that does not
   pass both does not go on a robot.
3. **Export** the ONNX with Pollen's exporter; the interface is in
   [`rl`'s DEPLOY.md](https://github.com/harrysungit/microduck-rl/blob/main/docs/DEPLOY.md).
4. **Bring the board up** and put the runtime on it: [board/](board/README.md).
5. **Check the IMU**: which boards the runtime reads, and how it is mounted:
   [features/imu/](features/imu/README.md).
6. **Protect the servos** before the first powered run:
   [tools/hd1910_protection.py](tools/hd1910_protection.py) turns on their
   voltage and over-current unload conditions.
7. **Run** it from Studio.

A set of component versions that has run together on a robot becomes a
release in [releases/](releases/README.md). There is none yet: no policy from
this project has run on a robot.

## Layout

| Path | Contents |
|---|---|
| `components.toml`, `scripts/fetch.py` | The component repositories and how to fetch them |
| `releases/` | Component versions that have run together on a robot |
| `features/` | One directory per feature of our own; `features/imu/` so far |
| `board/` | Main board bring-up, USB networking, replacing robotd |
| `tools/` | Servo tools |
| `docs/` | Roadmap |
| `tests/` | `python -m pytest tests` (some tests need the fetched components) |

## Adding a feature

A new feature that is not a change to `rl`, `robotd` or Studio gets a
directory under `features/` with its own README (what it does, its status,
the hardware it needs), dependencies, tests and service files. Code shared by
features goes in `features/common/`. A change to a component's own code goes
to that component's repository, and upstream from there when it is general.

## License

Apache-2.0, see [LICENSE](LICENSE). The components carry their own licenses.
