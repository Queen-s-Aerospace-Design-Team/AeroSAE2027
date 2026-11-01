#include "onboarding/sub.hpp"

Subscriber::Subscriber() : Node( "onboarding_subscriber" )
{
    subscription_ = create_subscription<std_msgs::msg::String>(
        "chatter",
        10,
        [this]( const std_msgs::msg::String::SharedPtr message )
        { RCLCPP_INFO( get_logger(), "Received: '%s'", message->data.c_str() ); } );
}

Subscriber::~Subscriber() = default;

int main( int argc, char** argv )
{
    rclcpp::init( argc, argv );
    rclcpp::spin( std::make_shared<Subscriber>() );
    rclcpp::shutdown();
    return 0;
}
