# AGENTS.md

Context for any AI agent working in this repo. If you're a human, this is also a
fast-onboarding doc — see also [CLAUDE.md](./CLAUDE.md) for Claude-Code-specific workflow
notes, [SETUP.md](./SETUP.md) for the ~30-minute new-member setup, and [README.md](./README.md)
for the long per-OS install guide.

## Scope

This repo is the autonomy + perception stack for the **AeroSAE 2027** competition, developed
by **Queen's Aerospace Design Team (QADT)**.

Branch naming, PR conventions, and review norms are **not** repeated here — see
[CONTRIBUTING.md](./CONTRIBUTING.md). `main` is protected: every change lands via a PR with at
least one approving review.

Agents in this repo:

- **Assist, they don't replace understanding.** Members are here to learn ROS 2, PX4, Git, and
  this stack.
- **Good uses:** boilerplate and scaffolding, explaining existing code, drafting a launch file
  or a test for a member to review, writing tests.
- **Bad uses:** writing or merging core autonomy/perception logic — the `flight_missions` FSM,
  the mission executables, the ZED pipeline, the DBSCAN clustering — that the submitting member
  doesn't understand and can't explain in review.

This lines up with the review norm in `CONTRIBUTING.md`: deep scrutiny is reserved for anything
touching flight-critical logic (`flight_missions/`, `mission_core/`) or the shared
devcontainer/deployment config.

## Project summary

QADT (Queen's Aerospace Design Team) AeroSAE 2027 software monorepo: drone autonomy on PX4 +
ROS 2 Jazzy, perception (ZED stereo camera), hardware control (gimbal/water-release payload), a
Google Drive upload service, and Gazebo simulation assets. Everything is built and run inside a
Docker dev container — there is no supported host-native build.

## Stack

- ROS 2 **Jazzy** (`/opt/ros/jazzy`, Python 3.12)
- PX4 via the Micro XRCE-DDS bridge. **No PX4 version is pinned in this repo** — the dev image
  is tagged `:latest` and ships its own `~/PX4-Autopilot`, so the effective version is whatever
  that image currently carries. See `docs/context/px4-integration.md`.
- ZED stereo camera perception, mostly *outside* the ROS workspace (see `perception/`)
- DBSCAN clustering for target detection (`min_samples=5`)
- C++ (`flight_missions`, `ament_cmake`) + Python (`navigation_core`, `hardware_controllers`,
  `google_drive`)
- Devcontainer-based dev environment — no supported host-native build

## Development environment

- All development happens inside the VSCode **Dev Container** (`.devcontainer/`). Open the repo in VSCode and "Reopen in Container"; do not try to build the ROS workspace on the bare host.
- `.devcontainer/initialize.sh` runs before the container starts: it detects the host platform (linux-NVIDIA / linux-nonNVIDIA / macos / wsl) and copies the matching `.devcontainer/compose.<profile>.yml` to `compose.active.yml` (gitignored), which `devcontainer.json` composes together with `compose.base.yml`. This is a one-time file *copy*, not a symlink — if you edit a `compose.<profile>.yml`, rerun `initialize.sh` (or re-trigger "Reopen in Container") to regenerate `compose.active.yml`, or your edits silently won't take effect.
- On the Linux profiles, `initialize.sh` requires a working X11 display for GUI passthrough (Gazebo, rviz2, etc.), but accepts XWayland too: it checks for either `XDG_SESSION_TYPE=x11` or a live socket at `/tmp/.X11-unix/X<N>`, so Wayland-default hosts (e.g. Ubuntu 24.04+ GNOME) work as long as XWayland is running.
- `.devcontainer/postStart.sh` starts the Micro XRCE-DDS Agent (`MicroXRCEAgent udp4 -p 8888`) needed for PX4 ↔ ROS 2 communication.
- `./scripts/manualCompose.sh` brings the devcontainer up/down from the terminal (runs `initialize.sh`, `docker compose up -d`, execs a shell) as an alternative to VSCode's "Reopen in Container".
- Editor: format-on-save with `clang-format` is enabled for C/C++ inside the container; Python paths are pointed at `/opt/ros/jazzy/...`, the built `px4_msgs` install, and `ros_ws/src`.

More detail — image reference, mount layout, container identity — in `docs/context/devcontainer.md`.

## Build & run

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

## Repo layout

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

The two stacks also run as **different users**: `qadt` in the dev container, `qadt-deploy` in the
deployment containers. Don't copy a path from one into the other.

## Coding conventions

### C++

`.clang-format` at the repo root (LLVM-based) governs all C/C++ under `ros_ws/src`: Allman brace style, space before parens on function calls/declarations, 2-space access-modifier offset. Run `./scripts/format-all.sh` (or rely on format-on-save in the devcontainer) rather than hand-formatting.

`px4_msgs` and `px4_ros_com` are vendored upstream and excluded from the format check — don't
reformat them.

### Python

- ROS packages (`navigation_core`, `hardware_controllers`, `google_drive`) use the
  `ament_python` test convention: a `test/` folder with `test_flake8.py`, `test_pep257.py`, and
  `test_copyright.py`, run through `colcon test` — **not** pytest directly.
- `perception/zed-positional-measurement/` is the exception: a standalone subproject with its
  own `tests/`, run with plain `pytest`, outside colcon entirely.

## CI

`.github/workflows/ci.yml` runs on pull requests into `main`. Four jobs; the first three gate
merges, lint is advisory and never blocks:

| Job | What it does | Blocks merge? |
| --- | --- | --- |
| **Secret scanning** | gitleaks over the commits the PR adds | Yes |
| **Devcontainer config check** | runs `initialize.sh`, `docker compose config` over every compose profile, asserts `devcontainer.json` agrees with `compose.base.yml` (`remoteUser`/`workspaceFolder`/`working_dir`/bind target), and confirms the image is pullable | Yes |
| **Colcon build (ROS2 workspace)** | verifies container identity (the image actually runs as `qadt`), then `colcon build --symlink-install` inside the dev image | Yes |
| **Lint (Python + C++)** | `clang-format --dry-run --Werror` plus `ament_flake8` / `ament_pep257`; findings surface as PR annotations | **No — advisory** |

Container jobs read the image name out of `.devcontainer/compose.base.yml` at runtime, so CI
cannot drift from the dev environment. The container-identity check exists specifically to catch
an upstream rename of the container user — see `docs/context/devcontainer.md`.

## Deeper context

- Architecture detail (FSM, mission executables, ZED pipeline, clustering) → [docs/context/architecture.md](docs/context/architecture.md)
- Devcontainer build/mount details, the `qadt-dev` → `qadt` history → [docs/context/devcontainer.md](docs/context/devcontainer.md)
- uXRCE-DDS bridge, PX4 specifics → [docs/context/px4-integration.md](docs/context/px4-integration.md)
- Team/competition-specific terms → [docs/context/glossary.md](docs/context/glossary.md)
