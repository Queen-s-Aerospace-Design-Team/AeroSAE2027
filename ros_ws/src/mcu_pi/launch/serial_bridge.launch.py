from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    serial_bridge_node = Node(
        package='mcu_pi',
        executable='serial_bridge_node',
        name='serial_bridge_node',
        output='screen'
    )

    return LaunchDescription([
        serial_bridge_node
    ])
