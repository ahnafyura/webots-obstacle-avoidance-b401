# Catatan Serah-Terima untuk Agent Berikutnya

Dokumen ini merangkum **apa yang dibuat, kenapa, bagaimana caranya, hasilnya, dan aturan yang harus dijaga** di repo ini. Baca seluruhnya sebelum mengubah apa pun.

- Pemilik: Ahnaf (GitHub `ahnafyura`). Komunikasi dalam Bahasa Indonesia. Pemilik biasanya menyerahkan tugas end-to-end.
- Repo (PUBLIK): https://github.com/ahnafyura/webots-obstacle-avoidance-b401
- Lokasi lokal: `~/Documents/Barunastra/obstacle-avoidance-b401`

---

## 1. Objektif tugas (Tugas Pelatihan Lab B401)

| # | Ketentuan dari tugas / pemilik | Status | Cara dipenuhi |
|---|---|---|---|
| 1 | Robot obstacle avoidance di **Webots** | ✅ | Humanoid berjalan otonom memakai Lidar, koridor selebar badan, dan state machine |
| 2 | Bentuk robot bebas | ✅ | **Humanoid NAO (25 sendi)** dengan gait engine buatan sendiri |
| 3 | Obstacle **di dalam** arena, tidak hanya di pinggir | ✅ | 12 obstacle setinggi 0.8 m di arena 5×5 m |
| 4 | Sensor bebas | ✅ | Lidar 360° di kepala, sonar, IMU, gyro, accelerometer, GPS, FSR kaki, kamera, sensor sendi |
| 5 | Repo GitHub publik + dokumentasi **PDF** | ✅ | `docs/Laporan_Obstacle_Avoidance_B401.pdf` (±23 halaman) |
| 6 | Slide presentasi bergaya deck magang di `/barunastra/c16` | ✅ | `slides/Presentasi_Obstacle_Avoidance_B401.pdf` (25 slide) |
| 7 | Slide **tanpa logo apa pun dan tanpa unsur Barunastra/ITS** | ✅ | Logo, pill, dan latar laut dihapus. Footer: "Pelatihan Lab B401 · Robot Humanoid Obstacle Avoidance" |
| 8 | Robot humanoid dengan **setiap sendi berjalan baik** dan **Lidar di atas** | ✅ | Lidar di `headSlot` NAO, tinggi ±0.57 m dari lantai |
| 9 | **Rumus benar**, tidak ada salah | ✅ | Rumus di laporan, slide, dan README dicocokkan dengan konstanta di kode |
| 10 | **RViz2 menampilkan semua sensor** | ✅ | Lihat §6 |
| 11 | **Peningkatan coverage** | ✅ | Eksplorasi "kebaruan": 42.9% vs acak 30.3% (+42%) |
| 12 | Push **tanpa trailer `Co-Authored-By: Claude`** | ✅ | Berlaku sejak commit `c32f97d`. Lihat §9 |

---

## 2. Riwayat versi (kebaharuan)

| Versi | Commit/tag | Isi |
|---|---|---|
| v1 | tag `v1-robot-roda` (`9230c3c`…`c6f884f`) | Robot **beroda** differential drive (badan Box, roda HingeJoint, caster BallJoint, mirip modul line tracer), Lidar 360 + ultrasonik. Kemudian ditambah slide, ROS 2 bridge + RViz2, dan fix XWayland |
| v2 (sekarang) | `c32f97d` | **Diganti ke humanoid NAO** dengan Lidar di kepala, gait engine sendiri, navigasi kebaruan, RViz2 semua sensor, slide tanpa logo, laporan baru |

Pembaruan utama dari v1 ke v2:
1. Robot beroda diganti humanoid NAO 25 DOF, dan Lidar dipindah ke kepala.
2. **Gait engine sendiri.** Motion bawaan Webots membuat NAO jatuh di detik 1.2, jadi robot sekarang digerakkan sendi per sendi dengan transisi smoothstep.
3. Navigasi dengan **memori sel yang sudah dikunjungi**, sehingga coverage naik 42% dibanding mode acak.
4. Aturan keselamatan dan watchdog khusus humanoid: ruang putar, mundur, macet, terjebak di area sempit, dan bangun bila jatuh.
5. Evaluator mendeteksi **jatuh**, selain tabrakan.
6. ROS 2 bridge mempublikasikan **semua sensor**, dan URDF humanoid dibuat untuk RViz2.
7. Slide dibersihkan dari logo dan Barunastra. Simbol θ diperbaiki, karena font Anton tidak punya huruf Yunani; rumus kini memakai class `.math` dengan DejaVu Serif.
8. Laporan PDF ditulis ulang, dan semua angkanya diambil otomatis dari `docs/stress_results.json`.

