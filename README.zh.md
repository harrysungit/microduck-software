# microduck-software

[English](README.md) | [中文](README.zh.md)

用飞特 HD-1910 舵机搭建的 [Microduck](https://github.com/pollen-robotics/microduck) 的软件：训练、机器人上的
运行时、IMU 兼容和 Studio 网页中控。硬件（CAD、物料清单、装配、电路）见
[fanhao375/microduck-replica](https://github.com/fanhao375/microduck-replica)；本项目是软件这一侧。

## 组件

| 组件 | 仓库 | 内容 |
|---|---|---|
| `rl` | [harrysungit/microduck-rl](https://github.com/harrysungit/microduck-rl) | 在 Pollen 的 microduck_rl 之上训练：HD-1910 任务、ROCm、验收门、sim2sim |
| `robotd` | [harrysungit/Microduck-kissqy](https://github.com/harrysungit/Microduck-kissqy) | 机器人上的运行时：fanhao375 为 HD-1910 构建的官方守护进程，我们的修复在一个分支上 |
| `studio` | [fanhao375/microduck-replica](https://github.com/fanhao375/microduck-replica) | Microduck Studio，机器人上的网页中控（`software/studio`） |
| 本仓库 | | IMU 兼容、主控板启动、舵机工具，以及所有不属于上面几个组件代码的功能 |

[components.toml](components.toml) 固定了每个组件的版本。把它们拉到 `components/` 下（部分克隆，只检出用到的目录）：

```bash
python3 scripts/fetch.py
```

## 从训练到机器人

1. **训练**：用 `rl` 训一个技能（或者用它的训练队列复现那五个验收通过的技能）。
2. **检查**：`rl` 的验收门和 sim2sim。两项没都过的策略不上机器人。
3. **导出**：用 Pollen 的导出脚本导出 ONNX；接口见 [`rl` 的 DEPLOY.md](https://github.com/harrysungit/microduck-rl/blob/main/docs/DEPLOY.md)。
4. **启动主控板**并装上运行时：[board/](board/README.md)。
5. **检查 IMU**：运行时能读哪些板子，装得方向对不对：[features/imu/](features/imu/README.md)。
6. **保护舵机**：第一次上电运行前，用 [tools/hd1910_protection.py](tools/hd1910_protection.py) 打开电压、过流等卸载保护。
7. 从 Studio **运行**。

在机器人上一起跑通过的一组组件版本，记成 [releases/](releases/README.md) 里的一个版本。目前还没有：本项目的策略还没在机器人上跑过。

## 目录

| 路径 | 内容 |
|---|---|
| `components.toml`、`scripts/fetch.py` | 组件仓库，以及怎么拉取 |
| `releases/` | 在机器人上一起跑通过的组件版本 |
| `features/` | 我们自己的功能，一个功能一个目录；目前有 `features/imu/` |
| `board/` | 主控板启动、USB 网络、替换 robotd |
| `tools/` | 舵机工具 |
| `docs/` | 路线图 |
| `tests/` | `python -m pytest tests`（部分测试需要先拉取组件） |

## 新增功能

不属于 `rl`、`robotd`、Studio 代码改动的新功能，在 `features/` 下建一个目录，自带 README（做什么、现状、需要什么硬件）、
依赖、测试和服务文件。功能之间共用的代码放 `features/common/`。改某个组件自身的代码，就提交到那个组件的仓库，
通用的再从那里提给上游。

## 许可

Apache-2.0，见 [LICENSE](LICENSE)。各组件适用各自的许可。
