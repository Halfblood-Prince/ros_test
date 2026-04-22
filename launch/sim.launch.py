from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
from launch.substitutions import Command
import os

def generate_launch_description():

    world = os.path.join(
        os.path.dirname(__file__),
        '..',
        'worlds',
        'test.world'
    )

    urdf_file = os.path.join(
        os.path.dirname(__file__),
        '..',
        'urdf',
        'cube_robot.xacro'
    )

    return LaunchDescription([

        # Start Gazebo Sim
        ExecuteProcess(
            cmd=['gz', 'sim', '-r', world],
            output='screen'
        ),

        # Robot state publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'use_sim_time': True,
                'robot_description': Command(['xacro ', urdf_file])
            }],
            output='screen'
        ),

    ])