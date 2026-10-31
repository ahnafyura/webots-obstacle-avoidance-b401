"""
Jembatan opsional ROS 2 untuk menampilkan SEMUA sensor humanoid di RViz2.

Aktif otomatis jika rclpy bisa di-import (Webots dijalankan dari terminal yang sudah
`source /opt/ros/jazzy/setup.bash`, lihat tools/rviz.sh). Tanpa ROS 2 controller tetap jalan.

Topic:
  /scan                 sensor_msgs/LaserScan      Lidar 360 di atas kepala
  /sonar/left, /right   sensor_msgs/Range          sonar dada
  /imu                  sensor_msgs/Imu            orientasi (InertialUnit) + gyro + accelerometer
  /fsr/left, /right     geometry_msgs/WrenchStamped  gaya tapak kaki (FSR)
  /camera/image_raw     sensor_msgs/Image          kamera atas NAO
  /joint_states         sensor_msgs/JointState     posisi 24 sendi (model robot bergerak di RViz)
  /odom                 nav_msgs/Odometry          GPS (posisi) + IMU (orientasi)
  /oa/decision          visualization_msgs/MarkerArray  koridor, arah tujuan, state, panel sensor
  TF                    odom -> base_link (+ URDF lewat robot_state_publisher)
"""

import math
import os

import rclpy
from geometry_msgs.msg import TransformStamped, WrenchStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Image, Imu, JointState, LaserScan, Range
from tf2_ros import TransformBroadcaster
from visualization_msgs.msg import Marker, MarkerArray

STATE_COLORS = {'JALAN': (0.12, 0.62, 0.33), 'JALAN_KIRI': (0.12, 0.62, 0.33),
                'JALAN_KANAN': (0.12, 0.62, 0.33), 'BERHENTI': (0.9, 0.55, 0.0),
                'MUNDUR': (0.78, 0.06, 0.18), 'PUTAR': (0.04, 0.36, 0.68),
                'MAJU_KECIL': (0.9, 0.55, 0.0), 'BANGUN': (0.6, 0.0, 0.6), 'SIAP': (0.5, 0.5, 0.5)}
PUBLISH_EVERY = 2          # publish tiap 2 step (25 Hz pada basicTimeStep 20 ms)
CAMERA_EVERY = 5           # kamera 10 Hz


def quat_rpy(roll, pitch, yaw):
    cr, sr = math.cos(roll / 2), math.sin(roll / 2)
    cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
    cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
    return (sr * cp * cy - cr * sp * sy, cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy, cr * cp * cy + sr * sp * sy)


