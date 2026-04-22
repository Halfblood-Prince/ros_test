from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
import os

def generate_launch_description():

    world = os.path.join(
        os.path.dirname(__file__),
        '..',
        'worlds',
        'test.sdf'
    )

    return LaunchDescription([

        # Start Gazebo Sim (NEW)
        ExecuteProcess(
            cmd=['gz', 'sim', '-r', world],
            output='screen'
        ),

        # Robot state publisher (unchanged concept)
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'use_sim_time': True,
                'robot_description': open(
                    os.path.join(
                        os.path.dirname(__file__),
                        '..',
                        'urdf',
                        'cube_robot.xacro'
                    )
                ).read()
            }],
            output='screen'
        ),

    ])