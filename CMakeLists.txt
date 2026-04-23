
cmake_minimum_required(VERSION 3.8)
project(cuboid_robot_description)
find_package(ament_cmake REQUIRED)
install(DIRECTORY launch urdf config worlds rviz scripts models DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/save_map.sh scripts/odom_to_tf.py DESTINATION lib/${PROJECT_NAME})
ament_package()
