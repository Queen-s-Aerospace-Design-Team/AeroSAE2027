#pragma once

#include <memory>

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>

class Subscriber : public rclcpp::Node
{
  public:
    explicit Subscriber();
    ~Subscriber() override;

  private:
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
};