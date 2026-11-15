#!/usr/bin/env bash
# Starts sim/launch.sh headless, checks PX4 and ROS 2 come up, sends one Ctrl-C, and fails
# if any sim process is left behind. Run inside the dev container. Exit 0 = pass.
#   ./sim/smoke_test.sh [--world NAME]
set -uo pipefail

LOG="$(mktemp /tmp/sim_smoke.XXXXXX.log)"
PATTERN='px4_sitl_default/bin/px4|gz sim|parameter_bridge'
# An agent started by postStart.sh isn't the sim's to stop.
pgrep -x MicroXRCEAgent >/dev/null || PATTERN+='|MicroXRCEAgent'

fail() { echo "FAIL: $*"; tail -n 30 "$LOG"; kill -KILL -- "-$SIM" 2>/dev/null; exit 1; }
# A zombie (exited, not yet reaped) still passes kill -0.
alive() { [[ "$(ps -o stat= -p "$SIM" 2>/dev/null)" =~ ^[^Z] ]]; }

pgrep -af "$PATTERN" && { echo "FAIL: sim processes already running (above)"; exit 1; }

# Own process group, as a terminal gives it. Without set -m, bash starts `&` jobs with
# SIGINT ignored and launch.sh could never see the Ctrl-C.
set -m
"$(dirname "$0")/launch.sh" --headless "$@" >"$LOG" 2>&1 </dev/null &
SIM=$!
set +m
trap 'kill -INT "$SIM"; exit 130' INT

# Not "Ready for takeoff": PX4 1.16 only prints that once QGroundControl connects.
for _ in {1..120}; do
    grep -aq "Startup script returned successfully" "$LOG" && break
    alive || fail "launch.sh exited early"
    sleep 2
done
grep -aq "Startup script returned successfully" "$LOG" || fail "PX4 not ready after 240s"
echo "PASS: PX4 started and connected to Gazebo"

set +u
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash
set -u
timeout 20 ros2 topic echo --once /clock >/dev/null 2>&1 || fail "no /clock (ros_gz_bridge)"
echo "PASS: /clock is publishing (ros_gz_bridge)"
# --spin-time: the default 0.5s is too short to discover the agent's topics.
for _ in {1..5}; do
    ros2 topic list --no-daemon --spin-time 3 2>/dev/null | grep -q '^/fmu/out/' && break
done || fail "no /fmu/out/* topics (MicroXRCEAgent)"
echo "PASS: /fmu/out/* topics visible (MicroXRCEAgent)"

kill -INT "$SIM"
for _ in {1..20}; do alive || break; sleep 1; done
alive && fail "launch.sh still running 20s after Ctrl-C"
sleep 1
pgrep -af "$PATTERN" && fail "orphaned processes (above)"
echo "PASS: Ctrl-C stopped everything, no orphans"
rm -f "$LOG"
