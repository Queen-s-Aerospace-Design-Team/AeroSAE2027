"""Launch the Pi-side serial bridge node."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """Create the launch description for the serial bridge."""
    config = os.path.join(
        get_package_share_directory('mcu_pi'),
        'config',
        'serial_bridge.yaml',
    )
    return LaunchDescription([
        Node(
            package='mcu_pi',
            executable='serial_bridge_node',
            name='serial_bridge',
            output='screen',
            parameters=[config],
        ),
    ])
