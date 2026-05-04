from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare("ros_test")
    world = LaunchConfiguration("world")
    gui_config = LaunchConfiguration("gui_config")
    gz_args = LaunchConfiguration("gz_args")
    auto_drive_enabled = LaunchConfiguration("auto_drive")

    default_world = PathJoinSubstitution([pkg_share, "robot.sdf"])
    default_gui_config = PathJoinSubstitution([pkg_share, "config", "gazebo_teleop.config"])
    slam_params = PathJoinSubstitution([pkg_share, "config", "slam_toolbox.yaml"])
    rviz_config = PathJoinSubstitution([pkg_share, "rviz", "slam.rviz"])

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"])
        ),
        launch_arguments={
            "gz_args": [gz_args, " ", world, " --gui-config ", gui_config],
        }.items(),
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="ros_gz_bridge",
        output="screen",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            "/imu@sensor_msgs/msg/Imu[gz.msgs.IMU",
            "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
        ],
    )

    odom_to_tf = Node(
        package="ros_test",
        executable="odom_to_tf",
        name="odom_to_tf",
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    lidar_static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="lidar_static_tf",
        output="screen",
        arguments=[
            "--x", "0.45",
            "--y", "0.0",
            "--z", "0.32",
            "--roll", "0.0",
            "--pitch", "0.0",
            "--yaw", "0.0",
            "--frame-id", "chassis",
            "--child-frame-id", "vehicle_blue/chassis/gpu_lidar",
        ],
    )

    slam_toolbox = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        output="screen",
        parameters=[slam_params, {"use_sim_time": True}],
        remappings=[("scan", "/scan")],
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": True}],
    )

    map_monitor = Node(
        package="ros_test",
        executable="map_monitor",
        name="map_monitor",
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    auto_drive = Node(
        package="ros_test",
        executable="auto_drive",
        name="auto_drive",
        output="screen",
        parameters=[{"use_sim_time": True}],
        condition=IfCondition(auto_drive_enabled),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "world",
                default_value=default_world,
                description="Gazebo SDF world to load.",
            ),
            DeclareLaunchArgument(
                "gui_config",
                default_value=default_gui_config,
                description="Gazebo GUI config with the Teleop panel.",
            ),
            DeclareLaunchArgument(
                "gz_args",
                default_value="-r",
                description="Arguments passed to gz sim before the world path.",
            ),
            DeclareLaunchArgument(
                "auto_drive",
                default_value="false",
                description="Set true to make the robot drive itself.",
            ),
            gazebo,
            bridge,
            odom_to_tf,
            lidar_static_tf,
            TimerAction(period=2.0, actions=[slam_toolbox, map_monitor, auto_drive]),
            TimerAction(period=4.0, actions=[rviz]),
        ]
    )
