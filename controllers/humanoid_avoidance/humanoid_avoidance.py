"""
Controller : humanoid_avoidance
Tugas      : Pelatihan Lab B401 - Robot Obstacle Avoidance (Webots, Python)

Robot      : humanoid NAO (25 DOF). Setiap sendi dikendalikan langsung oleh gait.py.
Sensor     : Lidar 360 derajat di atas kepala (sensor utama)
             2 sonar dada (Sonar/Left, Sonar/Right) sebagai lapisan safety
             InertialUnit (orientasi), GPS (posisi untuk memori eksplorasi)
             Gyro, Accelerometer, sensor gaya kaki (FSR), kamera, sensor posisi sendi
             (semua dikirim ke RViz2 lewat ros_bridge.py)

Algoritma  : keputusan diambil di batas setiap gerakan (setiap siklus jalan 2.04 s).
  1. Scan Lidar diubah ke titik (x, y) frame robot. Untuk 36 kandidat arah theta
     dihitung JARAK BEBAS koridor selebar badan humanoid + margin (2 x 0.22 m).
  2. Skor tiap arah:
        skor(theta) = min(bebas, 2 m)/2 m + W_BARU * kebaruan(theta) - 0.35 * |theta|/pi
     kebaruan(theta) = rata-rata 1/(1 + kunjungan) sel grid 0.25 m yang dilewati
     garis arah theta (sampai jarak bebas). Robot mengutamakan area yang belum
     dikunjungi -> coverage naik (dibandingkan mode acak, lihat laporan).
  3. State machine:
        SIAP   : berdiri, memilih gerakan berikutnya
        JALAN  : siklus jalan lurus / belok kiri / belok kanan, diperpanjang selama
                 koridor depan bebas >= 0.85 m dan arah terbaik |theta| <= 40 derajat
        BERHENTI, PUTAR (40/60 derajat di tempat), MUNDUR, BANGUN (jika jatuh)
"""

import math
import os
import random

from controller import Robot

from gait import Gait

# ---------------------------------------------------------------------------
# Parameter
# ---------------------------------------------------------------------------
HALF_W = 0.25              # m, setengah lebar koridor (bahu+lengan NAO ~0.16 m + margin)
LOOKAHEAD = 2.0            # m, jarak bebas maksimum yang dihargai dalam skor
FREE_CAP = 3.5             # m, batas perhitungan jarak bebas koridor
CONTINUE_FREE = 0.85       # m, koridor minimum (searah langkah) untuk satu siklus jalan lagi
STEER_FRONT = 0.70         # m, koridor lurus minimum saat siklus berbelok menjauhi obstacle
START_FREE = 0.85          # m, koridor minimum untuk mulai jalan ke suatu arah
BACKUP_DIST = 0.30         # m, obstacle sedekat ini di depan -> mundur
ROTATE_SAFE = 0.33         # m, clearance minimal untuk berputar di tempat (lengan + ayunan badan)
STEER_DEADBAND = math.radians(7)
WALK_MAX_ANGLE = math.radians(75)   # belok sambil jalan sampai target sejauh ini
K_TURN = float(os.environ.get('OA_K_TURN', '0.35'))       # penalti belok (per pi radian)
W_NOVELTY = float(os.environ.get('OA_W_NOV', '0.6'))      # bobot kebaruan (mode 'kebaruan')
NOVELTY_RANGE = float(os.environ.get('OA_NOV_RANGE', '2.5'))  # m, jarak sampel kebaruan
K_KEEP = float(os.environ.get('OA_K_KEEP', '0.25'))       # penalti ganti arah tujuan (frame dunia)
CELL = 0.25                # m, ukuran sel memori kunjungan
CANDIDATES = [math.radians(a) for a in range(-180, 180, 10)]
SONAR_STOP = 0.30          # m, sonar membaca lebih dekat -> berhenti/mundur
SONAR_START = float(os.environ.get("OA_SONAR_START", "0.0"))  # m, sonar minimal untuk mulai jalan (0 = tidak dipakai)
START_FRONT = 0.60         # m, koridor depan minimal untuk mulai jalan
START_FRONT_SIDE_CLEAR = 0.45  # m, boleh lebih pendek jika samping lega
SIDE_CLEAR = 0.35          # m, samping dianggap lega
                           #    (mulai 0.10 m + berhenti 0.18 m + badan + margin)
