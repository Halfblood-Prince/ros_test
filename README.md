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
ros2 launch cube bringup.launch.py
```

Run keyboard control node:

```bash
ros2 run cube keyboard_control
```
