import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


class OdomToTf(Node):
    def __init__(self):
        super().__init__("odom_to_tf")
        self._broadcaster = TransformBroadcaster(self)
        self.create_subscription(Odometry, "/odom", self._handle_odom, 10)

    def _handle_odom(self, msg):
        transform = TransformStamped()
        transform.header = msg.header
        if not transform.header.frame_id:
            transform.header.frame_id = "odom"
        transform.child_frame_id = msg.child_frame_id or "chassis"
        transform.transform.translation.x = msg.pose.pose.position.x
        transform.transform.translation.y = msg.pose.pose.position.y
        transform.transform.translation.z = msg.pose.pose.position.z
        transform.transform.rotation = msg.pose.pose.orientation
        self._broadcaster.sendTransform(transform)


def main(args=None):
    rclpy.init(args=args)
    node = OdomToTf()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
