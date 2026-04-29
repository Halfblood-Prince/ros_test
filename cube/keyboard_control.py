import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
import sys
import threading

# termios/tty are only available on Unix-like systems. Import lazily and
# handle missing modules (e.g., on Windows) so the node can still be used
# when keypresses are provided via a ROS topic.
try:
    import termios
    import tty
except Exception:
    termios = None
    tty = None


class KeyboardControl(Node):
    def __init__(self):
        super().__init__('keyboard_control')

        # Publisher for cmd_vel
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Parameter: name of topic to receive keypresses (std_msgs/String).
        # If empty, the node will read from the local terminal (Unix only).
        self.declare_parameter('input_topic', '')
        input_topic = self.get_parameter('input_topic').get_parameter_value().string_value

        self._running = False
        self._thread = None
        self.settings = None

        if input_topic:
            # Subscribe to a topic providing single-character keypresses
            self.create_subscription(String, input_topic, self._topic_key_cb, 10)
            self.get_logger().info(f"Subscribed to key topic: '{input_topic}'")
        else:
            # Terminal mode: require termios/tty
            if termios is None or tty is None:
                self.get_logger().error('Terminal input is not supported on this platform; set parameter "input_topic" to use topic-based key input.')
                raise RuntimeError('termios/tty not available')

            try:
                fd = sys.stdin.fileno()
                self.settings = termios.tcgetattr(fd)
            except Exception as e:
                self.get_logger().warning(f'Could not get terminal settings: {e}')
                self.settings = None

            # Start background thread to read stdin so rclpy.spin() can run
            self._running = True
            self._thread = threading.Thread(target=self._keyboard_loop, daemon=True)
            self._thread.start()

    def _topic_key_cb(self, msg: String):
        key = msg.data
        if not key:
            return
        # Use only first character
        self._handle_key(key[0])

    def _keyboard_loop(self):
        fd = sys.stdin.fileno()
        while self._running and rclpy.ok():
            try:
                key = self._get_key_from_terminal(fd)
            except Exception as e:
                self.get_logger().error(f'Error reading key: {e}')
                break
            if key:
                self._handle_key(key)

        # restore terminal on exit
        if self.settings is not None:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, self.settings)
            except Exception:
                pass

    def _get_key_from_terminal(self, fd: int):
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if self.settings is not None:
            termios.tcsetattr(fd, termios.TCSADRAIN, self.settings)
        return ch

    def _handle_key(self, key: str):
        msg = Twist()

        if key == 'w':
            msg.linear.x = 1.0
        elif key == 's':
            msg.linear.x = -1.0
        elif key == 'a':
            msg.angular.z = 1.0
        elif key == 'd':
            msg.angular.z = -1.0
        elif key == ' ' or key == 'x':
            # stop
            msg.linear.x = 0.0
            msg.angular.z = 0.0
        elif key == 'q':
            # quit request
            self.get_logger().info('Quit received, stopping keyboard control')
            self.stop()
            return

        self.pub.publish(msg)

    def stop(self):
        self._running = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.0)


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = KeyboardControl()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            try:
                node.stop()
            except Exception:
                pass
            node.destroy_node()
        rclpy.shutdown()
