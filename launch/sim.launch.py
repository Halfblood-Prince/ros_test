from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
import os

def generate_launch_description():

    world = os.path.join(
        os.path.dirname(__file__),
        '..',
        'worlds',
        'test.world'
    )

    return LaunchDescription([

        ExecuteProcess(
            cmd=['gazebo', '--verbose', world, '-s', 'libgazebo_ros_init.so'],
            output='screen'
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'use_sim_time': True}],
            arguments=[os.path.join(
                os.path.dirname(__file__),
                '..',
                'urdf',
                'cube_robot.xacro'
            )]
        ),

    ])