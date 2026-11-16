import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

from px4_msgs.msg import OffboardControlMode
from px4_msgs.msg import TrajectorySetpoint
from px4_msgs.msg import VehicleLocalPosition
from px4_msgs.msg import VehicleStatus

NAN3 = [math.nan] * 3
TARGET_TOLERANCE_M = 0.3


class OffboardHeartbeatNode(Node):
    def __init__(self):
        super().__init__('offboard_heartbeat_node')

        # Absolute NED position [north, east, down] in metres; PX4 forgets it, so we keep it.
        self.declare_parameter('target', [0.0, 0.0, -5.0])
        # Limit on how fast the commanded setpoint moves, so resuming never jumps.
        self.declare_parameter('max_speed', 1.0)
        # Seconds of *active* (non-paused) time allowed to reach the target.
        self.declare_parameter('mission_timeout_s', 120.0)

        self.target = list(self.get_parameter('target').get_parameter_value().double_array_value)
        self.max_speed = self.get_parameter('max_speed').get_parameter_value().double_value
        self.mission_timeout_s = (
            self.get_parameter('mission_timeout_s').get_parameter_value().double_value)

        # Match PX4 uXRCE-DDS bridge QoS requirements (Best Effort)
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.offboard_pub = self.create_publisher(
            OffboardControlMode, '/fmu/in/offboard_control_mode', qos_profile)
        self.setpoint_pub = self.create_publisher(
            TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos_profile)

        self.status_sub = self.create_subscription(
            VehicleStatus, '/fmu/out/vehicle_status_v1', self.status_callback, qos_profile)
        self.position_sub = self.create_subscription(
            VehicleLocalPosition, '/fmu/out/vehicle_local_position',
            self.position_callback, qos_profile)

        self.paused = True
        self.position = None  # latest valid [x, y, z], or None
        self.cmd = None       # setpoint we are currently streaming
        self.active_s = 0.0   # time spent in Offboard; frozen while paused
        self.reached = False
        self.timed_out = False
        self.last_tick = self.get_clock().now()

        # Publish continuously at 10 Hz (every 0.1 seconds)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info(
            f"Heartbeat node active at 10Hz. Target (NED) {self.target}, "
            f"max_speed {self.max_speed} m/s, timeout {self.mission_timeout_s}s active time.")

    def position_callback(self, msg: VehicleLocalPosition):
        if msg.xy_valid and msg.z_valid:
            self.position = [msg.x, msg.y, msg.z]
        else:
            self.position = None

    def status_callback(self, msg: VehicleStatus):
        in_offboard = (msg.nav_state == VehicleStatus.NAVIGATION_STATE_OFFBOARD)
        if in_offboard and self.paused:
            self.resume()
        elif not in_offboard and not self.paused:
            self.pause()

    def pause(self):
        self.paused = True
        self.get_logger().info(
            f"<<< OFFBOARD STOPPED: mission paused at {self.active_s:.1f}s active time, "
            f"target kept at {self.target} >>>")

    def resume(self):
        self.paused = False
        # Start the slew from where the drone actually is, then walk to the stored target.
        if self.position is not None:
            self.cmd = list(self.position)
        self.get_logger().info(
            f">>> OFFBOARD STARTED: mission resumed toward {self.target} "
            f"at max {self.max_speed} m/s >>>")

    def slew_toward_target(self, cmd, dt):
        step = self.max_speed * dt
        delta = [t - c for t, c in zip(self.target, cmd)]
        dist = math.sqrt(sum(d * d for d in delta))
        if dist <= step:
            return list(self.target)
        return [c + d / dist * step for c, d in zip(cmd, delta)]

    def check_mission(self):
        if self.reached or self.timed_out or self.position is None:
            return
        err = math.dist(self.position, self.target)
        if err <= TARGET_TOLERANCE_M:
            self.reached = True
            self.get_logger().info(
                f"Target reached after {self.active_s:.1f}s active time (error {err:.2f} m).")
        elif self.active_s >= self.mission_timeout_s:
            self.timed_out = True
            self.get_logger().warn(
                f"MISSION TIMEOUT: target not reached in {self.mission_timeout_s}s active time.")

    def timer_callback(self):
        now = self.get_clock().now()
        dt = (now - self.last_tick).nanoseconds / 1e9
        self.last_tick = now
        timestamp_us = now.nanoseconds // 1000

        if self.paused:
            # Keep the stream alive, but only hold where the drone is, so entering
            # Offboard never causes a jump. The mission clock does not advance.
            if self.position is not None:
                self.cmd = list(self.position)
        elif self.cmd is not None:
            self.active_s += dt
            self.cmd = self.slew_toward_target(self.cmd, dt)
            self.check_mission()

        # 1. Heartbeat: OffboardControlMode must keep arriving or PX4 drops Offboard.
        ocm = OffboardControlMode()
        ocm.timestamp = timestamp_us
        ocm.position = True
        ocm.velocity = False
        ocm.acceleration = False
        ocm.attitude = False
        ocm.body_rate = False
        self.offboard_pub.publish(ocm)

        # 2. Setpoint. With no valid position yet we send NaN, which PX4 refuses to fly.
        sp = TrajectorySetpoint()
        sp.timestamp = timestamp_us
        sp.position = self.cmd if self.cmd is not None else NAN3
        sp.velocity = NAN3
        sp.acceleration = NAN3
        sp.jerk = NAN3
        sp.yaw = math.nan
        sp.yawspeed = math.nan
        self.setpoint_pub.publish(sp)


def main(args=None):
    rclpy.init(args=args)
    node = OffboardHeartbeatNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