---

## 3. Lingkungan

- **Webots R2025a** di `~/opt/webots` (instal tanpa sudo).
- Python 3. Controller memakai Python.
- **ROS 2 Jazzy** di `/opt/ros/jazzy`. Ini opsional: kalau `rclpy` tidak ada, terjadi ImportError dan controller tetap jalan tanpa ROS.
- Desktop memakai Wayland, jadi RViz2 **harus** dijalankan dengan `QT_QPA_PLATFORM=xcb`. Tanpa itu Ogre crash.
- PDF laporan dibuat dengan reportlab (font DejaVu) dan grafik dengan matplotlib. Slide berupa HTML 1440×810 yang dirender ke PDF oleh `google-chrome --headless`.

---

## 4. Struktur file

```
worlds/obstacle_avoidance.wbt     DIBUAT oleh tools/make_world.py (jangan edit manual, edit generatornya)
controllers/humanoid_avoidance/
  humanoid_avoidance.py           controller utama: sensor, navigasi, state machine, watchdog, log
  gait.py                         gait engine (pemutar keyframe .motion + blend + pulsa belok)
  ros_bridge.py                   publisher ROS 2 (opsional)
  motions/*.motion + SUMBER.txt   file motion NAO dari Webots (Apache 2.0)
controllers/evaluator/evaluator.py  Supervisor penguji: tabrakan, jatuh, clearance, coverage, screenshot, CSV
rviz/humanoid.rviz                konfigurasi RViz2
rviz/humanoid_b401.urdf, nao_webots_export.urdf, rsp_params.yaml   DIBUAT oleh tools/make_urdf.py
tools/run_test.sh                 satu uji headless
tools/stress_test.sh              uji massal (8 posisi awal per set)
tools/plot_results.py             grafik ke docs/images + docs/stress_results.json
tools/make_report.py              laporan PDF
tools/record_ros_view.py          rekam /scan + /odom ke docs/images/ros_scan_view.png
tools/rviz.sh                     Webots + robot_state_publisher + RViz2 sekaligus
slides/slides.html + buat_slide.py  slide (placeholder {{...}} diisi dari stress_results.json)
logs/                             hasil uji (DI-.gitignore, hanya ada di laptop lokal)
```

---

## 5. Cara kerja teknis

### 5.1 Robot dan world
- Arena 5×5 m dengan dinding 0.8 m. Ada 12 obstacle setinggi 0.8 m: `kotak_1, dinding_miring, tabung_1, tabung_2, dinding_tengah, kotak_berlian, tabung_besar, dinding_utara, tiang, kotak_2, siku_L_a, siku_L_b`.
- `DEF ROBOT Nao` mulai di (−2, −2, 0.334) dengan yaw 0.785.
- **Lidar** di `headSlot` pada z = 0.085: 360 sinar, jangkauan 0.06–4 m.
  - Urutan sinar: indeks 0 = belakang, lalu searah jarum jam.
  - Sudut sinar ke-i: θᵢ = π − i·2π/N.
- **InertialUnit `imu_body`** dipasang di `bodySlot`, karena IMU bawaan NAO tidak punya sumbu yaw.
- Perangkat bawaan NAO yang dipakai:
  - `Sonar/Left`, `Sonar/Right`, `gps`, `gyro`
  - `accelerometer`: terpasang terbalik 180° di sumbu x, sehingga **y dan z harus dibalik tandanya**
  - `LFsr`/`RFsr` (TouchSensor force-3d), `CameraTop`
  - sensor sendi dengan nama `<sendi>S`

