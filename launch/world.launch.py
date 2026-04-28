from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
import os

from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_path = get_package_share_directory('lidar_ground_world')
    world = os.path.join(pkg_path, 'worlds', 'lidar_world.sdf')

    return LaunchDescription([

        # Start Gazebo
        ExecuteProcess(
            cmd=['gz', 'sim', world],
            output='screen'
        ),

        # Bridge lidar to ROS2
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/lidar@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan'
            ],
            output='screen'
        ),
    ])