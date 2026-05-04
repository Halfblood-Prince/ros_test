from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_share = FindPackageShare("ros_test")
    world = LaunchConfiguration("world")
    gz_args = LaunchConfiguration("gz_args")
    gui_config = LaunchConfiguration("gui_config")
    auto_drive_enabled = LaunchConfiguration("auto_drive")

    default_world = PathJoinSubstitution([package_share, "robot.sdf"])
    default_gui_config = PathJoinSubstitution(
        [package_share, "config", "gazebo_teleop.config"]
    )
    rviz_config = PathJoinSubstitution([package_share, "rviz", "slam.rviz"])
    slam_params = {
        "use_sim_time": True,
        "mode": "mapping",
        "map_frame": "map",
        "odom_frame": "odom",
        "base_frame": "chassis",
        "scan_topic": "/scan",
        "throttle_scans": 1,
        "transform_publish_period": 0.02,
        "map_update_interval": 2.0,
        "resolution": 0.05,
        "max_laser_range": 10.0,
        "minimum_time_interval": 0.2,
        "transform_timeout": 0.5,
        "tf_buffer_duration": 30.0,
        "stack_size_to_use": 40000000,
        "use_scan_matching": True,
        "use_scan_barycenter": True,
        "minimum_travel_distance": 0.1,
        "minimum_travel_heading": 0.1,
        "scan_buffer_size": 10,
        "scan_buffer_maximum_scan_distance": 10.0,
        "solver_plugin": "solver_plugins::CeresSolver",
        "ceres_linear_solver": "SPARSE_NORMAL_CHOLESKY",
        "ceres_preconditioner": "SCHUR_JACOBI",
        "ceres_trust_strategy": "LEVENBERG_MARQUARDT",
        "ceres_dogleg_type": "TRADITIONAL_DOGLEG",
        "ceres_loss_function": "None",
    }

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"]
            )
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
            "--x",
            "0.8",
            "--y",
            "0.0",
            "--z",
            "0.5",
            "--roll",
            "0.0",
            "--pitch",
            "0.0",
            "--yaw",
            "0.0",
            "--frame-id",
            "chassis",
            "--child-frame-id",
            "vehicle_blue/chassis/gpu_lidar",
        ],
    )

    auto_drive = Node(
        package="ros_test",
        executable="auto_drive",
        name="auto_drive",
        output="screen",
        parameters=[{"use_sim_time": True}],
        condition=IfCondition(auto_drive_enabled),
    )

    map_monitor = Node(
        package="ros_test",
        executable="map_monitor",
        name="map_monitor",
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    slam_toolbox = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        output="screen",
        parameters=[slam_params],
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

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "world",
                default_value=default_world,
                description="Path to the Gazebo Harmonic SDF world file.",
            ),
            DeclareLaunchArgument(
                "gz_args",
                default_value="-r",
                description="Arguments passed to gz sim before the world path.",
            ),
            DeclareLaunchArgument(
                "gui_config",
                default_value=default_gui_config,
                description="Gazebo GUI config that opens the Teleop panel.",
            ),
            DeclareLaunchArgument(
                "auto_drive",
                default_value="false",
                description="Set true to make the robot drive itself with lidar obstacle avoidance.",
            ),
            gazebo,
            bridge,
            odom_to_tf,
            lidar_static_tf,
            TimerAction(period=2.0, actions=[slam_toolbox, auto_drive, map_monitor]),
            TimerAction(period=4.0, actions=[rviz]),
        ]
    )
