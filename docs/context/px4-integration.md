# PX4 integration

Detail behind the PX4 references in [AGENTS.md](../../AGENTS.md).

## Version

**No PX4 version is pinned in this repo.** There is no `PX4_VERSION`, no submodule pin, and no
version string in any compose file, script, or doc. PX4 lives at `~/PX4-Autopilot` **inside the
dev container image**, so the effective version is whatever `devcontainer-px4:latest` currently
ships — and that tag moves. See [devcontainer.md](devcontainer.md).

> `TODO:` decide whether the team wants to pin a PX4 version, and record it here if so. Until
> then, treat "what PX4 version are we on?" as a question answered by inspecting the running
> container (`cd ~/PX4-Autopilot && git describe --tags`), not by reading this repo.
>
> The version table in `ros_ws/src/px4_msgs/README.md` (v1.13 / v1.14 / v1.15 / main) is
> **upstream PX4's own compatibility matrix**, vendored along with the package. It is not a
> statement about what this team runs.

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
- They're excluded from this repo's clang-format check, so reformatting them would produce a large
  diff that CI won't catch and reviewers can't read.
- They dominate build time. This is why the clean-rebuild gotcha in `AGENTS.md` warns against
  wiping `ros_ws/build` unnecessarily.

The message definitions must match the PX4 firmware you're talking to. A mismatch usually shows up
as topics that exist but never deliver, or as deserialization errors from the agent — not as a
build failure.

## SITL simulation

Two tmux harnesses, each opening PX4 SITL + Gazebo + the `ros_gz` bridge + rviz2 in four panes:

| Script | World / target |
| --- | --- |
| `./scripts/simulateDepth.sh` | walls world, `gz_x500_depth_walls` target |
| `./scripts/simulateTask2.sh` | custom world at `gz_worlds/aeac` |

Both resolve `PX4_DIR="$HOME/PX4-Autopilot"`. Run them from inside the dev container.

`./scripts/launchQGC.sh` starts QGroundControl separately, in a new terminal. Per `SETUP.md`, give
the sim 30–60 seconds, then wait for QGC to show **"Ready"** before trying to arm.

macOS caveat (from `SETUP.md`): Gazebo's 3D view specifically doesn't work well on Mac — a known
driver mismatch — though the rest of the stack does.
