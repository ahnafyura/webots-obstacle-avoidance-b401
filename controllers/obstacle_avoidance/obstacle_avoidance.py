"""
Controller : obstacle_avoidance
Tugas      : Pelatihan Lab B401 - Robot Obstacle Avoidance (Webots, Python)

Robot      : differential drive kustom (body Box, 2 roda HingeJoint, 1 roda kastor
             BallJoint) - struktur sama seperti modul Line Tracer.
Sensor     : 1x Lidar 360 derajat (sensor utama)
             3x DistanceSensor tipe sonar / ultrasonik di depan (lapisan safety)
             2x PositionSensor (encoder roda) + 1x InertialUnit (IMU) untuk odometri

Algoritma  : "Corridor Gap Selection" + state machine
  1. Setiap step, hasil scan Lidar diubah ke koordinat robot (x maju, y kiri).
  2. Untuk sejumlah kandidat arah (heading) theta, dihitung JARAK BEBAS di sepanjang
     koridor selebar robot (+ margin) ke arah theta. Titik lidar yang masuk ke
     dalam koridor dianggap memblokir jalan.
  3. Dipilih arah dengan skor terbaik:
        skor = min(jarak_bebas, LOOKAHEAD)
               - K_BIAS  * |theta - bias_jelajah|
               - K_SMOOTH* |theta - theta_sebelumnya|
     sehingga robot memilih jalur yang lapang, tetap ingin "menjelajah", dan
     tidak zig-zag. bias_jelajah = arah global acak (diganti tiap 5-10 s) yang
     dikonversi ke frame robot memakai odometri encoder.
  4. Kecepatan linear diskalakan dengan jarak bebas di depan (melambat saat dekat
     obstacle), kecepatan sudut proporsional terhadap theta (kontrol P).
  5. State machine:
        JELAJAH : navigasi normal (langkah 2-4)
        MUNDUR  : ada obstacle terlalu dekat di depan -> mundur sambil memutar
        PUTAR   : berputar di tempat menuju arah paling lapang
     Ditambah watchdog "macet": jika scan lidar hampir tidak berubah padahal robot
     diperintah bergerak, robot dianggap tersangkut lalu masuk MUNDUR.
"""

import math
import os
import random

from controller import Robot

# ---------------------------------------------------------------------------
# Parameter fisik robot (harus sesuai dengan world file)
# ---------------------------------------------------------------------------
WHEEL_RADIUS = 0.03        # m
WHEEL_BASE = 0.14          # m, jarak antar roda kiri-kanan
MAX_WHEEL_SPEED = 14.0     # rad/s (motor maxVelocity = 15)

# ---------------------------------------------------------------------------
# Parameter navigasi
# ---------------------------------------------------------------------------
V_MAX = 0.28               # m/s kecepatan maju maksimum
W_MAX = 3.0                # rad/s kecepatan putar maksimum
K_W = 2.8                  # gain proporsional untuk belok

ROBOT_HALF_WIDTH = 0.08    # m (setengah lebar robot termasuk roda)
SIDE_MARGIN = 0.05         # m, margin aman di kiri/kanan koridor
LOOKAHEAD = 1.0            # m, jarak pandang maksimum yang dihitung
D_STOP = 0.17              # m (dari pusat robot) -> v = 0
D_SLOW = 0.60              # m, mulai melambat
D_EMERGENCY = 0.13         # m, jarak titik terdekat di depan -> MUNDUR
D_ROTATE_SAFE = 0.115      # m, minimal clearance agar aman berputar di tempat

K_BIAS = 0.15              # bobot preferensi arah jelajah (per radian)
K_SMOOTH = 0.08            # bobot penalti perubahan arah (per radian)
CANDIDATES = [math.radians(a) for a in range(-150, 151, 5)]

WANDER_MIN = 5.0           # s, interval minimum ganti arah jelajah
WANDER_MAX = 10.0          # s, interval maksimum ganti arah jelajah

STUCK_WINDOW = 2.0         # s
STUCK_SCAN_DIFF = 0.004    # m, rata-rata perubahan scan dianggap "diam"

LOG_PERIOD = 1.0           # s

