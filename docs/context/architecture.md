# Architecture

Detail behind the "Repo layout" summary in [AGENTS.md](../../AGENTS.md). Read that first.

## `flight_missions` — the mission framework

C++, `ament_cmake`. It is **one** ament package — there is a single `flight_missions/package.xml`;
`mission_core/` and `mission_nodes/` are plain CMake `add_subdirectory()` targets, not sub-packages,
so don't go looking for a `package.xml` in either.

- `mission_core/` builds a **library** (`add_library(mission_core)`) holding the `Mission` base class.
- `mission_nodes/` builds three **executables**: `return_to_origin`, `return_to_origin_v2`,
  `orbit_location`. Each is launched on its own, e.g. `ros2 run flight_missions orbit_location`
  (see `deployment/compose.mission.yml`).

> ⚠️ **`return_to_origin` is not a `Mission`.** `mission_nodes/src/return_to_origin.cpp:63` declares
> `class ReturnToOrigin : public rclcpp::Node` — it is a ~410-line legacy node predating the
> framework, with its own duplicated FSM (`Init, OffboardRequested, WaitForStableOffboard,
> ArmRequested, Approach, ManualRequested, Finished` — no `Failed`, no finish-policy states), its
> own copy of `Utilities::waitForServices`, and no header file. Only `orbit_location` and
> `return_to_origin_v2` subclass `Mission`. Read `return_to_origin_v2` if you want the pattern.

### The `Mission` base class

`mission_core/include/mission_core/mission.hpp`. A `rclcpp::Node` subclass that owns the shared
offboard-control state machine, so a concrete mission only has to describe *where the drone
should go* and *when it has arrived*.

**FSM states** (`enum FSM : uint8_t`), in the order the mission walks them:

`Init` → `OffboardRequested` → `WaitForStableOffboard` → `ArmRequested` → `MissionObjective`
→ `FinishPolicyRequested` → `FinishPolicyMonitor` → `Finished`, with `Failed` as the terminal
error state.

Two gaps worth knowing before you debug a stuck mission: **`Failed` is not reachable from
`MissionObjective` or `FinishPolicyMonitor`** — there are no timeouts on either, so a mission whose
`isMissionObjectiveReached()` never returns true hangs indefinitely rather than failing. And
`FinishPolicyMonitor` is a no-op pass-through when the policy is `Manual`.

Note the shape: offboard mode is requested first, then held through `WaitForStableOffboard` for
more than 10 ticks (~550 ms at the 50 ms tick) before the vehicle is armed.

The usual justification — PX4 will not stay in offboard mode unless setpoints keep streaming — is
general PX4 behaviour, **not** something this repo documents; the only comment gesturing at it is
`return_to_origin.cpp:96` ("offboard_control_mode needs to be paired with trajectory_setpoint"),
inherited from the vendored upstream examples. Note the code does not actually pre-stream: the
first tick publishes one setpoint pair and requests offboard in the same tick. The stabilisation
delay is applied before *arming*, not before the mode request.

**Finish policies** (`enum FinishPolicy : uint8_t`), chosen via the `Mission` constructor's second
argument (defaults to `Manual`):

- `Manual` — hand control back, take no ending action
- `RTL` — return to launch
- `RTLAndDisarm` — return to launch, then disarm

### What a concrete mission overrides

Two are **pure virtual** — a subclass will not compile without them:

| Method | Required? | Purpose |
| --- | --- | --- |
| `publishMissionSetpoint()` | **Yes** (`= 0`) | Publish this mission's trajectory setpoint each tick |
| `isMissionObjectiveReached()` | **Yes** (`= 0`) | Report whether the objective is complete, advancing the FSM |
| `onMissionObjectiveStart()` | No | Hook fired when `MissionObjective` is entered |
| `onMissionFinished()` | No | Hook fired when the mission completes. Default body is empty and **no node currently overrides it** |
| `publishOffboardControlMode()` | No | Override the default control-mode advertisement, which sets `position=true, velocity=true` and everything else false. **No mission_nodes subclass currently overrides it.** |

> **History:** the pre-`AGENTS.md` docs listed the overridables as `onMissionObjectiveStart()` /
> `publishMissionSetpoint()` / `onMissionFinished()` — omitting `isMissionObjectiveReached()`,
> which is one of the two *required* ones, and not distinguishing required from optional. Both
> `AGENTS.md` and the table above now match `mission.hpp`. If you find a doc still repeating the
> old list, it predates this correction.

### PX4 interface

