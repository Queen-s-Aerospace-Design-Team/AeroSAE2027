"""Generate a simple Gazebo Sim world with a 25 mm dark line on a light floor.

Save this file inside the AeroSAE2027/gz_worlds/ directory and run:
    python3 gz_worlds/generate_line_world.py

The resulting line_follow.sdf is written beside this script.
"""

import math
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

TAPE_WIDTH_M = 0.025       # 2.5 cm; change to 0.020 for 2.0 cm tape
TAPE_HEIGHT_M = 0.001     # 1 mm high visual representation
TAPE_CENTRE_Z_M = 0.001  # Tape is visually just above the floor (no collision)
FLOOR_SIZE_M = 10.0
CURVE_SEGMENTS = 60

sdf = ET.Element("sdf", version="1.9")
world = ET.SubElement(sdf, "world", name="line_follow")

# Follow the layout of gz_worlds/generate_world.py: physics, scene, ground.
physics = ET.SubElement(world, "physics", type="ode")
ET.SubElement(physics, "max_step_size").text = "0.004"
ET.SubElement(physics, "real_time_factor").text = "1.0"
ET.SubElement(physics, "real_time_update_rate").text = "250"
ET.SubElement(world, "gravity").text = "0 0 -9.8"

scene = ET.SubElement(world, "scene")
ET.SubElement(scene, "grid").text = "false"
ET.SubElement(scene, "ambient").text = "0.8 0.8 0.8 1"
ET.SubElement(scene, "background").text = "0.7 0.7 0.7 1"
ET.SubElement(scene, "shadows").text = "false"

sun = ET.SubElement(world, "light", name="sun", type="directional")
ET.SubElement(sun, "pose").text = "0 0 10 0 0 0"
ET.SubElement(sun, "diffuse").text = "0.85 0.85 0.85 1"
ET.SubElement(sun, "specular").text = "0.1 0.1 0.1 1"
ET.SubElement(sun, "direction").text = "-0.3 0.2 -1"
ET.SubElement(sun, "cast_shadows").text = "false"

# Large, light-coloured ground plane, both visible and collidable.
ground = ET.SubElement(world, "model", name="ground_plane")
ET.SubElement(ground, "static").text = "true"
ground_link = ET.SubElement(ground, "link", name="link")

collision = ET.SubElement(ground_link, "collision", name="collision")
collision_plane = ET.SubElement(ET.SubElement(collision, "geometry"), "plane")
ET.SubElement(collision_plane, "normal").text = "0 0 1"
ET.SubElement(collision_plane, "size").text = f"{FLOOR_SIZE_M} {FLOOR_SIZE_M}"

floor_visual = ET.SubElement(ground_link, "visual", name="floor_visual")
floor_plane = ET.SubElement(ET.SubElement(floor_visual, "geometry"), "plane")
ET.SubElement(floor_plane, "normal").text = "0 0 1"
ET.SubElement(floor_plane, "size").text = f"{FLOOR_SIZE_M} {FLOOR_SIZE_M}"
floor_material = ET.SubElement(floor_visual, "material")
ET.SubElement(floor_material, "ambient").text = "0.92 0.92 0.92 1"
ET.SubElement(floor_material, "diffuse").text = "0.92 0.92 0.92 1"
ET.SubElement(floor_material, "specular").text = "0.05 0.05 0.05 1"

# One static, collision-free model with many visual-only tape segments.
# The boxes are visible to a Gazebo camera but won't act like raised obstacles.
track = ET.SubElement(world, "model", name="dark_tape_track")
ET.SubElement(track, "static").text = "true"
track_link = ET.SubElement(track, "link", name="tape")
segment_count = 0


def draw_segment(start, end):
    """Add a thin rectangle between two (x, y) points on the floor."""
    global segment_count
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return
    yaw = math.atan2(dy, dx)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

    visual = ET.SubElement(track_link, "visual", name=f"tape_{segment_count:03d}")
    ET.SubElement(visual, "pose").text = f"{cx:.6f} {cy:.6f} {TAPE_CENTRE_Z_M} 0 0 {yaw:.8f}"
    box = ET.SubElement(ET.SubElement(visual, "geometry"), "box")
    ET.SubElement(box, "size").text = f"{length + 0.004:.6f} {TAPE_WIDTH_M} {TAPE_HEIGHT_M}"
    material = ET.SubElement(visual, "material")
    ET.SubElement(material, "ambient").text = "0.015 0.015 0.015 1"
    ET.SubElement(material, "diffuse").text = "0.015 0.015 0.015 1"
    ET.SubElement(material, "specular").text = "0.01 0.01 0.01 1"
    segment_count += 1


def draw_curve(x_start, x_end, baseline_y, bump_height):
    """Smoothly bend left/right, returning to the baseline with flat tangents."""
    points = []
    for i in range(CURVE_SEGMENTS + 1):
        t = i / CURVE_SEGMENTS
        x = x_start + (x_end - x_start) * t
        y = baseline_y + bump_height * math.sin(math.pi * t) ** 2
        points.append((x, y))
    for a, b in zip(points, points[1:]):
        draw_segment(a, b)


# Route: straight -> two smooth bends -> straight -> sharp 90-degree turn.
draw_segment((-3.5, -1.8), (-2.0, -1.8))          # Straight start
draw_curve(-2.0, 0.0, -1.8, +0.65)              # Gentle upward bend
draw_curve(0.0, 2.0, -1.8, -0.50)               # Gentle downward bend
draw_segment((2.0, -1.8), (3.0, -1.8))          # Straight approach
draw_segment((3.0, -1.8), (3.0, 2.4))           # Sharp 90-degree turn

output_path = Path(__file__).resolve().with_name("line_follow.sdf")
xml_bytes = ET.tostring(sdf, encoding="utf-8")
pretty_xml = minidom.parseString(xml_bytes).toprettyxml(indent="  ")
output_path.write_text(pretty_xml, encoding="utf-8")
print(f"Created {output_path} with {segment_count} tape visuals, width {TAPE_WIDTH_M * 100:.1f} cm")
