import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys, termios, tty

class KeyboardControl(Node):
    def __init__(self):
        super().__init__('keyboard_control')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

    def get_key(self):
        tty.setraw(sys.stdin.fileno())
        key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        return key

    def run(self):
        while True:
            key = self.get_key()
            msg = Twist()

            if key == 'w':
                msg.linear.x = 1.0
            elif key == 's':
                msg.linear.x = -1.0
            elif key == 'a':
                msg.angular.z = 1.0
            elif key == 'd':
                msg.angular.z = -1.0

            self.pub.publish(msg)

def main():
    global settings
    settings = termios.tcgetattr(sys.stdin)

    rclpy.init()
    node = KeyboardControl()
    node.run()
    node.destroy_node()
    rclpy.shutdown()