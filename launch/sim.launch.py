
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    x = LaunchConfiguration('x', default='0.0')
    y = LaunchConfiguration('y', default='0.0')
    z = LaunchConfiguration('z', default='0.2')
    world = PathJoinSubstitution([FindPackageShare('cuboid_robot_description'), 'worlds', 'sample_world.sdf'])
    robot_desc = Command(['xacro ', PathJoinSubstitution([FindPackageShare('cuboid_robot_description'), 'urdf', 'cuboid_robot.urdf.xacro'])])
    gz = IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'])), launch_arguments={'gz_args': ['-r ', world]}.items())
    rsp = Node(package='robot_state_publisher', executable='robot_state_publisher', parameters=[{'robot_description': robot_desc, 'use_sim_time': use_sim_time}], output='screen')
    spawn = Node(package='ros_gz_sim', executable='create', arguments=['-name','cuboid_robot','-topic','robot_description','-x',x,'-y',y,'-z',z], output='screen')
    bridge = Node(package='ros_gz_bridge', executable='parameter_bridge', arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock]','/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan]'], output='screen')
    slam = Node(package='slam_toolbox', executable='async_slam_toolbox_node', parameters=[PathJoinSubstitution([FindPackageShare('cuboid_robot_description'),'config','slam_toolbox.yaml']), {'use_sim_time': use_sim_time}], output='screen')
    rviz = Node(package='rviz2', executable='rviz2', arguments=['-d', PathJoinSubstitution([FindPackageShare('cuboid_robot_description'),'rviz','mapping.rviz'])], parameters=[{'use_sim_time': use_sim_time}], output='screen')
    return LaunchDescription([DeclareLaunchArgument('x', default_value='0.0'),DeclareLaunchArgument('y', default_value='0.0'),DeclareLaunchArgument('z', default_value='0.2'),gz,rsp,spawn,bridge,slam,rviz])
