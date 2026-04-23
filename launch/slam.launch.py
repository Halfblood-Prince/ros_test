from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    config = PathJoinSubstitution([
        FindPackageShare('cuboid_robot_description'),
        'config',
        'slam_toolbox.yaml'
    ])

    return LaunchDescription([
        Node(
            package='slam_toolbox',
            executable='sync_slam_toolbox_node',
            name='slam_toolbox',
            parameters=[config],
            output='screen'
        )
    ])