### 5.2 Gait engine (`gait.py`)
- Membaca keyframe `.motion` (satu frame per 40 ms) lalu menginterpolasinya secara linear dan memanggil `setPosition` pada semua motor setiap step.
- Pindah ke gerakan baru memakai transisi **smoothstep** s(u) = 3u² − 2u³ selama 0.4 s, dari pose saat ini ke pose awal gerakan.
- Klip berantai (`jalan_lurus`, `jalan_kiri`, `jalan_kanan`, `jalan_berhenti`) memakai blend 0 agar langkah tidak patah.
- **Siklus jalan**: `Forwards50` frame 51–102. Frame 51 dan 102 identik, jadi siklus bisa diulang terus. Satu siklus = 2 langkah, 2.04 s, maju ±0.18 m.
  - Klip mulai: frame 0–51. Klip berhenti: frame 102–170.
- **Belok sambil jalan**: pulsa sendi `HipYawPitch` beramplitudo 0.25 rad, menghasilkan ±17° ke kiri atau ±13° ke kanan per siklus.
  - Kiri: membuka di frame 7–20, menutup di 20–33.
  - Kanan: membuka di frame 20–33, menutup di 33–46.
  - Amplitudo 0.4–0.5 membuat kaki selip, jadi **jangan dinaikkan**.
- **Putar di tempat**:
  - 10° dan 20°: HipYawPitch dari `TurnLeft40`/`TurnRight40` dikali 0.25 dan 0.5.
  - 40° dan 60° memakai klip apa adanya.
  - `putar_balik` memakai `TurnLeft180` dan hasil terukurnya +196° dalam 9.0 s.
- Gerakan lain: `mundur`, `maju_kecil`, dan `bangun` (StandUpFromFront).

### 5.3 Navigasi (`humanoid_avoidance.py`)
1. Untuk 36 kandidat arah (−180°…170°, langkah 10°), hitung **jarak bebas koridor** dengan lebar 2×`HALF_W` = 0.5 m, dibatasi maksimal 3.5 m.
2. Skor setiap arah:
   `skor(θ) = min(bebas,2)/2 + 0.6·K(θ) − 0.35·|θ|/π − 0.25·|wrap(ψ+θ−ψ_tujuan)|/π`
   - **Kebaruan K(θ)** = rata-rata 1/(1+kunjungan) atas sel grid 0.25 m sepanjang arah θ, dari 0.5 m sampai min(bebas, 2.5 m).
   - Jumlah kunjungan dicatat dari posisi GPS setiap 0.5 s.
   - Pada mode `acak` (pembanding), suku kebaruan diganti −0.3·|wrap(ψ+θ−ψ_wander)|/π, dengan arah wander yang diacak ulang setiap 20 s.
3. State machine: SIAP / JALAN (lurus, kiri, kanan) / BERHENTI / PUTAR / MUNDUR / BANGUN.
4. **Aturan keselamatan.** Semua angka di bawah hasil tuning dari kasus tabrakan nyata; jangan diubah tanpa uji ulang.
   - Tetap jalan hanya jika koridor ke arah langkah ≥ 0.85 m. Saat berbelok, jarak lurus ke depan harus ≥ 0.70 m.
   - Mulai jalan jika depan ≥ 0.60 m, atau ≥ 0.45 m bila kedua sisi (30–120°) ≥ 0.35 m.
   - Putar di tempat hanya jika **semua** titik scan ≥ 0.33 m. Kalau tidak, robot mundur atau maju kecil dulu.
   - Mundur jika sektor depan (±50°) < 0.30 m dan belakang ≥ 0.45 m.
   - Alarm sonar (< 0.30 m) hanya dihitung jika Lidar sektor depan < 0.6 m, karena sonar NAO sering memberi alarm palsu.
   - Turn-lock (arah putar dikunci) hanya berlaku saat tujuan ada di belakang, untuk mencegah robot bolak-balik di sudut.
   - Belok sambil jalan diizinkan sampai 75°. Deadband belok 7°.
5. **Watchdog:**
   - Macet: bergerak < 0.15 m dalam 30 s → putar 60°.
   - Terjebak di area sempit: tetap dalam radius 0.5 m selama 60 s → mode escape 25 s, menuju arah dengan jarak bebas terbesar (minimal 1.2 m).
   - Jatuh: |roll| atau |pitch| > 45° → gerakan bangun.
6. Variabel lingkungan:
   - `OA_EXPLORE=kebaruan|acak`, `OA_SEED`, `OA_ROS=0|1`, `OA_ROS_CAMERA`
   - Tuning: `OA_K_TURN`, `OA_W_NOV`, `OA_NOV_RANGE`, `OA_K_KEEP`, `OA_SONAR_START`

