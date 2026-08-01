#!/bin/bash
# Starts the Micro XRCE-DDS Agent used to communicate with PX4 after the container starts.
set -e

echo "Starting Micro XRCE Agent..."
MicroXRCEAgent udp4 -p 8888
