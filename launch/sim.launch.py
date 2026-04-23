import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, SetEnvironmentVariable, TimerAction
from launch.conditions import IfCondition
from launch_ros.actions import Node
from launch.substitutions import Command, EnvironmentVariable, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('cuboid_robot_description')
    use_rviz = LaunchConfiguration('use_rviz')
    use_slam = LaunchConfiguration('use_slam')
    use_teleop = LaunchConfiguration('use_teleop')
    teleop_terminal = LaunchConfiguration('teleop_terminal')

    world = PathJoinSubstitution([pkg_share, 'worlds', 'sample_world.sdf'])
    robot_file = PathJoinSubstitution([pkg_share, 'urdf', 'cuboid_robot.urdf.xacro'])
    slam_params = PathJoinSubstitution([pkg_share, 'config', 'slam_toolbox.yaml'])
    rviz_config = PathJoinSubstitution([pkg_share, 'rviz', 'mapping.rviz'])

    robot_description = Command([
        FindExecutable(name='xacro'),
        ' ',
        robot_file
    ])

    gazebo_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[
            pkg_share,
            os.pathsep,
            EnvironmentVariable('GZ_SIM_RESOURCE_PATH', default_value='')
        ]
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True
        }],
        output='screen'
    )

    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world],
        output='screen'
    )

    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'cuboid_robot',
            '-z', '0.5'
        ],
        output='screen'
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry'
        ],
        output='screen'
    )

    teleop = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        prefix=[teleop_terminal, ' '],
        condition=IfCondition(use_teleop),
        emulate_tty=True,
        output='screen'
    )

    slam = Node(
        package='slam_toolbox',
        executable='sync_slam_toolbox_node',
        name='slam_toolbox',
        condition=IfCondition(use_slam),
        output='screen',
        parameters=[slam_params]
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        condition=IfCondition(use_rviz),
        arguments=['-d', rviz_config],
        output='screen'
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('use_slam', default_value='true'),
        DeclareLaunchArgument('use_teleop', default_value='false'),
        DeclareLaunchArgument('teleop_terminal', default_value='xterm -e'),
        gazebo_resource_path,
        gazebo,
        robot_state_publisher,
        TimerAction(period=2.0, actions=[spawn_entity]),
        TimerAction(period=2.5, actions=[bridge]),
        TimerAction(period=3.0, actions=[teleop, slam, rviz])
    ])