class RosBridge:
    def __init__(self, ctl):
        self.c = ctl
        rclpy.init(args=None)
        n = self.node = Node('webots_humanoid_b401')
        self.pub = {
            'scan': n.create_publisher(LaserScan, 'scan', 10),
            'sl': n.create_publisher(Range, 'sonar/left', 10),
            'sr': n.create_publisher(Range, 'sonar/right', 10),
            'imu': n.create_publisher(Imu, 'imu', 10),
            'fl': n.create_publisher(WrenchStamped, 'fsr/left', 10),
            'fr': n.create_publisher(WrenchStamped, 'fsr/right', 10),
            'cam': n.create_publisher(Image, 'camera/image_raw', 2),
            'js': n.create_publisher(JointState, 'joint_states', 10),
            'odom': n.create_publisher(Odometry, 'odom', 10),
            'dec': n.create_publisher(MarkerArray, 'oa/decision', 10),
        }
        self.tf = TransformBroadcaster(n)
        # kamera butuh rendering; dimatikan otomatis saat Webots dijalankan --no-rendering
        self.camera = None
        if os.environ.get('OA_ROS_CAMERA', '1') != '0':
            self.camera = ctl.robot.getDevice('CameraTop')
            self.camera.enable(ctl.ts * CAMERA_EVERY)
        self.k = 0
        n.get_logger().info('ROS 2 bridge humanoid aktif (scan, sonar, imu, fsr, kamera, '
                            'joint_states, odom, TF, marker)')

    def _hdr(self, msg, frame, now):
        msg.header.stamp = now
        msg.header.frame_id = frame
        return msg

    def publish(self):
        self.k += 1
        if self.k % PUBLISH_EVERY:
            return
        c, now = self.c, self.node.get_clock().now().to_msg()
        x, y, z, roll, pitch, yaw = c.pose()
        if x != x:            # GPS belum siap (NaN)
            return
        q = quat_rpy(roll, pitch, yaw)

        # TF + odometri (posisi GPS, orientasi IMU). Frame odom = frame dunia arena.
        t = self._hdr(TransformStamped(), 'odom', now)
        t.child_frame_id = 'base_link'
        t.transform.translation.x, t.transform.translation.y, t.transform.translation.z = x, y, z
        r = t.transform.rotation
        r.x, r.y, r.z, r.w = q
        self.tf.sendTransform(t)
        od = self._hdr(Odometry(), 'odom', now)
        od.child_frame_id = 'base_link'
        od.pose.pose.position.x, od.pose.pose.position.y, od.pose.pose.position.z = x, y, z
        o = od.pose.pose.orientation
        o.x, o.y, o.z, o.w = q
        self.pub['odom'].publish(od)

        # Lidar: urutan Webots dibalik agar sudut naik berlawanan jarum jam (konvensi ROS)
        step = c.fov / c.n_rays
        sc = self._hdr(LaserScan(), 'lidar', now)
        sc.angle_min = -c.fov / 2.0 + step
        sc.angle_increment = step
        sc.angle_max = sc.angle_min + step * (c.n_rays - 1)
        sc.range_min = c.lidar.getMinRange()
        sc.range_max = c.max_range
        sc.ranges = [float(v) for v in reversed(c.lidar.getRangeImage())]
        self.pub['scan'].publish(sc)

        # Sonar
        for key, dev, frame in (('sl', c.sonar_l, 'sonar_left'), ('sr', c.sonar_r, 'sonar_right')):
            rg = self._hdr(Range(), frame, now)
            rg.radiation_type = Range.ULTRASOUND
            rg.field_of_view = 1.04
            rg.min_range, rg.max_range = 0.25, 2.55
            rg.range = float(dev.getValue())
            self.pub[key].publish(rg)

        # IMU
        im = self._hdr(Imu(), 'base_link', now)
        im.orientation.x, im.orientation.y, im.orientation.z, im.orientation.w = q
        gx, gy, gz = c.gyro.getValues()
        ax, ay, az = c.acc.getValues()
        ay, az = -ay, -az     # accelerometer NAO terpasang terbalik (rotasi 180 deg sumbu x)
        im.angular_velocity.x, im.angular_velocity.y, im.angular_velocity.z = gx, gy, gz
        im.linear_acceleration.x, im.linear_acceleration.y, im.linear_acceleration.z = ax, ay, az
        self.pub['imu'].publish(im)

        # FSR kaki (gaya 3D dalam newton)
        forces = []
        for key, dev, frame in (('fl', c.fsr_l, 'l_sole'), ('fr', c.fsr_r, 'r_sole')):
            v = dev.getValues()       # pointer ctypes (bukan list): ambil 3 elemen saja
            fx, fy, fz = float(v[0]), float(v[1]), float(v[2])
            w = self._hdr(WrenchStamped(), frame, now)
            w.wrench.force.x, w.wrench.force.y, w.wrench.force.z = fx, fy, fz
            self.pub[key].publish(w)
            forces.append(fz)

        # Sendi
        js = self._hdr(JointState(), '', now)
        pos = c.gait.joint_positions()
        js.name = list(pos)
        js.position = [float(v) for v in pos.values()]
        self.pub['js'].publish(js)

        # Kamera
        if self.camera is not None and self.k % (PUBLISH_EVERY * CAMERA_EVERY) == 0:
            raw = self.camera.getImage()
            if raw:
                img = self._hdr(Image(), 'camera_top', now)
                img.height, img.width = self.camera.getHeight(), self.camera.getWidth()
                img.encoding, img.step = 'bgra8', 4 * img.width
                img.data = raw
                self.pub['cam'].publish(img)

        self._markers(now, x, y, yaw, roll, pitch, (gx, gy, gz), (ax, ay, az), forces)

    def _markers(self, now, x, y, yaw, roll, pitch, gyro, acc, forces):
        c = self.c
        theta, free = c.decision
        r, g, b = STATE_COLORS.get(c.state, (0.5, 0.5, 0.5))
        ma = MarkerArray()

        def mk(ns, mid, mtype, frame='base_link'):
            m = Marker()
            m.header.stamp, m.header.frame_id = now, frame
            m.ns, m.id, m.type, m.action = ns, mid, mtype, Marker.ADD
            m.pose.orientation.w = 1.0
            m.color.r, m.color.g, m.color.b, m.color.a = r, g, b, 1.0
            return m

        # koridor arah terpilih (di lantai, frame odom supaya datar walau badan bergoyang)
        length = max(0.05, min(free, 2.0))
        hd = yaw + theta
        cor = mk('koridor', 0, Marker.CUBE, 'odom')
        cor.pose.position.x = x + math.cos(hd) * length / 2
        cor.pose.position.y = y + math.sin(hd) * length / 2
        cor.pose.position.z = 0.005
        qz = quat_rpy(0, 0, hd)
        cor.pose.orientation.x, cor.pose.orientation.y, cor.pose.orientation.z, cor.pose.orientation.w = qz
        cor.scale.x, cor.scale.y, cor.scale.z = length, 0.5, 0.01
        cor.color.a = 0.35
        ma.markers.append(cor)

        arrow = mk('arah', 1, Marker.ARROW, 'odom')
        arrow.pose = cor.pose
        arrow.pose.position.z = 0.02
        arrow.scale.x, arrow.scale.y, arrow.scale.z = max(0.1, min(free, 0.8)), 0.04, 0.04
        ma.markers.append(arrow)

        txt = mk('state', 2, Marker.TEXT_VIEW_FACING, 'odom')
        txt.pose.position.x, txt.pose.position.y, txt.pose.position.z = x, y, 0.95
        txt.scale.z = 0.12
        txt.text = f'{c.state}:{c.gait.name or "-"}'
        ma.markers.append(txt)

        # panel nilai sensor: satu baris per marker agar rapi di RViz
        # catatan: spasi pada TEXT marker RViz2 dirender sangat lebar, jadi dipakai '|' dan ':'
        lines = [
            f'IMU|roll:{math.degrees(roll):+.1f}|pitch:{math.degrees(pitch):+.1f}|yaw:{math.degrees(yaw):+.0f}deg',
            f'gyro:{gyro[0]:+.2f},{gyro[1]:+.2f}rad/s|acc_z:{acc[2]:+.1f}m/s2',
            f'sonar|L:{c.sonar_l.getValue():.2f}m|R:{c.sonar_r.getValue():.2f}m',
            f'FSR|L:{forces[0]:.0f}N|R:{forces[1]:.0f}N',
        ]
        for k, text in enumerate(lines):
            m = mk('panel', 10 + k, Marker.TEXT_VIEW_FACING, 'odom')
            m.pose.position.x, m.pose.position.y = x, y
            m.pose.position.z = 1.55 - 0.11 * k
            m.scale.z = 0.085
            m.color.r, m.color.g, m.color.b = 1.0, 1.0, 1.0
            m.text = text
            ma.markers.append(m)

        # sel yang sudah dikunjungi (memori eksplorasi)
        cells = mk('kunjungan', 4, Marker.CUBE_LIST, 'odom')
        cells.scale.x = cells.scale.y = 0.23
        cells.scale.z = 0.002
        cells.color.r, cells.color.g, cells.color.b, cells.color.a = 1.0, 0.8, 0.2, 0.35
        from geometry_msgs.msg import Point
        size = 0.25
        for (cx, cy) in c.visits:
            p = Point()
            p.x, p.y, p.z = (cx + 0.5) * size, (cy + 0.5) * size, 0.001
            cells.points.append(p)
        ma.markers.append(cells)
        self.pub['dec'].publish(ma)

    def shutdown(self):
        self.node.destroy_node()
        rclpy.try_shutdown()