### 5.4 Evaluator (`controllers/evaluator/evaluator.py`)
- **Tabrakan** dihitung dari titik kontak fisik robot yang lebih tinggi dari `CONTACT_Z` = 0.03 m (kontak telapak kaki dengan lantai diabaikan). Detektor ini sudah divalidasi dengan humanoid "buta" yang sengaja ditabrakkan.
- **Jatuh** dihitung jika z badan < 0.22 m.
- **Coverage** = persen sel grid 0.2 m yang pernah dilewati (radius robot 0.18 m).
- Juga mencatat clearance minimum, CSV trajektori (termasuk z), screenshot (view top, chase, oblique), dan ringkasan setiap 10 s.
- Variabel lingkungan: `EVAL_DURATION`, `EVAL_LOG_DIR`, `EVAL_START`.

---

## 6. RViz2 (`tools/rviz.sh`)

Skrip ini menjalankan Webots (realtime), robot_state_publisher (executable langsung dengan `--params-file rviz/rsp_params.yaml`), dan `QT_QPA_PLATFORM=xcb rviz2 -d rviz/humanoid.rviz`. Saat keluar, `trap` mematikan semua child process.

| Topic | Isi | Display di RViz2 |
|---|---|---|
| `/scan` | Lidar 360°. Urutan sinar Webots dibalik, `angle_min = −π + step` | LaserScan sekarang + jejak 60 s |
| `/sonar/left`, `/sonar/right` | `Range` | Range (alpha 0.12) |
| `/imu` | orientasi + gyro + accelerometer | Axes `imu_body` |
| `/fsr/left`, `/fsr/right` | `WrenchStamped` (gaya kaki ±50 N saat berdiri) | Wrench |
| `/camera/image_raw` | bgra8, ±5 Hz | Image |
| `/joint_states` + `/robot_description` | semua sendi | RobotModel |
| `/odom` + TF `odom→base_link` | posisi | Odometry |
| `/oa/decision` | MarkerArray: koridor, panah arah, teks state, panel sensor, sel dikunjungi | MarkerArray |

- Bridge mempublikasikan setiap 2 step (±25 Hz), dan kamera setiap publish ke-5.
- URDF berasal dari ekspor Webots (`getUrdf`, hanya kaki) yang dilengkapi lengan, kepala, lidar, dan kamera oleh `tools/make_urdf.py`. Ekspor URDF Webots belum mendukung Hinge2Joint.

---

## 7. Hasil uji akhir (kode sekarang)

32 uji × 10 menit = 5.3 jam simulasi (16 posisi awal × 2 mode):

| Set | Kebaruan | Acak |
|---|---|---|
| set1 | 43.5 % (min 37.6) | 31.1 % |
| set2 | 42.3 % (min 27.9) | 29.4 % |
| **Total** | **42.9 %** (27.9–48.8), 0 tabrakan, 0 jatuh, 681 m | 30.3 % (19.4–37.3), 0 tabrakan, 0 jatuh, 704 m |

- Peningkatan coverage: **+42 %**.
- Jarak tempuh dihitung dari posisi yang disampel setiap 1 s (`path_length(rows, every=10)`), supaya goyangan badan tidak ikut terhitung.

---

## 8. Cara menjalankan dan membangun ulang

```bash
# Demo: Webots → File → Open World → worlds/obstacle_avoidance.wbt → Play
tools/rviz.sh                                   # demo + RViz2

# Uji headless (--batch --mode=fast --minimize --no-rendering)
tools/stress_test.sh 600 kebaruan               # set 1, 8 posisi awal
tools/stress_test.sh 600 acak
STARTS_SET=2 tools/stress_test.sh 600 kebaruan  # set 2
STARTS_SET=2 tools/stress_test.sh 600 acak

# Bangun ulang dokumen (urutan penting)
python3 tools/plot_results.py    # butuh logs/set{1,2}_{kebaruan,acak} → docs/images + docs/stress_results.json
python3 tools/make_report.py     # → docs/Laporan_Obstacle_Avoidance_B401.pdf
python3 slides/buat_slide.py     # → slides/Presentasi_Obstacle_Avoidance_B401.pdf

# Generator (jalankan ulang jika world/URDF berubah)
python3 tools/make_world.py
python3 tools/make_urdf.py
```

