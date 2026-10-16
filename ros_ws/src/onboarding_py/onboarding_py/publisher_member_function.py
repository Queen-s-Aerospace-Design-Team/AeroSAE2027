import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MinimalPublisher(Node):

    def __init__(self):  # "talker" function
        super().__init__('minimal_publisher')  # Gain access to the ROS 2 node
        # This creates a "channel" in the ROS 2 middleware which is where the listener gets tuned to listen for the communications from the talker | The 10 means hold up to 10 recent messages in that channel
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        timer_period = 0.5  # seconds
        # Setup the timer | Connects the time period with the timer_callback function (the message printer)
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0  # To track how many calls have been made

    def timer_callback(self):
        msg = String()  # Create a blank string message
        msg.data = f'Hello World: {self.i}'  # Populate the message
        self.publisher_.publish(msg)  # Publish the message
        self.get_logger().info(f'Publishing: "{msg.data}"')  # Print the message to the console
        self.i += 1  # Add to the counting index


def main(args=None):
    rclpy.init(args=args)
    minimal_publisher = MinimalPublisher()  # Triggers the __init__ function in the parent class
    rclpy.spin(minimal_publisher)
    minimal_publisher.destroy_node()  # Allows for graceful shutdown
    rclpy.shutdown()


if __name__ == '__main__':  # Run the main function
    main()
