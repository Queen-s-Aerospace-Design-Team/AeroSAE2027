# Testing offboard_heartbeat

Run everything inside the dev container, using Terminal 1 (build and sim, PX4 `pxh>` pane), Terminal 2 (node) and Terminal 3 (checks).

## 1. Clean up (Terminal 1)

```bash
tmux kill-server; pkill -f px4; pkill -f "gz sim"; pkill -f heartbeat_node
```

Does: Stops any leftover sim, PX4 and node processes.

Expect: No sim processes left ("no process found" is fine).

## 2. Build (Terminal 1)

```bash
cd ~/AeroSAE2027/ros_ws && colcon build --symlink-install
```

Does: Builds the ROS 2 workspace.

Expect: All packages finish.

## 3. Start sim (Terminal 1)

```bash
cd ~/AeroSAE2027 && ./scripts/simulateDepth.sh
```

Does: Launches PX4 SITL with Gazebo.

Expect: Gazebo shows the drone and `pxh>` appears after about a minute.

## 4. Start node (Terminal 2)

```bash
source ~/AeroSAE2027/ros_ws/install/setup.zsh
ros2 run offboard_heartbeat heartbeat_node
```

Does: Runs the heartbeat node.

Expect: One "Heartbeat node active at 10Hz" line, then quiet.

## 5. Check heartbeat (Terminal 3)

```bash
source ~/AeroSAE2027/ros_ws/install/setup.zsh
ros2 topic hz /fmu/in/offboard_control_mode
```

Does: Measures the heartbeat publish rate.

Expect: Average rate about 10 Hz (20 Hz means two nodes are running).

## 6. Enter Offboard (pxh>)

```
commander mode offboard
```

Does: Switches PX4 into Offboard mode.

Expect: Terminal 2 logs `OFFBOARD STARTED`.

## 7. Leave Offboard (pxh>)

```
commander mode auto:loiter
```

Does: Switches PX4 out of Offboard mode.

Expect: Terminal 2 logs `OFFBOARD STOPPED`.

Note: Steps 6 and 7 are the #126 done condition and work on the ground.

## 8. Optional flight (pxh>)

```
commander arm
commander takeoff
commander mode offboard
```

Does: Arms, takes off, then hands control to the node.

Expect: Drone climbs smoothly to 5 m and Terminal 2 logs `Target reached`. If arming is denied, run `commander check`.

## 9. Shut down

```
shutdown          # at pxh>
# Ctrl+C in Terminal 2
tmux kill-server  # Terminal 1
```

Does: Stops PX4, the node and the tmux session.

Expect: All sim windows close.

Note: Closing a terminal does not stop the sim.
