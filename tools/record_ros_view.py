"""Merekam /scan + /odom dari bridge ROS 2 lalu menggambar tampilan ala RViz2 (top-down).

Jalankan saat simulasi berjalan dengan ROS 2 di-source:
    python3 tools/record_ros_view.py [durasi_detik]
Hasil: docs/images/ros_scan_view.png
"""
import math
import os
import sys
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
LIDAR_Z = 0.065

rclpy.init()
node = Node('rekam_view')
odom = {}
trail, path, last = [], [], {}


def on_odom(m):
    q = m.pose.pose.orientation
    odom['p'] = (m.pose.pose.position.x, m.pose.pose.position.y, 2 * math.atan2(q.z, q.w))
    path.append(odom['p'][:2])


def on_scan(m):
    if 'p' not in odom:
        return
    x, y, yaw = odom['p']
    pts = []
    for i, r in enumerate(m.ranges):
        if math.isfinite(r):
            a = yaw + m.angle_min + i * m.angle_increment
            pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    trail.append(pts[::2])
    last['pts'], last['pose'] = pts, (x, y, yaw)


node.create_subscription(Odometry, 'odom', on_odom, 10)
node.create_subscription(LaserScan, 'scan', on_scan, 10)
t0 = time.time()
while time.time() - t0 < DUR:
    rclpy.spin_once(node, timeout_sec=0.05)

fig, ax = plt.subplots(figsize=(8, 8), facecolor='#1e222a')
ax.set_facecolor('#1e222a')
for k in range(-6, 7):
    ax.axhline(k * 0.5, color='#a0a0a4', alpha=0.15, lw=0.8)
    ax.axvline(k * 0.5, color='#a0a0a4', alpha=0.15, lw=0.8)
tx = [p[0] for s in trail[::3] for p in s]
ty = [p[1] for s in trail[::3] for p in s]
ax.scatter(tx, ty, s=1.2, color='#78aaff', alpha=0.35, label=f'/scan, jejak {DUR:.0f} s (Decay Time)')
ax.plot([p[0] for p in path], [p[1] for p in path], color='#ffc83c', lw=1.6, label='/odom (lintasan)')
if last:
    ax.scatter([p[0] for p in last['pts']], [p[1] for p in last['pts']], s=9, color='#ff3c3c',
               label='/scan sekarang')
    x, y, yaw = last['pose']
    ax.arrow(x, y, 0.15 * math.cos(yaw), 0.15 * math.sin(yaw), width=0.02, color='white')
ax.set_aspect('equal')
if tx:
    cx, cy = (min(tx) + max(tx)) / 2, (min(ty) + max(ty)) / 2
    half = max(max(tx) - min(tx), max(ty) - min(ty)) / 2 + 0.15
    ax.set_xlim(cx - half, cx + half)
    ax.set_ylim(cy - half, cy + half)
ax.tick_params(colors='#c8ccd4')
for sp in ax.spines.values():
    sp.set_color('#555')
ax.set_xlabel('x frame odom (m)', color='#c8ccd4')
ax.set_ylabel('y frame odom (m)', color='#c8ccd4')
ax.set_title('Data ROS 2 dari robot (fixed frame: odom)', color='white')
leg = ax.legend(loc='upper left', fontsize=8.5, facecolor='#2a2f38', edgecolor='#555')
for t in leg.get_texts():
    t.set_color('white')
fig.tight_layout()
out = os.path.join(ROOT, 'docs', 'images', 'ros_scan_view.png')
fig.savefig(out, dpi=150, facecolor=fig.get_facecolor())
print('OK', out, len(trail), 'scan')
