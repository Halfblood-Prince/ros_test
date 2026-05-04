# ROS 2 Jazzy Gazebo Lidar SLAM Simulation

This package launches a Gazebo Harmonic simulation of a differential-drive lidar robot inside an extended building-like floor plan, bridges the simulated sensor data into ROS 2, runs `slam_toolbox`, and opens RViz.

## Install dependencies

```bash
sudo apt update
sudo apt install python3-colcon-common-extensions ros-jazzy-nav2-bringup ros-jazzy-ros-gz ros-jazzy-ros-gz-bridge ros-jazzy-ros-gz-sim ros-jazzy-rviz2 ros-jazzy-slam-toolbox ros-jazzy-tf2-ros
```

## Build

From the root of your ROS 2 workspace:

```bash
colcon build --symlink-install
source install/setup.bash
```

## Launch

```bash
ros2 launch ros_test gazebo_slam.launch.py
```

Gazebo opens with a floating Teleop panel, RViz opens with `/scan`, TF, and `/map` displays, and Nav2 sends nearby map-local goals so the robot scans rooms automatically without driving to coordinates outside the current SLAM map.

The launch starts:

- Gazebo Harmonic world: `robot.sdf`
- Gazebo Teleop GUI panel
- ROS-Gazebo bridge for `/clock`, `/scan_raw`, `/imu`, `/odom`, and ROS `/cmd_vel`
- scan republisher from `/scan_raw` to `/scan` with frame `base_link`
- `odom_to_tf`, publishing `odom -> base_link`
- `slam_toolbox`, publishing `/map` from `/scan` and TF
- RViz
- `map_monitor`, which reports when `/map` is received
- Nav2, publishing `/cmd_vel` from nearby free/frontier goals selected from `/map`

## Manual and Fallback Modes

To disable Nav2 and drive only from the Gazebo Teleop panel:

```bash
ros2 launch ros_test gazebo_slam.launch.py nav2:=false
```

For the simple wall-following driver instead of Nav2:

```bash
ros2 launch ros_test gazebo_slam.launch.py nav2:=false auto_drive:=true
```

For the older odom-only fallback mapper:

```bash
ros2 launch ros_test gazebo_slam.launch.py nav2:=false mapper:=true
```

If the RViz map appears to slide with the robot, make sure RViz Global Options uses fixed frame `map`, not `odom`. The robot should move in the map; the map should not move with the robot.

## Expected topics

```text
/scan_raw sensor_msgs/msg/LaserScan from Gazebo
/scan     sensor_msgs/msg/LaserScan with frame base_link
/imu     sensor_msgs/msg/Imu
/odom    nav_msgs/msg/Odometry
/map     nav_msgs/msg/OccupancyGrid
/cmd_vel geometry_msgs/msg/Twist
```

Move the robot for a few seconds before expecting a useful map. The simulated lidar range is 5 m, so the map expands as the robot explores nearby rooms and corridors.

During live SLAM, RViz may briefly show small pose corrections because `slam_toolbox` updates the `map -> odom` transform. The autonomous mode uses slow velocities and disables loop closure to keep those corrections from looking like large jumps while mapping.
