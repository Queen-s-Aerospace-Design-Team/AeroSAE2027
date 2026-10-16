import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MinimalSubscriber(Node):

    def __init__(self):  # Setup the listener ROS2 function
        super().__init__('minimal_subscriber')
        self.subscription = self.create_subscription(  # This creates a subscription to the middleware channel created in the talker to pick up the message, connect to the listener_callback function, and then print the message picked up in terminal
            String, 'topic', self.listener_callback, 10
        )
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        # Print the subscriber message in terminal
        self.get_logger().info(f'I heard: "{msg.data}"')


def main(args=None):  # Similar as to the talker file main function
    rclpy.init(args=args)
    minimal_subscriber = MinimalSubscriber()
    rclpy.spin(minimal_subscriber)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