# Urutan data lidar (FOV 360): indeks 0 = belakang (+FOV/2 = +180 deg), lalu searah
# jarum jam: 90 = kiri, 180 = depan, 270 = kanan. Diverifikasi dengan uji di world.
LIDAR_FIRST_ANGLE_SIGN = 1.0


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


class ObstacleAvoider:
    def __init__(self):
        self.robot = Robot()
        self.dt_ms = int(self.robot.getBasicTimeStep())
        self.dt = self.dt_ms / 1000.0

        # --- Aktuator ---
        self.motor_l = self.robot.getDevice('motor_kiri')
        self.motor_r = self.robot.getDevice('motor_kanan')
        for m in (self.motor_l, self.motor_r):
            m.setPosition(float('inf'))
            m.setVelocity(0.0)

        # --- Encoder ---
        self.enc_l = self.robot.getDevice('encoder_kiri')
        self.enc_r = self.robot.getDevice('encoder_kanan')
        self.enc_l.enable(self.dt_ms)
        self.enc_r.enable(self.dt_ms)

        # --- Lidar ---
        self.lidar = self.robot.getDevice('lidar')
        self.lidar.enable(self.dt_ms)
        # point cloud diperlukan agar 'Show Lidar Point Cloud' di Webots tampil
        self.lidar.enablePointCloud()
        self.n_rays = self.lidar.getHorizontalResolution()
        self.fov = self.lidar.getFov()
        self.max_range = self.lidar.getMaxRange()
        # sudut tiap sinar dalam frame robot (0 = depan, + = kiri)
        step = self.fov / self.n_rays
        self.ray_angles = [LIDAR_FIRST_ANGLE_SIGN * (self.fov / 2.0 - i * step)
                           for i in range(self.n_rays)]
        self.ray_cos = [math.cos(a) for a in self.ray_angles]
        self.ray_sin = [math.sin(a) for a in self.ray_angles]

        # --- IMU: heading lebih akurat dari encoder (tidak terpengaruh slip roda) ---
        self.imu = self.robot.getDevice('imu')
        self.imu.enable(self.dt_ms)
        self.imu_yaw0 = None

        # --- Ultrasonik (safety layer) ---
        self.us = {}
        for name in ('us_kiri', 'us_depan', 'us_kanan'):
            s = self.robot.getDevice(name)
            s.enable(self.dt_ms)
            self.us[name] = s

        # --- State ---
        self.state = 'JELAJAH'
        self.state_timer = 0.0
        self.turn_dir = 1.0
        self.prev_theta = 0.0
        self.bias = 0.0
        self.wander_heading = 0.0        # arah jelajah global (frame odometri)
        self.wander_timer = 0.0
        self.odom_yaw = 0.0              # heading hasil odometri encoder
        self.odom_x = 0.0                # posisi hasil odometri (frame odom)
        self.odom_y = 0.0
        self.chosen = (0.0, 0.0)         # (theta, jarak_bebas) terakhir, untuk RViz
        self.prev_enc = None
        self.log_timer = 0.0
        self.scan_history = []           # (waktu, scan) untuk deteksi macet
        self.cmd_v = 0.0
        self.time = 0.0
        self.stats = {'mundur': 0, 'macet': 0}
        random.seed(int(os.environ.get('OA_SEED', '401')))

        # --- ROS 2 bridge (opsional, untuk RViz2) ---
        self.ros = None
        if os.environ.get('OA_ROS', '1') != '0':
            try:
                from ros_bridge import RosBridge
                self.ros = RosBridge(0.065, self.n_rays, self.fov,
                                     self.lidar.getMinRange(), self.max_range)
            except ImportError:
                pass                     # ROS 2 tidak di-source: jalan tanpa bridge

    # ------------------------------------------------------------------
    # Pengolahan sensor
    # ------------------------------------------------------------------
    def read_scan(self):
        raw = self.lidar.getRangeImage()
        scan = []
        for r in raw:
            if r != r or r == float('inf') or r <= 0.0 or r > self.max_range:
                r = self.max_range
            scan.append(r)
        return scan

    def corridor_free(self, scan, theta, half_width):
        """Jarak bebas sepanjang koridor selebar 2*half_width ke arah theta."""
        ct, st = math.cos(theta), math.sin(theta)
        free = LOOKAHEAD
        for i, r in enumerate(scan):
            if r >= LOOKAHEAD + half_width:
                continue
            x = r * self.ray_cos[i]
            y = r * self.ray_sin[i]
            longi = x * ct + y * st          # komponen searah theta
            if longi <= 0.0:
                continue
            lat = -x * st + y * ct           # komponen menyamping
            if abs(lat) < half_width and longi < free:
                free = longi
        return free

    def sector_min(self, scan, a_min, a_max):
        m = self.max_range
        for i, r in enumerate(scan):
            a = self.ray_angles[i]
            if a_min <= a <= a_max and r < m:
                m = r
        return m

    def is_stuck(self, scan):
        self.scan_history.append((self.time, scan))
        while self.scan_history and self.time - self.scan_history[0][0] > STUCK_WINDOW:
            self.scan_history.pop(0)
        if self.time < STUCK_WINDOW + 0.5 or abs(self.cmd_v) < 0.05:
            return False
        old = self.scan_history[0][1]
        diff = sum(abs(a - b) for a, b in zip(scan, old)) / len(scan)
        return diff < STUCK_SCAN_DIFF

    # ------------------------------------------------------------------
    # Penggerak
    # ------------------------------------------------------------------
    def drive(self, v, w):
        wl = (v - w * WHEEL_BASE / 2.0) / WHEEL_RADIUS
        wr = (v + w * WHEEL_BASE / 2.0) / WHEEL_RADIUS
        scale = max(1.0, abs(wl) / MAX_WHEEL_SPEED, abs(wr) / MAX_WHEEL_SPEED)
        self.motor_l.setVelocity(wl / scale)
        self.motor_r.setVelocity(wr / scale)
        self.cmd_v = v

    def set_state(self, s):
        if s != self.state:
            self.state = s
            self.state_timer = 0.0

    # ------------------------------------------------------------------
    # Loop utama
    # ------------------------------------------------------------------
    def step(self):
        scan = self.read_scan()
        us_min = min(s.getValue() for s in self.us.values())

        hw = ROBOT_HALF_WIDTH + SIDE_MARGIN
        front_free = self.corridor_free(scan, 0.0, ROBOT_HALF_WIDTH + 0.02)
        front_min = self.sector_min(scan, -math.radians(60), math.radians(60))
        rear_min = self.sector_min(scan, math.radians(120), math.pi)
        rear_min = min(rear_min, self.sector_min(scan, -math.pi, -math.radians(120)))
        all_min = min(scan)
        left_space = sum(scan[i] for i, a in enumerate(self.ray_angles) if 0.2 < a < 1.8)
        right_space = sum(scan[i] for i, a in enumerate(self.ray_angles) if -1.8 < a < -0.2)

        # odometri heading dari encoder roda (dead reckoning)
        enc = (self.enc_l.getValue(), self.enc_r.getValue())
        if self.prev_enc is not None:
            dl = (enc[0] - self.prev_enc[0]) * WHEEL_RADIUS
            dr = (enc[1] - self.prev_enc[1]) * WHEEL_RADIUS
            ds = (dr + dl) / 2.0
            imu_yaw = self.imu.getRollPitchYaw()[2]
            if imu_yaw == imu_yaw:                       # bukan NaN
                if self.imu_yaw0 is None:
                    self.imu_yaw0 = imu_yaw
                new_yaw = wrap(imu_yaw - self.imu_yaw0)  # heading dari IMU
            else:
                new_yaw = wrap(self.odom_yaw + (dr - dl) / WHEEL_BASE)
            mid = self.odom_yaw + wrap(new_yaw - self.odom_yaw) / 2.0
            self.odom_x += ds * math.cos(mid)
            self.odom_y += ds * math.sin(mid)
            self.odom_yaw = new_yaw
        self.prev_enc = enc

        # arah jelajah: robot memilih arah global acak setiap beberapa detik,
        # sehingga bergerak lurus-lurus ke berbagai arah dan menjelajahi arena
        # (tidak berputar-putar di satu lintasan).
        self.wander_timer -= self.dt
        if self.wander_timer <= 0.0:
            self.wander_timer = random.uniform(WANDER_MIN, WANDER_MAX)
            self.wander_heading = random.uniform(-math.pi, math.pi)
        self.bias = clamp(wrap(self.wander_heading - self.odom_yaw),
                          CANDIDATES[0], CANDIDATES[-1])

        emergency = front_min < D_EMERGENCY or us_min < D_EMERGENCY - 0.08
        stuck = self.is_stuck(scan)
        self.state_timer += self.dt

        v = w = 0.0
        if self.state == 'JELAJAH':
            if emergency or stuck:
                self.stats['mundur'] += 1
                if stuck:
                    self.stats['macet'] += 1
                self.turn_dir = 1.0 if left_space > right_space else -1.0
                self.set_state('MUNDUR')
            else:
                best, best_score, best_free = 0.0, -1e9, 0.0
                for th in CANDIDATES:
                    free = self.corridor_free(scan, th, hw)
                    score = (min(free, LOOKAHEAD)
                             - K_BIAS * abs(th - self.bias)
                             - K_SMOOTH * abs(th - self.prev_theta))
                    if score > best_score:
                        best, best_score, best_free = th, score, free
                if best_free < D_STOP + 0.05:
                    # tidak ada jalan yang cukup lapang -> putar di tempat
                    self.turn_dir = 1.0 if left_space > right_space else -1.0
                    self.set_state('PUTAR')
                else:
                    self.prev_theta = best
                    self.chosen = (best, best_free)
                    w = clamp(K_W * best, -W_MAX, W_MAX)
                    speed_factor = clamp((front_free - D_STOP) / (D_SLOW - D_STOP), 0.0, 1.0)
                    heading_factor = max(0.0, math.cos(best)) ** 2
                    v = V_MAX * speed_factor * heading_factor
                    if v < 0.03 and front_free > D_STOP + 0.03:
                        v = 0.03
                    if front_free <= D_STOP:
                        v = 0.0

        elif self.state == 'MUNDUR':
            # mundur pelan sambil memutar menjauhi obstacle
            if rear_min > 0.16:
                v = -0.10
            w = self.turn_dir * 1.5
            if self.state_timer > 0.6 or (rear_min <= 0.16 and self.state_timer > 0.1):
                self.set_state('PUTAR')

        elif self.state == 'PUTAR':
            if all_min < D_ROTATE_SAFE:
                # terlalu sempit untuk berputar: geser menjauh dari titik terdekat
                i_min = scan.index(all_min)
                v = -0.06 if abs(self.ray_angles[i_min]) < math.pi / 2 else 0.06
            w = self.turn_dir * 2.2
            path = self.corridor_free(scan, 0.0, hw)
            if (path > 0.45 and self.state_timer > 0.3) or self.state_timer > 4.0:
                self.prev_theta = 0.0
                self.scan_history.clear()
                self.set_state('JELAJAH')

        self.drive(v, w)

        if self.ros is not None and self.state != 'JELAJAH':
            self.chosen = (0.0, self.corridor_free(scan, 0.0, hw))
        if self.ros is not None:
            self.ros.publish(self.lidar.getRangeImage(), self.odom_x, self.odom_y, self.odom_yaw,
                             v, w, self.state, self.chosen[0], self.chosen[1], hw)

        # telemetri ke console Webots
        self.log_timer += self.dt
        if self.log_timer >= LOG_PERIOD:
            self.log_timer = 0.0
            print(f"[t={self.time:6.1f}s] state={self.state:7s} "
                  f"depan_bebas={front_free:4.2f}m min_depan={front_min:4.2f}m "
                  f"us_min={us_min:4.2f}m v={v:5.2f}m/s w={w:5.2f}rad/s "
                  f"enc=({self.enc_l.getValue():6.1f},{self.enc_r.getValue():6.1f})",
                  flush=True)

    def run(self):
        print(f"Robot B401 Obstacle Avoidance siap. Lidar: {self.n_rays} sinar, "
              f"FOV {math.degrees(self.fov):.0f} derajat, jangkauan {self.max_range} m", flush=True)
        while self.robot.step(self.dt_ms) != -1:
            self.time += self.dt
            self.step()


if __name__ == '__main__':
    ObstacleAvoider().run()
