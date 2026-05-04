import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node


class MapMonitor(Node):
    def __init__(self):
        super().__init__("map_monitor")
        self._received_map = False
        self._seconds_waited = 0
        self.create_subscription(OccupancyGrid, "/map", self._handle_map, 10)
        self.create_timer(5.0, self._report_status)

    def _handle_map(self, msg):
        if self._received_map:
            return

        self._received_map = True
        self.get_logger().info(
            "Received /map from slam_toolbox "
            f"({msg.info.width}x{msg.info.height}, resolution {msg.info.resolution:.3f})"
        )

    def _report_status(self):
        if self._received_map:
            return

        self._seconds_waited += 5
        self.get_logger().warn(
            f"Still waiting for /map after {self._seconds_waited}s. "
            "Lidar, odom, and auto-drive may be running before slam_toolbox publishes."
        )


def main(args=None):
    rclpy.init(args=args)
    node = MapMonitor()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
