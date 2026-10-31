"""
Jembatan opsional ke ROS 2 supaya data robot bisa dilihat di RViz2.

Aktif otomatis jika rclpy bisa di-import (Webots dijalankan dari terminal yang sudah
`source /opt/ros/<distro>/setup.bash`, lihat tools/rviz.sh). Jika tidak ada ROS 2,
controller tetap berjalan normal tanpa bridge.

Topic yang dipublish:
  /scan          sensor_msgs/LaserScan      scan Lidar 360 derajat (frame: lidar)
  /odom          nav_msgs/Odometry          odometri dari encoder roda (frame: odom)
  /oa/decision   visualization_msgs/MarkerArray  koridor & arah yang dipilih + state
  TF             odom -> base_link -> lidar
"""

import math

import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster
from visualization_msgs.msg import Marker, MarkerArray

STATE_COLORS = {'JELAJAH': (0.12, 0.62, 0.33), 'MUNDUR': (0.78, 0.06, 0.18), 'PUTAR': (0.04, 0.36, 0.68)}


def _quat_z(yaw):
    return 0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0)


class RosBridge:
    def __init__(self, lidar_height, n_rays, fov, min_range, max_range):
        rclpy.init(args=None)
        self.node = Node('webots_obstacle_avoidance')
        self.pub_scan = self.node.create_publisher(LaserScan, 'scan', 10)
        self.pub_odom = self.node.create_publisher(Odometry, 'odom', 10)
        self.pub_dec = self.node.create_publisher(MarkerArray, 'oa/decision', 10)
        self.tf = TransformBroadcaster(self.node)
        self.static_tf = StaticTransformBroadcaster(self.node)
        self.n_rays, self.fov = n_rays, fov
        self.min_range, self.max_range = min_range, max_range

        t = TransformStamped()
        t.header.stamp = self.node.get_clock().now().to_msg()
        t.header.frame_id = 'base_link'
        t.child_frame_id = 'lidar'
        t.transform.translation.z = lidar_height
        t.transform.rotation.w = 1.0
        self.static_tf.sendTransform(t)
        self.node.get_logger().info('ROS 2 bridge aktif: /scan /odom /oa/decision + TF')

    def publish(self, raw_ranges, x, y, yaw, v, w, state, theta, free, half_width):
        now = self.node.get_clock().now().to_msg()

        # TF odom -> base_link
        q = _quat_z(yaw)
        t = TransformStamped()
        t.header.stamp = now
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = x
        t.transform.translation.y = y
        t.transform.rotation.x, t.transform.rotation.y, t.transform.rotation.z, t.transform.rotation.w = q
        self.tf.sendTransform(t)

        od = Odometry()
        od.header.stamp = now
        od.header.frame_id = 'odom'
        od.child_frame_id = 'base_link'
        od.pose.pose.position.x = x
        od.pose.pose.position.y = y
        o = od.pose.pose.orientation
        o.x, o.y, o.z, o.w = q
        od.twist.twist.linear.x = v
        od.twist.twist.angular.z = w
        self.pub_odom.publish(od)

        # LaserScan. Webots: indeks i bersudut pi - i*step (menurun). ROS butuh sudut
        # naik berlawanan jarum jam, jadi urutan dibalik: angle_min = -pi + step.
        step = self.fov / self.n_rays
        sc = LaserScan()
        sc.header.stamp = now
        sc.header.frame_id = 'lidar'
        sc.angle_min = -self.fov / 2.0 + step
        sc.angle_increment = step
        sc.angle_max = sc.angle_min + step * (self.n_rays - 1)
        sc.range_min = self.min_range
        sc.range_max = self.max_range
        sc.ranges = [float(r) for r in reversed(raw_ranges)]
        self.pub_scan.publish(sc)

        # Marker: koridor yang dipilih + teks state
        r, g, b = STATE_COLORS.get(state, (0.5, 0.5, 0.5))
        ma = MarkerArray()
        corr = Marker()
        corr.header.stamp = now
        corr.header.frame_id = 'base_link'
        corr.ns, corr.id, corr.type, corr.action = 'koridor', 0, Marker.CUBE, Marker.ADD
        length = max(0.02, free)
        corr.pose.position.x = math.cos(theta) * length / 2.0
        corr.pose.position.y = math.sin(theta) * length / 2.0
        corr.pose.position.z = 0.0
        cq = _quat_z(theta)
        corr.pose.orientation.x, corr.pose.orientation.y, corr.pose.orientation.z, corr.pose.orientation.w = cq
        corr.scale.x, corr.scale.y, corr.scale.z = length, 2.0 * half_width, 0.01
        corr.color.r, corr.color.g, corr.color.b, corr.color.a = r, g, b, 0.35
        ma.markers.append(corr)

        arrow = Marker()
        arrow.header = corr.header
        arrow.ns, arrow.id, arrow.type, arrow.action = 'arah', 1, Marker.ARROW, Marker.ADD
        arrow.pose.orientation = corr.pose.orientation
        arrow.pose.position.z = 0.02
        arrow.scale.x, arrow.scale.y, arrow.scale.z = max(0.05, min(free, 0.6)), 0.025, 0.025
        arrow.color.r, arrow.color.g, arrow.color.b, arrow.color.a = r, g, b, 1.0
        ma.markers.append(arrow)

        txt = Marker()
        txt.header = corr.header
        txt.ns, txt.id, txt.type, txt.action = 'state', 2, Marker.TEXT_VIEW_FACING, Marker.ADD
        txt.pose.position.z = 0.25
        txt.pose.orientation.w = 1.0
        txt.scale.z = 0.08
        txt.color.r, txt.color.g, txt.color.b, txt.color.a = r, g, b, 1.0
        txt.text = f'{state}  v={v:.2f} m/s'
        ma.markers.append(txt)
        self.pub_dec.publish(ma)

    def shutdown(self):
        self.node.destroy_node()
        rclpy.try_shutdown()
