Cube single-package ROS 2 workspace

This repository has been reorganized into a single ROS 2 package named `cube`.

Build (Linux/macOS):

```bash
source /opt/ros/jazzy/setup.bash
colcon build --packages-select cube
source install/setup.bash
```

Build (Windows PowerShell):

```powershell
rem Replace with your ROS2 installation setup script
colcon build --packages-select cube
```

Run bringup (after sourcing install):

```bash
# Launch without Gazebo (default)
ros2 launch cube bringup.launch.py

# Launch with Gazebo (only if you have Gazebo and the gazebo_ros package available)
ros2 launch cube bringup.launch.py use_gazebo:=true
```

Run keyboard control node:

```bash
ros2 run cube keyboard_control

Using Gazebo keyboard (gz-keypress)

- Start bringup with Gazebo and enable the topic-mode keyboard node:

```bash
ros2 launch cube bringup.launch.py use_gazebo:=true use_gz_keyboard:=true
```

- The launched `keyboard_control` node will subscribe to the `/keyboard` topic.
	Forward Gazebo key events to that topic (for example using `ros_ign_bridge`),
	or test manually by publishing single-character messages:

```bash
ros2 topic pub /keyboard std_msgs/msg/String "data: 'w'" --once
```

- When running Gazebo, you can use a keypress tool (e.g. the `gz keyboard` utility
	or a Gazebo plugin) to emit key events; bridge those events into ROS on the
	`/keyboard` topic so the node receives them.

Installing slam_toolbox

If you see an error about `package 'slam_toolbox' not found` when launching, install the package for your ROS 2 distribution. On Debian/Ubuntu:

```bash
# replace <distro> with your ROS 2 distro, e.g. humble, iron
sudo apt update
sudo apt install ros-<distro>-slam-toolbox
```

Alternatively, install missing package dependencies with `rosdep` from your workspace root:

```bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

You can also disable SLAM in the bringup launch if you don't need it:

```bash
ros2 launch cube bringup.launch.py use_slam:=false
```
```
