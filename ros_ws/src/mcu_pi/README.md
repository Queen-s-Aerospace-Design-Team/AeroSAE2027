# mcu_pi

Pi-side ROS 2 package for the serial link between a Raspberry Pi 5 and an Arduino Nano.

**Status:** skeleton only. The node does not open a serial port, and the protocol, simulator, and functional tests are not implemented.

## Build and test

```bash
cd ros_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select mcu_pi --symlink-install
colcon test --packages-select mcu_pi
colcon test-result --verbose
```

## Run

```bash
source install/setup.bash
ros2 launch mcu_pi serial_bridge.launch.py
```

## To be decided

- Nano variant and serial device name
- Distance sensor and position actuation
- License
- ROS topics, message types, and wire payload layouts
