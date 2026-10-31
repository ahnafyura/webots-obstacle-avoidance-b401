# Robot Obstacle Avoidance — Tugas Pelatihan Lab B401

Robot differential drive kustom di **Webots** yang menjelajahi arena 3 × 3 m berisi **12 obstacle** tanpa menabrak.
Sensor utama **Lidar 360°**, dibantu **3 sensor ultrasonik** sebagai lapisan safety, serta **encoder roda + IMU** untuk odometri. Data Lidar bisa dilihat di **RViz2** (ROS 2).

📄 **Laporan lengkap (PDF):** [`docs/Laporan_Obstacle_Avoidance_B401.pdf`](docs/Laporan_Obstacle_Avoidance_B401.pdf)  
🖥️ **Slide presentasi (PDF):** [`slides/Presentasi_Obstacle_Avoidance_B401.pdf`](slides/Presentasi_Obstacle_Avoidance_B401.pdf) (sumber: `slides/slides.html`, render: `python3 slides/buat_slide.py`)

![Arena](docs/images/overview.jpg)

## Hasil Uji

Uji otomatis: 8 posisi awal × 300 detik simulasi. Tabrakan dideteksi dari *contact points* physics engine oleh Supervisor evaluator.

| Total waktu | Total jarak | **Tabrakan** | Clearance min* | Coverage rata-rata (5 menit) |
|---|---|---|---|---|
| 40 menit | 517 m | **0** | 2.3 cm | 52.7 % |

\*Diukur terhadap lingkaran pembungkus robot (r = 10 cm), jadi jarak body robot ke obstacle sebenarnya lebih besar.

<p align="center"><img src="docs/images/trajectory_all.png" width="48%"> <img src="docs/images/clearance.png" width="48%"></p>

## Ketentuan Tugas

| Ketentuan | Implementasi |
|---|---|
| Robot obstacle avoidance | Navigasi otonom *Corridor Gap Selection* + state machine |
| Bentuk robot bebas (boleh sama dengan modul) | Robot kustom dengan struktur seperti modul: body Box, 2× HingeJoint + motor, kastor BallJoint |
| Obstacle di arena, tidak hanya pinggiran | 12 obstacle: kotak, kotak miring, tabung, dinding, siku-L |
| Sensor bebas | Lidar 360° + 3 ultrasonik (sonar) + 2 encoder + IMU |

## Algoritma (singkat)

1. Scan Lidar (360 sinar) diubah ke titik (x, y) dalam frame robot.
2. Untuk 61 kandidat arah (−150°…150°), dihitung **jarak bebas koridor** selebar robot + margin.
3. Skor = `min(bebas, 1 m) − 0.15·|θ − θ_jelajah| − 0.08·|θ − θ_sebelumnya|`. Arah terbaik dipilih,
   lalu `ω = 2.8·θ` dan `v` diskalakan dengan jarak bebas di depan.
4. State machine: **JELAJAH → MUNDUR** (obstacle < 13 cm, sonar < 5 cm, atau macet) **→ PUTAR** (rotasi sampai koridor depan > 45 cm) **→ JELAJAH**.
5. θ_jelajah adalah arah global acak yang diganti tiap 5–10 s dan dikonversi ke frame robot memakai odometri (encoder + IMU), supaya robot menjelajah dan tidak berputar di satu lintasan.

## Cara Menjalankan

1. Instal [Webots R2025a](https://cyberbotics.com) (atau versi yang lebih baru) dan Python 3.
2. `git clone https://github.com/ahnafyura/webots-obstacle-avoidance-b401.git`
3. Di Webots: **File → Open World…** → `worlds/obstacle_avoidance.wbt` → **Play** ▶.
4. Opsional: **View → Optional Rendering → Show Lidar Ray Paths** untuk menampilkan sinar Lidar.

Console menampilkan telemetri robot setiap detik dan ringkasan evaluator (tabrakan, clearance, coverage) setiap 10 detik.

### Lihat data Lidar di RViz2 (ROS 2)

```bash
tools/rviz.sh        # butuh ROS 2 Jazzy di /opt/ros/jazzy; menjalankan Webots + RViz2
```

Controller otomatis mempublish data berikut jika Webots dijalankan dengan environment ROS 2 (tanpa ROS 2, controller tetap jalan normal):

| Topic | Tipe | Isi |
|---|---|---|
| `/scan` | `sensor_msgs/LaserScan` | scan Lidar 360° |
| `/odom` | `nav_msgs/Odometry` | odometri encoder + IMU |
| `/oa/decision` | `visualization_msgs/MarkerArray` | koridor yang dipilih + state |
| `/tf` | tf2 | `odom → base_link → lidar` |

![Data ROS 2](docs/images/ros_scan_view.png)

Di Webots sendiri, point cloud Lidar bisa ditampilkan lewat **View → Optional Rendering → Show Lidar Point Cloud**.

### Uji otomatis (headless, Linux)

```bash
tools/run_test.sh 180            # 1 run, 180 s -> logs/summary.json
tools/stress_test.sh 300         # 8 run dari posisi awal berbeda
python3 tools/plot_results.py    # grafik -> docs/images/
python3 tools/make_report.py     # laporan PDF -> docs/
```

Variabel lingkungan: `WEBOTS` (path executable), `EVAL_START="x,y,yaw"`, `OA_SEED`, `EVAL_SNAPSHOTS="1,30"`, `EVAL_VIEW=top|follow|oblique`.

## Struktur

```
worlds/obstacle_avoidance.wbt        arena + obstacle + robot + evaluator
controllers/obstacle_avoidance/      controller robot (Python)
controllers/evaluator/               supervisor penguji (tabrakan, clearance, coverage)
tools/                               skrip uji, grafik, generator PDF
docs/                                laporan PDF, gambar, hasil uji
```

Catatan: urutan sinar Lidar sudah diverifikasi lewat uji di world. Indeks 0 mengarah ke belakang robot, lalu searah jarum jam (90 = kiri, 180 = depan, 270 = kanan).