REGION_WINDOW = 60.0       # s, watchdog wilayah: jendela waktu
REGION_RADIUS = 0.5        # m, robot dianggap terjebak jika selalu dalam radius ini
ESCAPE_TIME = 25.0         # s, lama mode lolos
ESCAPE_FREE = 1.2          # m, koridor minimum yang dicari saat mode lolos
LOG_PERIOD = 1.0

# Urutan sinar Lidar 360 di Webots: indeks 0 = belakang (+180 deg), lalu searah jarum
# jam (90 = kiri, 180 = depan, 270 = kanan). Sudut sinar ke-i: pi - i*(2*pi/N).


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


class Humanoid:
    def __init__(self):
        self.robot = Robot()
        self.ts = int(self.robot.getBasicTimeStep())
        self.dt = self.ts / 1000.0
        here = os.path.dirname(os.path.abspath(__file__))
        self.gait = Gait(self.robot, self.dt, os.path.join(here, 'motions'))

        dev = self.robot.getDevice
        self.lidar = dev('lidar')
        self.lidar.enable(self.ts)
        self.lidar.enablePointCloud()          # untuk 'Show Lidar Point Cloud' di Webots
        self.n_rays = self.lidar.getHorizontalResolution()
        self.fov = self.lidar.getFov()
        self.max_range = self.lidar.getMaxRange()
        step = self.fov / self.n_rays
        self.ray_angles = [self.fov / 2.0 - i * step for i in range(self.n_rays)]
        self.ray_cos = [math.cos(a) for a in self.ray_angles]
        self.ray_sin = [math.sin(a) for a in self.ray_angles]

        self.sonar_l, self.sonar_r = dev('Sonar/Left'), dev('Sonar/Right')
        self.imu = dev('imu_body')
        self.gps = dev('gps')
        self.gyro = dev('gyro')
        self.acc = dev('accelerometer')
        self.fsr_l, self.fsr_r = dev('LFsr'), dev('RFsr')
        for d in (self.sonar_l, self.sonar_r, self.imu, self.gps, self.gyro, self.acc,
                  self.fsr_l, self.fsr_r):
            d.enable(self.ts)

        self.mode = os.environ.get('OA_EXPLORE', 'kebaruan')   # 'kebaruan' atau 'acak'
        random.seed(int(os.environ.get('OA_SEED', '401')))
        self.visits = {}
        self.visit_timer = 0.0
        self.wander = 0.0
        self.wander_timer = 0.0
        self.state = 'SIAP'
        self.walking = False
        self.time = 0.0
        self.log_timer = 0.0
        self.decision = (0.0, 0.0)       # (theta, jarak bebas) terakhir
        self.stats = {'mundur': 0, 'putar': 0, 'jatuh': 0, 'lolos': 0}
        self.progress = []               # (waktu, x, y) untuk watchdog macet
        self.goal_heading = 0.0          # arah tujuan terakhir (frame dunia), untuk persistensi
        self.turn_lock = None            # arah putar dikunci sampai robot mulai jalan
        self.turn_count = 0              # jumlah putar beruntun tanpa berjalan
        self.region = []                 # (waktu, x, y) 60 s terakhir untuk watchdog wilayah
        self.escape_timer = 0.0          # > 0: mode lolos dari area sempit

        self.ros = None
        if os.environ.get('OA_ROS', '1') != '0':
            try:
                from ros_bridge import RosBridge
                self.ros = RosBridge(self)
            except ImportError:
                pass

    # ------------------------------------------------------------------ sensor
    def scan(self):
        out = []
        for r in self.lidar.getRangeImage():
            if r != r or r == float('inf') or r <= 0.0 or r > self.max_range:
                r = self.max_range
            out.append(r)
        return out

    def pose(self):
        x, y, z = self.gps.getValues()
        roll, pitch, yaw = self.imu.getRollPitchYaw()
        return x, y, z, roll, pitch, yaw

    def corridor_free(self, scan, theta, half_width=HALF_W):
        ct, st = math.cos(theta), math.sin(theta)
        free = FREE_CAP
        for i, r in enumerate(scan):
            if r >= FREE_CAP + half_width:
                continue
            x, y = r * self.ray_cos[i], r * self.ray_sin[i]
            longi = x * ct + y * st
            if longi <= 0.0:
                continue
            if abs(-x * st + y * ct) < half_width and longi < free:
                free = longi
        return free

    def sector_min(self, scan, a_min, a_max):
        m = self.max_range
        for i, r in enumerate(scan):
            if a_min <= self.ray_angles[i] <= a_max and r < m:
                m = r
        return m

    # ----------------------------------------------------------- eksplorasi
    def cell(self, x, y):
        return (int(math.floor(x / CELL)), int(math.floor(y / CELL)))

    def novelty(self, x, y, heading, free):
        dist = min(free, NOVELTY_RANGE)
        if dist < 0.5:
            return 0.0
        vals, d = [], 0.5
        while d <= dist:
            c = self.cell(x + d * math.cos(heading), y + d * math.sin(heading))
            vals.append(1.0 / (1.0 + self.visits.get(c, 0)))
            d += CELL
        return sum(vals) / len(vals)

    def choose(self, scan, x, y, yaw, min_free=START_FREE):
        """Pilih arah terbaik. Kembalikan (theta, jarak_bebas, skor)."""
        best = (0.0, 0.0, -1e9)
        for th in CANDIDATES:
            free = self.corridor_free(scan, th)
            if free < min_free:
                continue
            if self.escape_timer > 0.0:
                # mode lolos: cari ruang paling lega, abaikan kebaruan dan penalti belok
                if free < ESCAPE_FREE:
                    continue
                score = free
                if score > best[2]:
                    best = (th, free, score)
                continue
            score = (min(free, LOOKAHEAD) / LOOKAHEAD - K_TURN * abs(th) / math.pi
                     - K_KEEP * abs(wrap(yaw + th - self.goal_heading)) / math.pi)
            if self.mode == 'kebaruan':
                score += W_NOVELTY * self.novelty(x, y, yaw + th, free)
            else:
                score -= 0.3 * abs(wrap(yaw + th - self.wander)) / math.pi
            if score > best[2]:
                best = (th, free, score)
        return best

    # ------------------------------------------------------------ keputusan
    def decide(self, scan):
        x, y, z, roll, pitch, yaw = self.pose()
        front = self.corridor_free(scan, 0.0)
        front_min = self.sector_min(scan, -math.radians(50), math.radians(50))
        rear_min = min(self.sector_min(scan, math.radians(130), math.pi),
                       self.sector_min(scan, -math.pi, -math.radians(130)))
        all_min = min(scan)
        sonar = min(self.sonar_l.getValue(), self.sonar_r.getValue())
        # sudah berputar 360 deg tanpa menemukan jalan: longgarkan syarat koridor
        min_free = START_FREE if self.turn_count < 7 else 0.6
        # sonar NAO berpancaran lebar (~60 deg) sehingga sering menangkap obstacle di samping.
        # Sonar dipakai sebagai konfirmasi: hanya berlaku jika Lidar juga melihat sesuatu dekat.
        sonar_alarm = sonar < SONAR_STOP and front_min < 0.6
        theta, free, score = self.choose(scan, x, y, yaw, min_free)
        if score > -1e9:
            self.goal_heading = wrap(yaw + theta)
        self.decision = (theta, free if score > -1e9 else front)
        g = self.gait

        if self.walking:
            # koridor diperiksa searah belokan yang akan diambil, bukan hanya lurus ke depan
            left_ok = theta > STEER_DEADBAND and front >= STEER_FRONT \
                and self.corridor_free(scan, math.radians(15)) >= CONTINUE_FREE
            right_ok = theta < -STEER_DEADBAND and front >= STEER_FRONT \
                and self.corridor_free(scan, -math.radians(15)) >= CONTINUE_FREE
            if sonar_alarm or score <= -1e9 or abs(theta) > WALK_MAX_ANGLE \
                    or not (left_ok or right_ok or front >= CONTINUE_FREE):
                g.play('jalan_berhenti')
                self.walking, self.state = False, 'BERHENTI'
            elif left_ok:
                g.play('jalan_kiri')
                self.state = 'JALAN_KIRI'
            elif right_ok:
                g.play('jalan_kanan')
                self.state = 'JALAN_KANAN'
            else:
                g.play('jalan_lurus')
                self.state = 'JALAN'
            return

        # berdiri
        if (front_min < BACKUP_DIST or (sonar_alarm and front_min < 0.5)) and rear_min > 0.45:
            g.play('mundur')
            self.state = 'MUNDUR'
            self.stats['mundur'] += 1
            return
        stuck = self.stuck()
        # jarak terdekat di samping (30-120 deg kiri dan kanan): lengan bisa menyenggol
        side_min = min(self.sector_min(scan, math.radians(30), math.radians(120)),
                       self.sector_min(scan, -math.radians(120), -math.radians(30)))
        # histeresis: arah dalam +-30 deg -> langsung jalan, koreksi sambil berjalan
        if not stuck and score > -1e9 and abs(theta) <= math.radians(35) \
                and self.corridor_free(scan, theta) >= min_free \
                and sonar >= SONAR_START and (front >= START_FRONT or (
                    front >= START_FRONT_SIDE_CLEAR and side_min >= SIDE_CLEAR)):
            g.play('jalan_mulai')
            self.walking, self.state = True, 'JALAN'
            self.turn_lock, self.turn_count = None, 0
            return

        # perlu berputar di tempat: pastikan ada ruang untuk lengan dan ayunan badan
        if all_min < ROTATE_SAFE:
            i_min = scan.index(all_min)
            if abs(self.ray_angles[i_min]) < math.pi / 2 and rear_min > 0.45:
                g.play('mundur')                       # obstacle di depan -> mundur
                self.state = 'MUNDUR'
                self.stats['mundur'] += 1
                return
            if abs(self.ray_angles[i_min]) >= math.pi / 2 and front_min > 0.5:
                g.play('maju_kecil')                   # obstacle di belakang -> maju sedikit
                self.state = 'MAJU_KECIL'
                return

        left_min = self.sector_min(scan, 0.15, math.pi - 0.15)
        right_min = self.sector_min(scan, -math.pi + 0.15, -0.15)
        if score > -1e9 and not stuck and abs(theta) <= math.pi / 2:
            # target di depan: arah putar jelas (ke sisi target), kunci dilepas
            side = 'kiri' if theta > 0 else 'kanan'
            big = abs(theta) > math.radians(50)
        elif self.turn_lock is not None:
            # target di belakang / tidak ada jalan: arah putar dikunci agar tidak bolak-balik
            side = self.turn_lock
            big = score <= -1e9 or stuck or abs(theta) > math.radians(50)
            if stuck:
                self.progress.clear()
        elif score <= -1e9 or stuck:
            side, big = ('kiri' if left_min >= right_min else 'kanan'), True
            self.progress.clear()
        else:
            # belokan besar (> 90 deg): putar ke sisi yang lebih lega, bukan sisi terdekat
            if abs(theta) > math.pi / 2:
                side = 'kiri' if left_min >= right_min else 'kanan'
            else:
                side = 'kiri' if theta > 0 else 'kanan'
            big = abs(theta) > math.radians(50)
        if score > -1e9 and abs(theta) > math.radians(140) and self.turn_lock in (None, 'kiri') \
                and all_min >= ROTATE_SAFE:
            g.play('putar_balik')                      # target di belakang: putar balik (~196 deg)
            self.state = 'PUTAR'
            self.stats['putar'] += 1
            self.turn_lock = 'kiri'
            self.turn_count += 3
            return
        if big:
            size = 60
        elif score > -1e9 and not stuck and abs(theta) <= math.radians(15):
            size = 10                                  # koreksi sangat halus (resolusi kandidat 10 deg)
        elif score > -1e9 and not stuck and abs(theta) <= math.radians(30):
            size = 20                                  # koreksi halus, tidak overshoot
        else:
            size = 40
        g.play(f'putar_{side}{size}')
        self.state = 'PUTAR'
        self.stats['putar'] += 1
        self.turn_lock = side
        self.turn_count += 1

    def stuck(self):
        """Macet: perpindahan < 0.15 m dalam 30 s terakhir."""
        if len(self.progress) < 2 or self.progress[-1][0] - self.progress[0][0] < 30.0:
            return False
        (_, x0, y0), (_, x1, y1) = self.progress[0], self.progress[-1]
        return math.hypot(x1 - x0, y1 - y0) < 0.15

    # ----------------------------------------------------------------- loop
    def step(self):
        self.time += self.dt
        x, y, z, roll, pitch, yaw = self.pose()

        # memori kunjungan (setiap 0.5 s) dan arah jelajah mode acak (setiap 20 s)
        self.visit_timer += self.dt
        if self.visit_timer >= 0.5 and x == x:
            self.visit_timer = 0.0
            c = self.cell(x, y)
            self.visits[c] = self.visits.get(c, 0) + 1
            self.progress.append((self.time, x, y))
            self.region.append((self.time, x, y))
            while self.region and self.time - self.region[0][0] > REGION_WINDOW:
                self.region.pop(0)
            if self.escape_timer <= 0.0 and self.region \
                    and self.time - self.region[0][0] >= REGION_WINDOW - 1.0:
                mx = sum(p[1] for p in self.region) / len(self.region)
                my = sum(p[2] for p in self.region) / len(self.region)
                if max(math.hypot(p[1] - mx, p[2] - my) for p in self.region) < REGION_RADIUS:
                    self.escape_timer = ESCAPE_TIME
                    self.region.clear()
                    self.stats['lolos'] += 1
            while self.progress and self.time - self.progress[0][0] > 31.0:
                self.progress.pop(0)
        self.escape_timer -= self.dt
        self.wander_timer -= self.dt
        if self.wander_timer <= 0.0:
            self.wander_timer = 20.0
            self.wander = random.uniform(-math.pi, math.pi)

        fallen = abs(roll) > math.radians(45) or abs(pitch) > math.radians(45)
        if fallen and self.state != 'BANGUN':
            self.stats['jatuh'] += 1
            self.walking = False
            self.gait.play('bangun', 0.3)
            self.state = 'BANGUN'
        elif not self.gait.busy():
            self.decide(self.scan())
        self.gait.step()

        if self.ros is not None:
            self.ros.publish()

        self.log_timer += self.dt
        if self.log_timer >= LOG_PERIOD:
            self.log_timer = 0.0
            th, fr = self.decision
            print(f"[t={self.time:6.1f}s] state={self.state:11s} gerak={self.gait.name or '-':14s} "
                  f"arah={math.degrees(th):+5.0f}deg bebas={fr:4.2f}m "
                  f"sonar=({self.sonar_l.getValue():.2f},{self.sonar_r.getValue():.2f})m "
                  f"pos=({x:+.2f},{y:+.2f}) sel={len(self.visits)}"
                  f"{' LOLOS' if self.escape_timer > 0 else ''}", flush=True)

    def run(self):
        print(f"Humanoid B401 siap. Lidar {self.n_rays} sinar, jangkauan {self.max_range} m. "
              f"Mode eksplorasi: {self.mode}", flush=True)
        self.robot.step(self.ts)
        self.gait.go_ready(1.2)
        while self.robot.step(self.ts) != -1:
            self.step()


if __name__ == '__main__':
    Humanoid().run()
