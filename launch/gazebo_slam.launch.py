from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition, UnlessCondition
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
    mapper = LaunchConfiguration("mapper")
    nav2_enabled = LaunchConfiguration("nav2")

    default_world = PathJoinSubstitution([pkg_share, "robot.sdf"])
    default_gui_config = PathJoinSubstitution([pkg_share, "config", "gazebo_teleop.config"])
    slam_params = PathJoinSubstitution([pkg_share, "config", "slam_toolbox.yaml"])
    nav2_params = PathJoinSubstitution([pkg_share, "config", "nav2_params.yaml"])
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
            "/scan_raw@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
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

    scan_to_chassis = Node(
        package="ros_test",
        executable="scan_to_chassis",
        name="scan_to_chassis",
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    simple_mapper = Node(
        package="ros_test",
        executable="simple_mapper",
        name="simple_mapper",
        output="screen",
        parameters=[{"use_sim_time": True}],
        condition=IfCondition(mapper),
    )

    slam_toolbox = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("slam_toolbox"), "launch", "online_async_launch.py"]
            )
        ),
        launch_arguments={
            "slam_params_file": slam_params,
            "use_sim_time": "true",
        }.items(),
        condition=UnlessCondition(mapper),
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": True}],
    )

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("nav2_bringup"), "launch", "navigation_launch.py"])
        ),
        launch_arguments={
            "use_sim_time": "true",
            "params_file": nav2_params,
            "autostart": "true",
        }.items(),
        condition=IfCondition(nav2_enabled),
    )

    nav2_explorer = Node(
        package="ros_test",
        executable="nav2_waypoint_explorer",
        name="nav2_waypoint_explorer",
        output="screen",
        parameters=[{"use_sim_time": True}],
        condition=IfCondition(nav2_enabled),
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
            DeclareLaunchArgument(
                "mapper",
                default_value="false",
                description="Set true to use the simple odom mapper instead of slam_toolbox.",
            ),
            DeclareLaunchArgument(
                "nav2",
                default_value="false",
                description="Set true to launch Nav2 and send exploration waypoints.",
            ),
            gazebo,
            bridge,
            odom_to_tf,
            scan_to_chassis,
            TimerAction(period=2.0, actions=[slam_toolbox, simple_mapper, map_monitor, auto_drive]),
            TimerAction(period=8.0, actions=[nav2]),
            TimerAction(period=16.0, actions=[nav2_explorer]),
            TimerAction(period=4.0, actions=[rviz]),
        ]
    )
