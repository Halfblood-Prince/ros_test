from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():

    return LaunchDescription([

        # Gazebo
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                '/opt/ros/jazzy/share/gazebo_ros/launch/gazebo.launch.py'
            )
        ),

        # Spawn robot
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=['-topic', 'robot_description', '-entity', 'cube'],
            output='screen'
        ),

        # SLAM
        Node(
            package='slam_toolbox',
            executable='sync_slam_toolbox_node',
            parameters=[{'use_sim_time': True}],
        ),

        # RViz
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', 'src/cube_bringup/rviz/config.rviz']
        )
    ])