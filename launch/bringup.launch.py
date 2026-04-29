from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory, PackageNotFoundError
import os


def generate_launch_description():
    use_gazebo = LaunchConfiguration('use_gazebo')
    use_gz_keyboard = LaunchConfiguration('use_gz_keyboard')

    ld = LaunchDescription()
    ld.add_action(DeclareLaunchArgument(
        'use_gazebo', default_value='false',
        description='Whether to start Gazebo and spawn the robot (true/false)'))

    ld.add_action(DeclareLaunchArgument(
        'use_gz_keyboard', default_value='false',
        description='Whether to start the keyboard_control node in topic mode to accept gz-keypress inputs'))

    # Conditionally include Gazebo (only if the package exists and the arg is true)
    try:
        gazebo_share = get_package_share_directory('gazebo_ros')
    except PackageNotFoundError:
        gazebo_share = None

    if gazebo_share:
        ld.add_action(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(gazebo_share, 'launch', 'gazebo.launch.py')),
            condition=IfCondition(use_gazebo)
        ))

        ld.add_action(Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=['-topic', 'robot_description', '-entity', 'cube'],
            output='screen',
            condition=IfCondition(use_gazebo)
        ))
    else:
        ld.add_action(LogInfo(msg='gazebo_ros package not found; Gazebo-related nodes will not be launched.'))

    # SLAM
    ld.add_action(Node(
        package='slam_toolbox',
        executable='sync_slam_toolbox_node',
        parameters=[{'use_sim_time': True}],
    ))

    # Optional: start keyboard_control in topic mode so it can receive
    # keypresses forwarded from Gazebo (e.g. via ros_ign_bridge).
    ld.add_action(Node(
        package='cube',
        executable='keyboard_control',
        name='keyboard_control',
        parameters=[{'input_topic': '/keyboard'}],
        output='screen',
        condition=IfCondition(use_gz_keyboard)
    ))

    # RViz - prefer installed package share, fallback to relative path
    try:
        pkg_share = get_package_share_directory('cube')
        rviz_config = os.path.join(pkg_share, 'rviz', 'config.rviz')
    except PackageNotFoundError:
        rviz_config = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rviz', 'config.rviz'))

    ld.add_action(Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config]
    ))

    return ld
