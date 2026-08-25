# PX4 integration

Detail behind the PX4 references in [AGENTS.md](../../AGENTS.md).

## Version

**No PX4 version is pinned in this repo.** There is no `PX4_VERSION`, no submodule pin, and no
version string in any compose file, script, or doc. PX4 lives at `~/PX4-Autopilot` **inside the
dev container image**, so the effective version is whatever `devcontainer-px4:latest` currently
ships — and that tag moves. See [devcontainer.md](devcontainer.md).

Not pinning is a deliberate choice, not an oversight — the version tracks the image. Answer "what
PX4 version are we on?" by asking the running container, not by reading this repo:

```bash
cd ~/PX4-Autopilot && git describe --tags
```

Worth knowing **when** that matters: `px4_msgs` definitions must match the firmware. A mismatch
does not fail the build and does not raise an error — topics simply exist and never deliver. If
you are debugging silent `/fmu/...` traffic, check this pairing early.

The version table in `ros_ws/src/px4_msgs/README.md` (v1.13 / v1.14 / v1.15 / main) is **upstream
PX4's own compatibility matrix**, vendored along with the package. It is not a statement about what
this team runs.

## The uXRCE-DDS bridge

PX4 and ROS 2 talk over **uXRCE-DDS**. PX4 runs an XRCE-DDS *client*; an agent process on the ROS
side bridges it onto the DDS network where ROS 2 nodes can see it.

`.devcontainer/postStart.sh` starts that agent every time the container starts:

```bash
MicroXRCEAgent udp4 -p 8888
```

UDP4 on port 8888. In `SETUP.md`'s walkthrough, the line "Starting Micro XRCE Agent..." in the
terminal is the signal that the container is up.

In deployment this is its own service — `./scripts/deploy.sh up uxrce`, see
`deployment/compose.uxrce.yml`.

**If ROS 2 can't see any `/fmu/...` topics, check the agent first.** No agent means no bridge, and
every node will sit there publishing into nothing without erroring.

## Topic and service convention

Everything crossing the bridge uses the standard PX4 namespace:

- `/fmu/in/*` — ROS 2 → PX4 (commands and setpoints the flight controller consumes), e.g.
  `OffboardControlMode`, `TrajectorySetpoint`, `VehicleCommand`
- `/fmu/out/*` — PX4 → ROS 2 (telemetry and state the flight controller emits)
- `/fmu/vehicle_command` — the service the `Mission` base class calls for arm/disarm/mode changes

The direction is from PX4's point of view: `in` means *into the flight controller*. See
[architecture.md](architecture.md) for how `Mission` drives these.

## Vendored upstream packages

`ros_ws/src/px4_msgs` and `ros_ws/src/px4_ros_com` are **unmodified upstream PX4 packages** —
message/service definitions and the ROS 2 bridge library respectively. Treat them as third-party:

- **Don't hand-edit them.** If message definitions need updating, follow the sync procedure in
  `ros_ws/src/px4_msgs/README.md`.
- They're excluded from the **CI** clang-format check — but **not** from `./scripts/format-all.sh`,
  which runs `clang-format -i` over all of `ros_ws/src` and will rewrite them in place. `ci.yml`
  says so itself: "note format-all.sh does NOT exclude them." So the most likely way to reformat
  vendored code is the very script the docs tell you to run. Check `git status` afterwards and
  revert any vendored churn — CI will not catch it for you.
- They dominate build time. This is why the clean-rebuild gotcha in `AGENTS.md` warns against
  wiping `ros_ws/build` unnecessarily.

The message definitions must match the PX4 firmware you're talking to. A mismatch usually shows up
as topics that exist but never deliver, or as deserialization errors from the agent — not as a
build failure.

## SITL simulation

Two tmux harnesses. Each creates **five** panes and drives four of them (the fifth is left as an
idle shell; the scripts' own "2x2 grid" comment is wrong):

| Pane | Runs |
| --- | --- |
| `.0` | PX4 SITL via `make px4_sitl` — **this is what launches Gazebo**; Gazebo is not its own pane |
| `.1` | `ros2 run ros_gz_bridge parameter_bridge` |
| `.2` | `rviz2` |
| `.3` | `rqt_image_view` |
| `.4` | idle shell |


| Script | World / target |
| --- | --- |
| `./scripts/simulateDepth.sh` | PX4's bundled `walls` world, target `gz_x500_depth_walls` |
| `./scripts/simulateTask2.sh` | target `gz_x500_depth`; **intends** `gz_worlds/aeac` but does not load it — see below |

⚠️ `simulateTask2.sh` sets `GZ_WORLD_PATH="$HOME/AeroSAE2027/gz_worlds/aeac"` and then chains
`PX4_GZ_WORLD=${GZ_WORLD_PATH} && make px4_sitl ...`. The `&&` makes that a shell variable, not an
exported environment variable, so `make`/PX4 never receives it — and the path is missing the `.sdf`
extension the on-disk file actually has (`gz_worlds/aeac.sdf`). The custom world is not applied.

Both resolve `PX4_DIR="$HOME/PX4-Autopilot"`. Run them from inside the dev container.

`./scripts/launchQGC.sh` backgrounds the QGroundControl AppImage, downloading it first if absent.
It does **not** spawn a terminal — running it from a second terminal is the user's step, per
`SETUP.md`. It also hard-exits on anything that isn't Linux/`x86_64`, so it is unusable on the
macOS setup discussed below. Per `SETUP.md`, give the sim 30–60 seconds, then wait for QGC to show
**"Ready"** before trying to arm.

macOS caveat, quoting `SETUP.md:50` exactly: "**macOS**: needs XQuartz for GUI passthrough —
Gazebo's 3D simulation view specifically won't work well on Mac (known limitation, driver
mismatch), but the rest should". `.devcontainer/compose.macos.yml:2` states it independently and
attributes it to XQuartz's out-of-date OpenGL driver.