The base class publishes `OffboardControlMode` and `TrajectorySetpoint` on `/fmu/in/...`, and
issues commands (arm, disarm, mode changes, RTL) through the `/fmu/vehicle_command` **service**.
A `/fmu/in/vehicle_command` publisher is also created but never published to — every command goes
via the service, so treat that publisher as dead code. See
[px4-integration.md](px4-integration.md) for the transport underneath.

## `navigation_core`

Python. `cmd_vel_to_px4.py` bridges `cmd_vel`-style velocity commands to PX4 setpoints, so
standard ROS navigation output can drive the vehicle. `cmd_vel_test.py` is a test publisher node.

## `hardware_controllers`

Python. The `gimbal_controller` node drives the payload gimbal PWM and the water-release GPIO.
Pin assignments are passed as explicit params at deploy time — `pitch_pwm_pin:=33`,
`water_gpio_pin:=31`, plus `dry_run` (`deployment/compose.hardware.yml`). Note that is only 3 of
the **21** params the node declares; the rest (servo limits, lock thresholds, `fire_duration_s`)
fall back to their code defaults.

## `google_drive` / `google_drive_interfaces`

The `drive_uploader` node plus the `DriveUploader.srv` service definition, for pushing captured
media to Google Drive. OAuth client config lives in `.credentials/credentials.json`; `token.json`
is generated by `generate_token.py` and is gitignored. Neither file should ever be committed —
CI's secret-scanning job will fail the PR if one is.

## Perception

### Standalone ZED/SVO tooling

Top-level scripts in `perception/`, run directly (not through colcon):

| Script | Role |
| --- | --- |
| `record_svo.py` | Capture a ZED SVO recording |
| `validate_svo.py` | Validate **YOLO detections / TRT engines** by replaying an SVO through them and drawing boxes; can compare two engines side by side. The SVO is the fixed input, not the thing under test |
| `extract_training_frames.py` | Pull frames out of an SVO for labelling |
| `upload_to_roboflow.py` | Push those frames to Roboflow |
| `circle_processing.py` | **Consumes** detections from a JSONL stream (batch via `ingest_json_file`, live via `tail_frames`), then clusters papers and wall planes, finds the ground plane, infers room corners, and emits target descriptions. It performs no detection itself |

### Clustering

`circle_processing.py` runs **DBSCAN** three separate times, with different parameters — quoting
`min_samples=5` alone is incomplete:

| Clustering | `min_samples` | Where |
| --- | --- | --- |
| Paper targets | **5** | `circle_processing.py:14`, used at `:355` |
| Wall planes | 3 | `:16`, used at `:442` |
| Ground plane | 2 | `:517` |

For paper targets a candidate needs **≥5 observations within `eps=0.3 m`** to survive as a cluster
— equivalent to ≥5 frames only if each paper is detected at most once per frame. This is the knob that
trades false positives against missing a briefly-seen target; `perception/docs/issues.md` covers
what to watch if clusters come out noisy after a hardware run.

### `zed-positional-measurement/`

A self-contained Python subproject (`src/zed_positional_measurement/`: `pipeline.py`, `sdk.py`,
`config.py`, `metrics.py`, `storage.py`, `exporters.py`, `geometry.py`, `cli.py`, `models.py`,
`providers.py`, `__main__.py`, `__init__.py`) with its own pytest suite. **Not** built or run through colcon.
"Self-contained" here means a directory whose `tests/conftest.py` injects `src/` onto `sys.path` —
there is no `pyproject.toml`, `setup.py`, or `pytest.ini`, so it is not an installable package.

Its `docs/` folder is the source of truth for its architecture. Read in this order:

`PRD.md` → `Technical.md` → `Operations.md` → `Schema.md` → `LucasHandoff.md` →
`Uncertainties.md` → `Validation.md`

⚠️ Per its own `docs/README.md`: those docs describe an intended **live-first** architecture, but
the current runtime is still **replay-first**. Don't assume the two match — check the code before
acting on a doc claim.

### Known caveats

`perception/docs/issues.md` and `perception/docs/learnings.md` track deferred perf items (per-frame
plane queries, an unused `mask_pixels` computation) and Jetson operational notes — notably the
`nvargus-daemon` / `zed_x_daemon` services behind the ZED X cameras, and how to restart them after
a bad camera-handoff state.

## `gz_worlds/`

`generate_world.py` writes `aeac.sdf`; `testing_room-params.xml` holds its parameters.

Only `simulateTask2.sh` references this directory, and it currently fails to apply the world:
`PX4_GZ_WORLD` is set with `&&` chaining instead of being exported, so `make`/PX4 never sees it,
and the path it points at (`gz_worlds/aeac`) lacks the `.sdf` extension the file actually has.
`simulateDepth.sh` does not use `gz_worlds/` at all — it uses PX4's bundled `walls` world.