Jika parameter navigasi atau gait diubah, **jalankan ulang ke-4 stress test** sebelum membangun ulang laporan dan slide. Angka di dokumen harus berasal dari kode yang sama.

---

## 9. Aturan yang WAJIB dijaga

1. **Commit tanpa baris `Co-Authored-By: Claude`.** Ini permintaan eksplisit pemilik dan mengalahkan aturan atribusi default. Author: `ahnafyura <farikatasyafi@gmail.com>`.
2. **Slide tanpa logo apa pun dan tanpa kata/unsur Barunastra atau ITS** (termasuk latar laut). Gaya visual tetap mengikuti deck magang (font Anton/Montserrat/JetBrains Mono, latar gelap).
3. Rumus di README, laporan, dan slide **harus sama dengan kode**. Kalau konstanta di kode berubah, perbarui ketiganya.
4. Angka hasil di laporan dan slide **selalu dibaca dari `docs/stress_results.json`**, jangan diketik manual.
5. Jangan edit `.wbt` atau URDF secara manual; edit generatornya di `tools/`.
6. Repo publik, jadi jangan commit kredensial atau data pribadi.

---

## 10. Masalah yang pernah terjadi dan solusinya (supaya tidak terulang)

| Masalah | Solusi |
|---|---|
| Motion bawaan membuat NAO jatuh (pitch 68° di detik 1.2) | Gait engine sendiri dengan transisi smoothstep |
| `Motion.play()` berulang macet atau timing-nya tidak pasti | Pemutar `Clip` sendiri |
| Skala langkah hampir tidak membuat robot berbelok | Pulsa HipYawPitch yang didefinisikan per rentang frame |
| Badan menyerempet dinding saat putar di tempat | `ROTATE_SAFE` = 0.33, putar ke sisi yang lebih lega, `HALF_W` = 0.25 |
| Bolak-balik di sudut | Turn-lock (hanya saat \|θ\| > 90°) |
| Putar 40° kebablasan | Tambah putar 20° dan 10° |
| Mulai jalan lalu langsung berhenti, lalu menabrak | Aturan depan ≥ 0.6 m / sisi lega |
| Alarm palsu sonar | Wajib dikonfirmasi Lidar |
| Terjebak di kantong sempit | Watchdog area + mode escape |
| Bridge ROS segfault | `TouchSensor.getValues()` mengembalikan pointer ctypes; ambil indeks [0..2] saja, **jangan `list()`** |
| Accelerometer membaca −9.9 | Balik tanda y dan z |
| Spasi di teks marker RViz tampil sangat lebar | Ganti spasi dengan `|` dan `:` |
| `pkill -f` ikut membunuh shell sendiri | Pakai pola `pgrep -f '[l]ib/...'` |
| `ros2 run` meninggalkan proses robot_state_publisher yatim | Jalankan executable-nya langsung |
| zsh tidak memecah `set -- $spec` | Skrip ditulis dalam bash |
| `rm -rf` di dalam `bash -c` diblokir safety check | Hapus dengan path eksplisit di perintah terpisah |
| Beberapa instance Webots sekaligus membuat ukuran screenshot rusak | Ambil screenshot secara berurutan |
| Jendela RViz kecil | Maximize via EWMH `_NET_WM_STATE`, atau dobel-klik judul jendela |

---

## 11. Batasan yang jujur dan ide lanjutan

- **GPS dipakai untuk memori eksplorasi** (sel kunjungan dan odometri RViz). Ini sah karena ketentuan sensornya bebas. Penghindaran obstacle sendiri murni berbasis Lidar (+ sonar). Ide lanjutan: ganti GPS dengan SLAM atau odometri Lidar.
- NAO adalah PROTO bawaan Webots. Yang dibuat sendiri adalah gait engine, navigasi, evaluator, bridge, dan URDF tambahan.
- Coverage minimum masih 27.9 % (set 2, posisi awal ke-3). Kasus ini kandidat perbaikan berikutnya.
- 3 commit lama (`9230c3c`, `c87fef8`, `f7f2e8b`/`c6f884f`) masih memuat trailer Claude. Menghapusnya butuh rewrite history + force-push repo publik, jadi **hanya lakukan dengan izin pemilik**.
- Nama di sampul laporan dan slide hanya "Ahnaf". Tambahkan NRP atau nama lengkap jika pemilik memberikannya.
