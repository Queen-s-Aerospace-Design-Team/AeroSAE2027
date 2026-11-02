"""Placeholder node for the serial bridge."""

import rclpy
from rclpy.node import Node


class SerialBridgeNode(Node):
    """Placeholder node with no functionality."""

    def __init__(self) -> None:
        super().__init__('serial_bridge_node')
        self.get_logger().info('serial_bridge_node placeholder started')


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SerialBridgeNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
