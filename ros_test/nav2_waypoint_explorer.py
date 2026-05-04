import math

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node


class Nav2WaypointExplorer(Node):
    def __init__(self):
        super().__init__("nav2_waypoint_explorer")
        self._client = ActionClient(self, NavigateToPose, "navigate_to_pose")
        self._waypoints = [
            (-5.4, 2.8, 0.0),
            (-5.4, -2.8, -1.57),
            (-1.5, -3.0, 0.0),
            (1.0, 0.0, 1.57),
            (0.0, 8.8, 1.57),
            (4.8, 1.6, 0.0),
            (9.2, 1.8, -1.57),
            (9.2, -1.8, 3.14),
            (3.8, -3.6, 3.14),
            (-2.5, 0.8, 2.4),
        ]
        self._index = 0
        self._active = False
        self.create_timer(2.0, self._maybe_send_goal)

    def _maybe_send_goal(self):
        if self._active:
            return
        if not self._client.wait_for_server(timeout_sec=0.1):
            self.get_logger().info("Waiting for Nav2 navigate_to_pose action server")
            return

        x, y, yaw = self._waypoints[self._index]
        goal = NavigateToPose.Goal()
        goal.pose = self._make_pose(x, y, yaw)
        self.get_logger().info(
            f"Sending Nav2 exploration goal {self._index + 1}/{len(self._waypoints)}: "
            f"x={x:.2f}, y={y:.2f}, yaw={yaw:.2f}"
        )
        self._active = True
        future = self._client.send_goal_async(goal)
        future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn("Nav2 goal rejected; trying the next waypoint")
            self._advance()
            return

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_callback)

    def _result_callback(self, future):
        status = future.result().status
        self.get_logger().info(f"Nav2 goal finished with status {status}")
        self._advance()

    def _advance(self):
        self._index = (self._index + 1) % len(self._waypoints)
        self._active = False

    def _make_pose(self, x, y, yaw):
        pose = PoseStamped()
        pose.header.frame_id = "map"
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        return pose


def main(args=None):
    rclpy.init(args=args)
    node = Nav2WaypointExplorer()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
