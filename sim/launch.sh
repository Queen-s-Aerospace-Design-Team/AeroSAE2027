#!/usr/bin/env bash
# PX4 SITL + Gazebo Sim + ros_gz_bridge. Run inside the dev container; one Ctrl-C stops it all.
#   ./sim/launch.sh [--headless] [--world NAME|FILE.sdf]    (default world: walls)
set -eo pipefail   # no -u: ROS setup.bash reads unset variables

SIM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEAM_WORLDS="$SIM_DIR/../gz_worlds"
PX4_DIR="${PX4_DIR:-$HOME/PX4-Autopilot}"
PX4_BUILD="$PX4_DIR/build/px4_sitl_default"
PX4_GZ="$PX4_DIR/Tools/simulation/gz"
HEADLESS=false
WORLD=walls

while [[ $# -gt 0 ]]; do
    case "$1" in
        --headless) HEADLESS=true ;;
        --world)    WORLD="${2:?--world needs a value}"; shift ;;
        -h|--help)  sed -n '2,3p' "$0"; exit 0 ;;
        *)          sed -n '2,3p' "$0" >&2; exit 1 ;;
    esac
    shift
done

case "$WORLD" in
    *.sdf) SDF="$WORLD" ;;
    *)     SDF="$TEAM_WORLDS/$WORLD.sdf"; [[ -f "$SDF" ]] || SDF="$PX4_GZ/worlds/$WORLD.sdf" ;;
esac
[[ -f "$SDF" ]] || { echo "World not found: $WORLD" >&2; exit 1; }
# PX4 finds the world by its <world name>, which can differ from the file name (aeac.sdf is "walls").
WORLD_NAME="$(grep -oPm1 '<world\s+name="\K[^"]+' "$SDF")"

[[ -x "$PX4_BUILD/bin/px4" ]] || make -C "$PX4_DIR" px4_sitl
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash

# PX4 normally sets these itself, but only when it starts Gazebo, which it doesn't here.
export GZ_IP=127.0.0.1
export GZ_SIM_RESOURCE_PATH="$PX4_GZ/models:$PX4_GZ/worlds:$TEAM_WORLDS"
export GZ_SIM_SYSTEM_PLUGIN_PATH="$PX4_BUILD/src/modules/simulation/gz_plugins"
export GZ_SIM_SERVER_CONFIG_PATH="$PX4_DIR/src/modules/simulation/gz_bridge/server.config"

# Each process gets its own process group, so stop() also reaches any children it spawns.
set -m
PIDS=()
stop() {
    trap - INT TERM EXIT
    echo "Stopping simulation..."
    for pid in "${PIDS[@]}"; do kill -TERM -- "-$pid" 2>/dev/null || true; done
    for _ in {1..10}; do
        pgrep -g "$(IFS=,; echo "${PIDS[*]}")" >/dev/null || break
        sleep 1
    done
    for pid in "${PIDS[@]}"; do kill -KILL -- "-$pid" 2>/dev/null || true; done
    wait 2>/dev/null || true
}
trap 'stop; exit 130' INT TERM
trap stop EXIT

# --headless-rendering even with the GUI: camera sensors rendered through the display
# crash the server on macOS/XQuartz.
gz sim --verbose=1 -r -s --headless-rendering "$SDF" </dev/null &
GZ_PID=$!; PIDS+=("$GZ_PID")

if ! $HEADLESS; then
    # Its output goes to a file: on macOS it always crashes (XQuartz lacks OpenGL 3.3).
    gz sim -g >/tmp/gz_gui.log 2>&1 </dev/null &
    PIDS+=($!)
    echo "Gazebo GUI log: /tmp/gz_gui.log"
fi

# Standalone: PX4 spawns the drone into the running world instead of starting its own
# Gazebo, which `make px4_sitl` leaves orphaned on Ctrl-C. -d: no interactive shell.
env -C "$PX4_BUILD/rootfs" PX4_SIM_MODEL=gz_x500_depth PX4_GZ_STANDALONE=1 \
    PX4_GZ_WORLD="$WORLD_NAME" PX4_GZ_MODELS="$PX4_GZ/models" \
    "$PX4_BUILD/bin/px4" -d </dev/null &
PX4_PID=$!; PIDS+=("$PX4_PID")

ros2 run ros_gz_bridge parameter_bridge --ros-args \
    -p config_file:="$SIM_DIR/bridge.yaml" -p use_sim_time:=true </dev/null &
PIDS+=($!)

# postStart.sh normally starts the agent already; a second one would fight over port 8888.
if ! pgrep -x MicroXRCEAgent >/dev/null; then
    MicroXRCEAgent udp4 -p 8888 >/dev/null </dev/null &
    PIDS+=($!)
fi
set +m   # groups are set; this just silences bash's "Terminated" job notices

wait -n "$GZ_PID" "$PX4_PID" || true
echo "Gazebo or PX4 exited."
