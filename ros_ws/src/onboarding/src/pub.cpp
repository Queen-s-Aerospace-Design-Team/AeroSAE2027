#include "onboarding/pub.hpp"

using namespace std::chrono_literals;

Publisher::Publisher() : Node( "onboarding_publisher" ), count_( 0 )
{
    publisher_ = create_publisher<std_msgs::msg::String>( "chatter", 10 );
    timer_     = create_wall_timer( 1s,
                                    [this]()
                                    {
                                    auto message = std_msgs::msg::String();
                                    message.data = "Hello from the publisher: " + std::to_string( count_++ );
                                    publisher_->publish( message );
                                    RCLCPP_INFO( get_logger(), "Published: '%s'", message.data.c_str() );
                                } );
}

Publisher::~Publisher() = default;

int main( int argc, char** argv )
{
    rclcpp::init( argc, argv );
    rclcpp::spin( std::make_shared<Publisher>() );
    rclcpp::shutdown();
    return 0;
}