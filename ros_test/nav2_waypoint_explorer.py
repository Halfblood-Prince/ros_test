import math

import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformException, TransformListener


class Nav2WaypointExplorer(Node):
    def __init__(self):
        super().__init__("nav2_waypoint_explorer")
        self._client = ActionClient(self, NavigateToPose, "navigate_to_pose")
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)
        self._map = None
        self._active = False
        self._goal_count = 0
        self._current_goal = None
        self._failed_goals = []
        self.create_subscription(OccupancyGrid, "/map", self._handle_map, 10)
        self.create_timer(3.0, self._maybe_send_goal)

    def _handle_map(self, msg):
        self._map = msg

    def _maybe_send_goal(self):
        if self._active:
            return
        if self._map is None:
            self.get_logger().info("Waiting for /map before choosing Nav2 exploration goals")
            return
        if not self._client.wait_for_server(timeout_sec=0.1):
            self.get_logger().info("Waiting for Nav2 navigate_to_pose action server")
            return

        robot = self._robot_pose()
        if robot is None:
            return

        target = self._choose_frontier_goal(robot)
        if target is None:
            self.get_logger().info("No safe nearby free/frontier cell found yet; waiting for map growth")
            return

        x, y = target
        yaw = math.atan2(y - robot[1], x - robot[0])
        goal = NavigateToPose.Goal()
        goal.pose = self._make_pose(x, y, yaw)
        self._goal_count += 1
        self.get_logger().info(
            f"Sending Nav2 map-local exploration goal {self._goal_count}: "
            f"x={x:.2f}, y={y:.2f}, yaw={yaw:.2f}"
        )
        self._active = True
        self._current_goal = (x, y)
        future = self._client.send_goal_async(goal)
        future.add_done_callback(self._goal_response_callback)

    def _robot_pose(self):
        try:
            transform = self._tf_buffer.lookup_transform("map", "base_link", Time())
        except TransformException as exc:
            self.get_logger().info(f"Waiting for map -> base_link TF: {exc}")
            return None

        return (
            transform.transform.translation.x,
            transform.transform.translation.y,
        )

    def _choose_frontier_goal(self, robot):
        best = None
        best_score = -1.0
        radii = (0.9, 1.2, 1.5, 1.8, 2.1)
        angle_steps = 24

        for radius in radii:
            for step in range(angle_steps):
                angle = 2.0 * math.pi * step / angle_steps
                x = robot[0] + radius * math.cos(angle)
                y = robot[1] + radius * math.sin(angle)
                cell = self._world_to_cell(x, y)
                if cell is None or not self._is_safe_free_cell(*cell):
                    continue
                if self._recently_failed(x, y):
                    continue

                frontier_score = self._unknown_neighbor_count(*cell)
                distance_score = radius * 0.2
                score = frontier_score + distance_score
                if score > best_score:
                    best = (x, y)
                    best_score = score

        return best

    def _world_to_cell(self, x, y):
        grid = self._map
        resolution = grid.info.resolution
        origin = grid.info.origin.position
        mx = int((x - origin.x) / resolution)
        my = int((y - origin.y) / resolution)
        if mx < 0 or my < 0 or mx >= grid.info.width or my >= grid.info.height:
            return None
        return mx, my

    def _cell_value(self, mx, my):
        return self._map.data[my * self._map.info.width + mx]

    def _is_safe_free_cell(self, mx, my):
        grid = self._map
        clearance_cells = max(2, int(0.45 / grid.info.resolution))
        for dy in range(-clearance_cells, clearance_cells + 1):
            for dx in range(-clearance_cells, clearance_cells + 1):
                x = mx + dx
                y = my + dy
                if x < 0 or y < 0 or x >= grid.info.width or y >= grid.info.height:
                    return False
                value = self._cell_value(x, y)
                if value < 0 or value >= 50:
                    return False
        return True

    def _unknown_neighbor_count(self, mx, my):
        grid = self._map
        radius = max(4, int(0.7 / grid.info.resolution))
        count = 0
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                x = mx + dx
                y = my + dy
                if x < 0 or y < 0 or x >= grid.info.width or y >= grid.info.height:
                    continue
                if self._cell_value(x, y) < 0:
                    count += 1
        return count

    def _recently_failed(self, x, y):
        return any(math.hypot(x - fx, y - fy) < 0.5 for fx, fy in self._failed_goals[-12:])

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn("Nav2 goal rejected; choosing a new map-local goal")
            if self._current_goal is not None:
                self._failed_goals.append(self._current_goal)
            self._current_goal = None
            self._active = False
            return

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_callback)

    def _result_callback(self, future):
        result = future.result()
        status = result.status
        self.get_logger().info(f"Nav2 goal finished with status {status}")
        if status != 4 and self._current_goal is not None:
            self._failed_goals.append(self._current_goal)
        self._current_goal = None
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
