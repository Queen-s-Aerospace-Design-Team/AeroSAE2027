# Glossary

Terms that show up across this repo, the compose files, and team conversation.

## Team and competition

| Term | Meaning |
| --- | --- |
| **QADT** | **Q**ueen's **A**erospace **D**esign **T**eam — the team that owns this repo |
| **AeroSAE 2027** | This season's competition, and the name of this repo (`AeroSAE2027`) |
| **AEAC 2026** | **Last** season's competition and repo (`AEAC2026`). Per commit `f7b730f`, AEAC 2026 was a genuinely different competition, not a year bump — so "AEAC" is not an old spelling of "AeroSAE", and old AEAC material may not carry over |

> `TODO:` record the competition's full official name, its class/category, and any judge-facing
> terminology (task names, scoring vocabulary). The repo only ever says "the AeroSAE 2027
> competition" — nothing in it confirms a longer official title, so none is asserted here.

## Flight stack

| Term | Meaning |
| --- | --- |
| **PX4** | The flight-control firmware running on the vehicle's autopilot |
| **FMU** | Flight Management Unit — the autopilot hardware. Source of the `/fmu/...` topic namespace |
| **uXRCE-DDS** | Micro XRCE-DDS, the transport bridging PX4 to the ROS 2 DDS network. `MicroXRCEAgent` is the bridging process; see [px4-integration.md](px4-integration.md) |
| **Offboard mode** | PX4 flight mode where an external computer streams setpoints. PX4 will refuse to enter it unless setpoints are already arriving, and will drop out if they stop |
| **Setpoint** | A commanded target (position, velocity, attitude) published each control tick |
| **Arm / disarm** | Enabling / disabling motor output. Arming is a distinct step from selecting a flight mode |
| **RTL** | Return To Launch — fly back to the takeoff point. One of the `FinishPolicy` options on `Mission` |
| **FSM** | Finite State Machine — here, the `enum FSM` in `Mission` that sequences a mission from `Init` to `Finished`. See [architecture.md](architecture.md) |
| **SITL** | Software In The Loop — PX4 firmware running as a host process against a simulated vehicle, no hardware involved |
| **HITL** | Hardware In The Loop — real autopilot hardware driven by a simulated world. Not currently used here |
| **QGC** | QGroundControl, the ground-station GUI. Launched with `./scripts/launchQGC.sh` |
| **Gazebo** | The 3D physics simulator SITL flies in. Worlds live in `gz_worlds/` |
| **`ros_gz`** | The bridge relaying topics between Gazebo and ROS 2 |

## ROS 2

| Term | Meaning |
| --- | --- |
| **ROS 2 Jazzy** | The ROS 2 distribution used here, at `/opt/ros/jazzy` |
| **colcon** | The build tool for the workspace. `colcon build`, `colcon test` |
| **ament** | ROS 2's package/build conventions. `ament_cmake` for C++ packages, `ament_python` for Python ones |
| **Workspace** | `ros_ws/` — `src/` is checked in; `build/`, `install/`, and `log/` are generated and gitignored |
| **Overlay / sourcing** | `source install/setup.bash` layers the built workspace on top of `/opt/ros/jazzy`. A new terminal needs this before it can see your packages |
| **`--symlink-install`** | Installs symlinks instead of copies, so edits to Python/config files take effect without rebuilding |
| **`cmd_vel`** | The conventional ROS velocity-command topic. `navigation_core` translates it into PX4 setpoints |

## Perception

| Term | Meaning |
| --- | --- |
| **ZED** | The Stereolabs stereo camera family used for perception. **ZED X** is the model on the Jetson |
| **SVO** | Stereolabs' recorded-stream format. Captured by `record_svo.py`, replayed for offline work |
| **Jetson** | The NVIDIA compute module onboard the aircraft that runs perception |
| **DBSCAN** | Density-based clustering used in `circle_processing.py` to group repeated target detections. `min_samples=5` — a target needs ≥5 frame observations to survive |
| **Roboflow** | The dataset/labelling service extracted frames get uploaded to |
| **Live-first vs replay-first** | `zed-positional-measurement`'s docs describe an intended live-camera architecture; the runtime still works from recordings. Don't assume the docs match the code |

## Containers and infrastructure

| Term | Meaning |
| --- | --- |
| **Dev container** | The VSCode development environment, `.devcontainer/`. Runs as user **`qadt`** at `/home/qadt/AeroSAE2027` |
| **Deployment container** | The production containers on the aircraft, `deployment/`. Run as user **`qadt-deploy`**. Distinct from the dev container — see [devcontainer.md](devcontainer.md) |
| **`qadt-dev`** | A **former** container username, renamed to `qadt` upstream. Appears in no current file; only relevant as history behind CI's container-identity check |
| **Compose profile** | One of `linux-NVIDIA` / `linux-nonNVIDIA` / `macos` / `wsl`. `initialize.sh` copies the matching file to `compose.active.yml` |
| **GHCR** | GitHub Container Registry, `ghcr.io` — where both images are hosted |
| **gitleaks** | The secret scanner CI runs over the commits a PR adds |
