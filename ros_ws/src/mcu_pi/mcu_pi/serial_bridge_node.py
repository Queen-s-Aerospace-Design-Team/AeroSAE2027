"""ROS 2 wrapper for the Pi to Nano serial link (skeleton)."""

import rclpy
from rclpy.node import Node


def main(args=None):
    """Report that the node is not implemented, then exit."""
    rclpy.init(args=args)
    node = Node('serial_bridge')
    node.get_logger().warning('Skeleton only: no serial port is opened.')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
