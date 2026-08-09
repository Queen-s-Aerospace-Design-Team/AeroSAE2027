# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

QADT (Queen's Aerospace Design Team) AeroSAE 2027 software monorepo: drone autonomy on PX4 + ROS 2 Jazzy, perception (ZED stereo camera), hardware control (gimbal/water-release payload), a Google Drive upload service, and Gazebo simulation assets. Everything is built and run inside a Docker dev container — there is no supported host-native build.

## Development environment

- All development happens inside the VSCode **Dev Container** (`.devcontainer/`). Open the repo in VSCode and "Reopen in Container"; do not try to build the ROS workspace on the bare host.
- `.devcontainer/initialize.sh` runs before the container starts: it detects the host platform (linux-NVIDIA / linux-nonNVIDIA / macos / wsl) and copies the matching `.devcontainer/compose.<profile>.yml` to `compose.active.yml` (gitignored), which `devcontainer.json` composes together with `compose.base.yml`. This is a one-time file *copy*, not a symlink — if you edit a `compose.<profile>.yml`, rerun `initialize.sh` (or re-trigger "Reopen in Container") to regenerate `compose.active.yml`, or your edits silently won't take effect.
- On the Linux profiles, `initialize.sh` requires a working X11 display for GUI passthrough (Gazebo, rviz2, etc.), but accepts XWayland too: it checks for either `XDG_SESSION_TYPE=x11` or a live socket at `/tmp/.X11-unix/X<N>`, so Wayland-default hosts (e.g. Ubuntu 24.04+ GNOME) work as long as XWayland is running.
- `.devcontainer/postStart.sh` starts the Micro XRCE-DDS Agent (`MicroXRCEAgent udp4 -p 8888`) needed for PX4 ↔ ROS 2 communication.
- `./scripts/manualCompose.sh` brings the devcontainer up/down from the terminal (runs `initialize.sh`, `docker compose up -d`, execs a shell) as an alternative to VSCode's "Reopen in Container".
- Editor: format-on-save with `clang-format` is enabled for C/C++ inside the container; Python paths are pointed at `/opt/ros/jazzy/...`, the built `px4_msgs` install, and `ros_ws/src`.

## Common commands

```bash
# Build the ROS 2 workspace (inside devcontainer)
cd ros_ws
source /opt/ros/jazzy/setup.bash
colcon build
source install/setup.bash

# Build/test a single package
colcon build --packages-select <package_name>
colcon test --packages-select <package_name>
colcon test-result --verbose

# Format all C/C++ sources under ros_ws/src (uses repo .clang-format)
./scripts/format-all.sh

# Launch QGroundControl
./scripts/launchQGC.sh

# PX4 SITL + Gazebo + ros_gz bridge + rviz2 dev simulation (tmux, 4 panes)
# requires PX4-Autopilot checked out at ~/PX4-Autopilot
./scripts/simulateDepth.sh      # walls world, gz_x500_depth_walls target
./scripts/simulateTask2.sh      # custom world at gz_worlds/aeac

# Standalone (non-ROS) perception pipeline tests
cd perception/zed-positional-measurement
pytest                          # all tests
pytest tests/test_pipeline.py::test_name   # single test

# Field/production deployment (outside the devcontainer, on the robot)
./scripts/deploy.sh up            # start all deployment services
./scripts/deploy.sh up mission    # start just one target
./scripts/deploy.sh logs perception
./scripts/deploy.sh attach mission
./scripts/deploy.sh down
# targets: all | mission | perception | drive | uxrce | hardware
```

Python ROS packages (`navigation_core`, `hardware_controllers`, `google_drive`) each carry an `ament_python`-style `test/` folder (`test_flake8.py`, `test_pep257.py`, `test_copyright.py`) run through `colcon test`, not directly via pytest.

**If the repo (or its devcontainer mount path) is ever renamed again** — e.g. next year's inevitable sequel to the `AEAC2026` → `AeroSAE2027` rename — `colcon build` will fail with a `CMake Error: ... is different than the directory ... where CMakeCache.txt was created`. CMake bakes the absolute source/build path into `ros_ws/build/*/CMakeCache.txt` the first time it configures, and refuses to reuse a cache pointing at a path that no longer exists. Fix with a one-time clean rebuild — safe, since these are pure generated output:
```bash
cd ros_ws
rm -rf build install log
colcon build --symlink-install
```
Don't do this preemptively on every build/container rebuild — it defeats colcon's incremental build caching and PX4-related packages (`px4_msgs`, `px4_ros_com`, `flight_missions`) are slow to compile from scratch. Only needed once, right after a path change.

## Architecture

### `ros_ws/src/` — ROS 2 Jazzy workspace (colcon)

- **`flight_missions`** (C++, `ament_cmake`): the PX4 offboard-control mission framework.
  - `mission_core`: `Mission` base class (`mission.hpp`/`.cpp`) — a ROS 2 `Node` that implements the shared arm/offboard/land/RTL state machine (`FSM`), publishes `OffboardControlMode`/`TrajectorySetpoint`/`VehicleCommand` on the `/fmu/in/...` topics, and calls the `/fmu/vehicle_command` service. Concrete missions subclass it and override `onMissionObjectiveStart()` / `publishMissionSetpoint()` / `onMissionFinished()`.
  - `mission_nodes`: concrete missions built on `Mission` — `orbit_location`, `return_to_origin`, `return_to_origin_v2`. Each is its own executable (see `compose.mission.yml` for how one gets launched: `ros2 run flight_missions orbit_location`).
- **`navigation_core`** (Python): bridges `cmd_vel`-style commands to PX4 setpoints (`cmd_vel_to_px4.py`), plus a test node (`cmd_vel_test.py`).
- **`hardware_controllers`** (Python): `gimbal_controller` node — drives the payload gimbal PWM and the water-release GPIO. Deployed with explicit pin params (see `deployment/compose.hardware.yml`).
- **`google_drive`** / **`google_drive_interfaces`**: `drive_uploader` node + `DriveUploader.srv` for uploading captured media to Google Drive. OAuth client config lives in `.credentials/credentials.json`; `token.json` is produced by `generate_token.py` and is gitignored.
- **`pubsub_01`**: minimal ROS 2 pub/sub example package (not part of the mission stack).
- **`px4_msgs`**, **`px4_ros_com`**: vendored, unmodified upstream PX4 packages (message/service definitions and the ROS 2 bridge library). Treat as third-party — if PX4 message defs need updating, follow the sync procedure in `px4_msgs/README.md` rather than hand-editing.

All packages communicate with PX4 over the standard `/fmu/in/*` and `/fmu/out/*` uXRCE-DDS topics/services exposed by the Micro XRCE-DDS Agent started in `postStart.sh`.

### `perception/` — computer vision, mostly outside the ROS workspace

- Top-level scripts (`record_svo.py`, `validate_svo.py`, `extract_training_frames.py`, `upload_to_roboflow.py`, `circle_processing.py`) are standalone ZED/SVO tooling; `circle_processing.py` does DBSCAN clustering of detected paper targets (`min_samples=5` — a target needs ≥5 frame observations to survive as a cluster).
- **`zed-positional-measurement/`** is a self-contained Python subproject (`src/zed_positional_measurement/`: `pipeline.py`, `sdk.py`, `config.py`, `metrics.py`, `storage.py`, `exporters.py`, `geometry.py`, `cli.py`) with its own `tests/` (pytest) — not built or run through colcon. Its `docs/` folder is the source of truth for architecture; **read in this order**: `PRD.md` → `Technical.md` → `Operations.md` → `Schema.md` → `LucasHandoff.md` → `Uncertainties.md` → `Validation.md`. Note per `docs/README.md`: the docs describe an intended **live-first** architecture, but the current runtime is still **replay-first** — don't assume the two match.
- `docs/issues.md` and `docs/learnings.md` track known perf caveats (e.g. per-frame plane queries, unused `mask_pixels` computation) and Jetson-specific operational notes (the `nvargus-daemon` / `zed_x_daemon` services that back the ZED X cameras and how to restart them after a bad camera-handoff state).

### `gz_worlds/` — Gazebo simulation

SDF world file(s) plus `generate_world.py` to produce them; consumed by the `scripts/simulate*.sh` tmux harnesses.

### Deployment vs. devcontainer compose files

Two separate Docker Compose stacks exist and should not be confused:
- `.devcontainer/compose.*.yml` — the **development** container (VSCode Dev Containers).
- `deployment/compose.*.yml` — **production** containers run on the robot, one per node/service (`mission`, `perception`, `drive`, `uxrce`, `hardware-controller`), all extending the shared `base`/`base_with_gpu` service in `compose.deployment.yml` and pulling `ghcr.io/queen-s-aerospace-design-team/deployment-px4`. `scripts/deploy.sh` is the entry point for managing these (see `--help` in the script for the full command/target matrix).

## C++ style

`.clang-format` at the repo root (LLVM-based) governs all C/C++ under `ros_ws/src`: Allman brace style, space before parens on function calls/declarations, 2-space access-modifier offset. Run `./scripts/format-all.sh` (or rely on format-on-save in the devcontainer) rather than hand-formatting.
