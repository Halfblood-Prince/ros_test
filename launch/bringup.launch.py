from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory, PackageNotFoundError
import os
import sys


def generate_launch_description():
    use_gazebo = LaunchConfiguration('use_gazebo')
    use_gz_keyboard = LaunchConfiguration('use_gz_keyboard')
    use_slam = LaunchConfiguration('use_slam')

    ld = LaunchDescription()
    ld.add_action(DeclareLaunchArgument(
        'use_gazebo', default_value='false',
        description='Whether to start Gazebo and spawn the robot (true/false)'))

    ld.add_action(DeclareLaunchArgument(
        'use_gz_keyboard', default_value='false',
        description='Whether to start the keyboard_control node in topic mode to accept gz-keypress inputs'))

    ld.add_action(DeclareLaunchArgument(
        'use_slam', default_value='true',
        description='Whether to start the slam_toolbox node (true/false)'))

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

    # SLAM (optional) — only add if package is available
    try:
        slam_share = get_package_share_directory('slam_toolbox')
    except PackageNotFoundError:
        slam_share = None

    if slam_share:
        ld.add_action(Node(
            package='slam_toolbox',
            executable='sync_slam_toolbox_node',
            name='slam_toolbox',
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(use_slam),
        ))
    else:
        ld.add_action(LogInfo(msg='slam_toolbox package not found; SLAM node will not be launched.'))

    # Optional: start keyboard_control in topic mode so it can receive
    # keypresses forwarded from Gazebo (e.g. via ros_ign_bridge).
    # If the installed console script isn't present (dev workspace not built),
    # fall back to running the source script directly if available.
    try:
        pkg_share = get_package_share_directory('cube')
    except PackageNotFoundError:
        pkg_share = None

    keyboard_launched = False
    if pkg_share:
        # compute package install prefix (e.g., /.../install/cube)
        prefix = os.path.abspath(os.path.join(pkg_share, os.pardir, os.pardir))
        lib_dir = os.path.join(prefix, 'lib', 'cube')
        if os.path.isdir(lib_dir):
            # installed ament_python console scripts live under <prefix>/lib/<package>
            ld.add_action(Node(
                package='cube',
                executable='keyboard_control',
                name='keyboard_control',
                parameters=[{'input_topic': '/keyboard'}],
                output='screen',
                condition=IfCondition(use_gz_keyboard)
            ))
            keyboard_launched = True

    if not keyboard_launched:
        # try to find the source script next to this launch file
        keyboard_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'keyboard_control.py'))
        if os.path.exists(keyboard_script):
            ld.add_action(ExecuteProcess(
                cmd=[sys.executable, keyboard_script, '--ros-args', '--params-file', ''],
                name='keyboard_control',
                output='screen',
                condition=IfCondition(use_gz_keyboard)
            ))
        else:
            ld.add_action(LogInfo(msg='keyboard_control executable not found; not launching keyboard_control.'))

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
