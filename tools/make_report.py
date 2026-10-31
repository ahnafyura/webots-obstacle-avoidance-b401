"""Membuat laporan PDF: docs/Laporan_Obstacle_Avoidance_B401.pdf (versi humanoid)."""
import json
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, 'docs', 'images')
OUT = os.path.join(ROOT, 'docs', 'Laporan_Obstacle_Avoidance_B401.pdf')
REPO = 'https://github.com/ahnafyura/webots-obstacle-avoidance-b401'

FD = '/usr/share/fonts/truetype/dejavu'
pdfmetrics.registerFont(TTFont('DV', f'{FD}/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DV-B', f'{FD}/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DV-I', f'{FD}/DejaVuSans-Oblique.ttf'))
pdfmetrics.registerFont(TTFont('DVM', f'{FD}/DejaVuSansMono.ttf'))
registerFontFamily('DV', normal='DV', bold='DV-B', italic='DV-I', boldItalic='DV-B')

ss = getSampleStyleSheet()
BLUE = colors.HexColor('#1f3f8f')
body = ParagraphStyle('body', parent=ss['Normal'], fontName='DV', fontSize=10, leading=14.5,
                      alignment=TA_JUSTIFY, spaceAfter=6)
h1 = ParagraphStyle('h1', parent=body, fontName='DV-B', fontSize=15, leading=20, textColor=BLUE,
                    spaceBefore=10, spaceAfter=8, alignment=0)
h2 = ParagraphStyle('h2', parent=body, fontName='DV-B', fontSize=11.5, leading=16, textColor=BLUE,
                    spaceBefore=8, spaceAfter=4, alignment=0)
cap = ParagraphStyle('cap', parent=body, fontName='DV-I', fontSize=8.5, leading=11,
                     alignment=TA_CENTER, textColor=colors.HexColor('#444'), spaceAfter=10)
bullet = ParagraphStyle('bullet', parent=body, leftIndent=14, bulletIndent=4, spaceAfter=3)
code = ParagraphStyle('code', fontName='DVM', fontSize=7.2, leading=9.0,
                      backColor=colors.HexColor('#f4f5f7'), borderColor=colors.HexColor('#d0d4da'),
                      borderWidth=0.5, borderPadding=5, spaceBefore=4, spaceAfter=10)
formula = ParagraphStyle('formula', parent=body, alignment=TA_CENTER, fontSize=10.5, spaceBefore=2,
                         spaceAfter=8)
cell = ParagraphStyle('cell', parent=body, fontSize=8.6, leading=11.2, alignment=0, spaceAfter=0)
cellb = ParagraphStyle('cellb', parent=cell, fontName='DV-B', textColor=colors.white)

W = A4[0] - 4 * cm
story = []
fig_no = [0]
tab_no = [0]


def P(t, s=body):
    story.append(Paragraph(t, s))


def F(t):
    story.append(Paragraph(t, formula))


def bullets(items):
    for it in items:
        story.append(Paragraph(it, bullet, bulletText='•'))


def fig(name, caption, width=W * 0.85):
    from PIL import Image as PI
    path = os.path.join(IMG, name)
    w, h = PI.open(path).size
    fig_no[0] += 1
    story.append(KeepTogether([Image(path, width=width, height=width * h / w),
                               Paragraph(f'Gambar {fig_no[0]}. {caption}', cap)]))


def table(rows, widths, caption=None):
    data = [[Paragraph(str(c), cellb if i == 0 else cell) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#b8bec8')),
          ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
          ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
          ('BACKGROUND', (0, 0), (-1, 0), BLUE)]
    st += [('BACKGROUND', (0, i), (-1, i), colors.HexColor('#eef1f7')) for i in range(2, len(rows), 2)]
    t.setStyle(TableStyle(st))
    items = [t]
    if caption:
        tab_no[0] += 1
        items.insert(0, Paragraph(f'Tabel {tab_no[0]}. {caption}', cap))
    story.append(KeepTogether(items))
    story.append(Spacer(1, 6))


def codeblock(text):
    story.append(Preformatted(text.rstrip('\n'), code))


# ---------------------------------------------------------------------------
R = json.load(open(os.path.join(ROOT, 'docs', 'stress_results.json')))
N, A = R['kebaruan'], R['acak']
UP = R['peningkatan_persen']
TOT_RUNS = len(N['runs']) + len(A['runs'])
TOT_MIN = (N['waktu_total_s'] + A['waktu_total_s']) / 60
TOT_COL = N['tabrakan'] + A['tabrakan']
TOT_FALL = N['jatuh'] + A['jatuh']
TOT_DIST = N['jarak_total_m'] + A['jarak_total_m']
STARTS = ['(−2.0, −2.0, 45°)', '(2.1, 1.0, −132°)', '(0.0, 1.2, 0°)', '(2.0, −0.8, 180°)',
          '(−2.0, 1.9, −29°)', '(−0.6, −0.1, 90°)', '(−0.5, −2.1, 0°)', '(1.45, 0.35, 115°)',
          '(−2.1, 0.6, 0°)', '(0.0, −1.1, 90°)', '(1.1, −0.9, 143°)', '(−1.0, 0.0, −57°)',
          '(0.3, 0.9, 57°)', '(2.15, −1.0, 90°)', '(−0.9, −2.1, 57°)', '(0.5, 2.1, 0°)']

# ---------------------------------------------------------------------------
# Sampul
# ---------------------------------------------------------------------------
title = ParagraphStyle('title', parent=body, fontName='DV-B', fontSize=22, leading=28,
                       alignment=TA_CENTER, textColor=BLUE)
sub = ParagraphStyle('sub', parent=body, fontSize=12, leading=17, alignment=TA_CENTER)
story += [Spacer(1, 1.6 * cm), Paragraph('LAPORAN TUGAS PELATIHAN LAB B401', sub), Spacer(1, 0.4 * cm),
          Paragraph('Robot Humanoid Obstacle Avoidance<br/>dengan Lidar 360° di Atas Kepala', title),
          Spacer(1, 0.4 * cm),
          Paragraph('Gait engine per sendi, navigasi koridor Lidar, dan eksplorasi berbasis kebaruan '
                    'di Webots', sub), Spacer(1, 0.7 * cm)]
fig('overview.jpg', 'Robot humanoid NAO (25 DOF) dengan Lidar 360° di atas kepala, di arena 5 × 5 m '
    'berisi 12 obstacle.', W)
story += [Spacer(1, 0.4 * cm), Paragraph('Disusun oleh: <b>Ahnaf</b>', sub),
          Paragraph(f'Repositori: <font color="#1f3f8f"><link href="{REPO}">{REPO}</link></font>', sub),
          Paragraph('Webots R2025a · Python 3 · ROS 2 Jazzy (RViz2)', sub),
          Paragraph('November 2026', sub), PageBreak()]

# ---------------------------------------------------------------------------
P('1. Pendahuluan', h1)
P('1.1 Latar Belakang', h2)
P('Pada modul pelatihan, robot dirakit sebagai robot beroda <i>line tracer</i>. Tugas ini meminta robot '
  '<b>obstacle avoidance</b> dengan bentuk dan sensor bebas, di arena yang berisi obstacle di bagian tengah, '
  'bukan hanya dinding pinggir. Proyek ini memakai robot <b>humanoid</b> (berjalan dengan dua kaki). '
  'Humanoid jauh lebih sulit dibanding robot beroda: robot harus tetap seimbang di setiap langkah, setiap '
  'sendi harus digerakkan dengan benar, dan robot tidak dapat berbelok atau berhenti seketika. Sensor '
  'utamanya Lidar 360° yang dipasang di atas kepala.')
P('1.2 Ketentuan Tugas dan Pemenuhannya', h2)
table([
    ['Ketentuan', 'Implementasi', 'Status'],
    ['Robot obstacle avoidance', f'Humanoid berjalan otonom dan menghindari obstacle. Diuji {TOT_RUNS} kali × '
     f'10 menit ({TOT_MIN / 60:.1f} jam simulasi) dengan hasil {TOT_COL} tabrakan dan {TOT_FALL} kali jatuh.', '✔'],
    ['Bentuk robot bebas', 'Humanoid NAO 25 DOF. Setiap sendi dikendalikan oleh gait engine buatan sendiri '
     '(transisi halus, siklus jalan kontinu, belok sambil jalan).', '✔'],
    ['Obstacle di arena, tidak hanya pinggiran', '12 obstacle setinggi 0.8 m di dalam arena 5 × 5 m: kotak, '
     'kotak miring, tabung, dinding, dan siku-L (sudut cekung).', '✔'],
    ['Sensor bebas', 'Lidar 360° di kepala (utama), 2 sonar, IMU, gyro, accelerometer, GPS, sensor gaya '
     'kaki (FSR), kamera, dan sensor posisi sendi. Semua dapat ditampilkan di RViz2.', '✔'],
], [3.8 * cm, 10.6 * cm, 1.8 * cm], 'Pemenuhan ketentuan tugas')
P('1.3 Tujuan', h2)
bullets(['Membuat humanoid yang dapat berjalan lurus, berbelok sambil berjalan, berputar di tempat, dan '
         'mundur tanpa jatuh.',
         'Menghindari obstacle memakai Lidar 360° di atas kepala, dengan sonar sebagai konfirmasi.',
         'Meningkatkan cakupan (coverage) eksplorasi arena dan membuktikannya secara kuantitatif '
         'dibandingkan eksplorasi acak.',
         'Menampilkan seluruh data sensor dan model robot di RViz2.'])

# ---------------------------------------------------------------------------
P('2. Dasar Teori', h1)
P('2.1 Robot Humanoid dan Gait', h2)
P('Gait adalah pola gerak sendi yang berulang saat berjalan. Satu siklus berisi dua langkah. Setiap langkah '
  'terdiri dari fase <i>double support</i> (kedua kaki menapak) dan <i>single support</i> (satu kaki '
  'terangkat). Saat satu kaki terangkat, pusat massa harus digeser ke atas kaki tumpu agar robot tidak jatuh. '
  'Itulah fungsi ayunan sendi <i>HipRoll</i>/<i>AnkleRoll</i> ke kiri dan ke kanan. Gait pada proyek ini '
  'berbasis <i>keyframe</i>: sudut setiap sendi disimpan setiap 40 ms, lalu diinterpolasi linear di antara '
  'keyframe. Untuk waktu t di antara keyframe k (waktu t<sub>k</sub>, sudut q<sub>k</sub>) dan k+1:')
F('q(t) = q<sub>k</sub> + (q<sub>k+1</sub> − q<sub>k</sub>) · (t − t<sub>k</sub>) / (t<sub>k+1</sub> − t<sub>k</sub>)')
P('2.2 Lidar', h2)
P('Lidar mengukur jarak dari waktu tempuh pantulan laser: d = c·t/2. Lidar 2D berputar menghasilkan deret '
  'jarak per sudut. Dari hasil uji di Webots, Lidar 360 sinar ini mengurutkan data sebagai berikut: '
  'indeks 0 mengarah ke belakang, lalu searah jarum jam (90 = kiri, 180 = depan, 270 = kanan). Jadi sudut '
  'sinar ke-i adalah θ<sub>i</sub> = π − i·(2π/360), dan titiknya dalam frame robot adalah '
  '(x, y) = (r<sub>i</sub> cos θ<sub>i</sub>, r<sub>i</sub> sin θ<sub>i</sub>) dengan x ke depan dan y ke kiri.')
P('2.3 Sensor Pendukung', h2)
bullets(['<b>Sonar</b> (ultrasonik): mengukur jarak dari pantulan suara. Pancarannya lebar (sekitar 60°), '
         'sehingga baik untuk deteksi dekat tetapi kurang tepat arahnya.',
         '<b>IMU</b> (InertialUnit): memberi orientasi roll, pitch, dan yaw. Roll dan pitch dipakai untuk '
         'mendeteksi robot jatuh, yaw sebagai arah hadap.',
         '<b>Gyro</b> dan <b>accelerometer</b>: kecepatan sudut dan percepatan badan.',
         '<b>GPS</b>: posisi robot di arena, dipakai untuk memori eksplorasi (sel mana yang sudah dikunjungi).',
         '<b>FSR</b> (force sensitive resistor) di telapak kaki: gaya tapak, menunjukkan kaki mana yang menumpu.',
         '<b>Sensor posisi sendi</b>: sudut aktual setiap sendi, dipakai untuk transisi halus dan model robot di RViz2.'])
P('2.4 Navigasi Reaktif dan Eksplorasi', h2)
P('Navigasi reaktif memutuskan gerak dari pembacaan sensor saat itu. Agar robot tidak hanya menghindar tetapi '
  'juga menjelajahi arena, dipakai memori kunjungan berbentuk grid. Arah menuju sel yang jarang dikunjungi '
  'diberi nilai lebih tinggi, mirip prinsip eksplorasi <i>frontier</i>. Kinerja eksplorasi diukur dengan '
  '<b>coverage</b>, yaitu persentase sel arena yang dapat dilalui dan pernah dikunjungi.')

# ---------------------------------------------------------------------------
P('3. Perancangan Robot', h1)
P('Robot yang dipakai adalah model humanoid NAO dari Webots: tinggi 57 cm, 25 derajat kebebasan (DOF). '
  'Lidar ditambahkan pada <i>headSlot</i>, yaitu di atas kepala, 0.57 m dari lantai. Dari posisi ini Lidar '
  'dapat melihat ke segala arah tanpa terhalang badan atau lengan robot. InertialUnit tambahan dipasang di '
  '<i>bodySlot</i>, karena InertialUnit bawaan NAO tidak mengeluarkan sudut yaw.')
fig('robot_closeup.jpg', 'Humanoid saat berjalan. Silinder merah di atas kepala adalah Lidar 360°.', W * 0.78)
table([
    ['Bagian', 'Sendi / device', 'Keterangan'],
    ['Kaki (12 sendi)', 'HipYawPitch, HipRoll, HipPitch, KneePitch, AnklePitch, AnkleRoll (kiri & kanan)',
     'Digerakkan gait engine setiap 20 ms'],
    ['Lengan (8 sendi)', 'ShoulderPitch, ShoulderRoll, ElbowYaw, ElbowRoll (kiri & kanan)', 'Ditahan di '
     'samping badan saat berjalan'],
    ['Kepala (2 sendi)', 'HeadYaw, HeadPitch', 'Ditahan 0 agar Lidar tetap datar'],
    ['Lidar 360°', 'Lidar <font face="DVM">lidar</font>', '360 sinar, 0.06–4 m, noise 0.2%, tinggi 0.57 m'],
    ['Sonar ×2', '<font face="DVM">Sonar/Left</font>, <font face="DVM">Sonar/Right</font>',
     'Jangkauan 0.25–2.55 m, di dada'],
    ['IMU', 'InertialUnit <font face="DVM">imu_body</font>', 'Roll, pitch, yaw'],
    ['Gyro, accelerometer', '<font face="DVM">gyro</font>, <font face="DVM">accelerometer</font>', 'Dipublish ke ROS 2'],
    ['GPS', '<font face="DVM">gps</font>', 'Posisi untuk memori eksplorasi'],
    ['FSR kaki ×2', '<font face="DVM">LFsr</font>, <font face="DVM">RFsr</font>', 'Gaya tapak 3 sumbu'],
    ['Kamera', '<font face="DVM">CameraTop</font>', '320 × 240, dipublish ke ROS 2'],
], [3.2 * cm, 7.6 * cm, 5.4 * cm], 'Sendi dan sensor robot humanoid')

# ---------------------------------------------------------------------------
P('4. Gait Engine: Membuat Humanoid Berjalan dengan Baik', h1)
P('4.1 Masalah pada Motion Bawaan', h2)
P('Webots menyediakan file gerak (.motion) untuk NAO. Saat diuji langsung, gerakan <i>Forwards50</i> '
  '(jalan panjang) membuat robot <b>jatuh ke depan pada detik ke-1.2</b> (pitch badan 68°). Penyebabnya, file '
  'motion langsung melompat ke pose pertamanya (lutut ditekuk 1.22 rad), sedangkan robot berdiri dengan kaki '
  'lurus. Lompatan sudut sebesar ini menyentak badan. Selain itu, file motion tidak dapat disambung menjadi '
  'jalan kontinu dan tidak ada gerak belok sambil berjalan. Karena itu dibuat gait engine sendiri '
  '(<font face="DVM">gait.py</font>) yang mengendalikan setiap sendi secara langsung.')
P('4.2 Transisi Halus Antar Gerakan', h2)
P('Sebelum klip gerak dimulai, setiap sendi j berpindah dari sudut target terakhir q<sub>j,awal</sub> ke '
  'sudut pertama klip q<sub>j,1</sub> selama T<sub>b</sub> (0.4 s), memakai fungsi <i>smoothstep</i> yang '
  'kecepatan awal dan akhirnya nol, sehingga tidak ada sentakan:')
F('u = t / T<sub>b</sub>,   s(u) = 3u² − 2u³,   q<sub>j</sub>(t) = q<sub>j,awal</sub> + (q<sub>j,1</sub> − '
  'q<sub>j,awal</sub>) · s(u),   0 ≤ t ≤ T<sub>b</sub>')
P('4.3 Siklus Jalan Kontinu', h2)
P('Gerakan Forwards50 dianalisis dengan autokorelasi sudut <i>HipRoll</i>. Periode ayunannya 25.5 frame '
  '(1.02 s per langkah). Frame 51 dan frame 102 ternyata <b>identik</b> (selisih maksimum 0 rad untuk semua '
  'sendi). Jadi frame 51–102 adalah satu siklus dua langkah (2.04 s) yang dapat diulang tanpa sambungan '
  'kasar. Forwards50 dipotong menjadi tiga klip: <i>mulai</i> (frame 0–51), <i>siklus</i> (51–102, '
  'diulang selama jalan aman), dan <i>berhenti</i> (102–170).')
fig('gait_cycle.png', 'Atas: sudut sendi kaki kiri dalam satu siklus jalan. Bawah: sendi HipYawPitch, '
    'datar saat jalan lurus dan berpulsa saat belok kiri.', W * 0.85)
P('4.4 Belok Sambil Berjalan', h2)
P('Pada gerakan belok bawaan (TurnLeft40), sendi <i>HipYawPitch</i> dibuka sampai −0.48 rad saat satu kaki '
  'terangkat, lalu ditutup kembali saat kaki itu menapak. Pola yang sama disisipkan ke siklus jalan sebagai '
  'satu pulsa per siklus. Untuk belok kiri, pulsa naik pada frame 7–20 dan turun pada frame 20–33. Untuk belok '
  'kanan, pulsa naik pada frame 20–33 dan turun pada frame 33–46. Dengan amplitudo A = 0.25 rad dan '
  'k = indeks frame dalam siklus, belok kiri dirumuskan:')
F('q<sub>HipYawPitch</sub>(k) = q<sub>siklus</sub>(k) − A · s(p(k)),   p(k) = (k−7)/13 untuk 7 ≤ k &lt; 20,'
  '   p(k) = 1 − (k−20)/13 untuk 20 ≤ k &lt; 33,   p(k) = 0 di luar itu')
P('dengan s(·) fungsi smoothstep di atas. Rumus belok kanan sama, dengan batas frame 20, 33, dan 46. '
  'Pulsa bernilai nol di batas siklus, jadi siklus lurus, belok kiri, dan belok kanan dapat disambung bebas. '
  'Amplitudo 0.4–0.5 rad sudah diuji, tetapi hasilnya tidak konsisten karena kaki tergelincir. Karena itu '
  'dipilih 0.25 rad. Putar di tempat 20° dan 10° dibuat dengan cara serupa: hanya sendi HipYawPitch dari '
  'TurnLeft40/TurnRight40 yang diskalakan 0.5 dan 0.25.')
table([
    ['Gerakan', 'Durasi', 'Hasil terukur (rata-rata)'],
    ['jalan_lurus (1 siklus)', '2.04 s', '+0.18 m, 0°'],
    ['jalan_kiri / jalan_kanan (1 siklus)', '2.04 s', '+0.16 m dan +17°  /  +0.17 m dan −13°'],
    ['jalan_mulai / jalan_berhenti', '2.04 / 2.68 s', '+0.10 m  /  +0.18 m'],
    ['putar_kiri10 / putar_kanan10', '2.9 s', '+10.9°  /  −11.3°'],
    ['putar_kiri20 / putar_kanan20', '2.9 s', '+20.7°  /  −20.7°'],
    ['putar_kiri40 / putar_kanan40', '2.9 s', '+39.4°  /  −39.7°'],
    ['putar_kiri60 / putar_kanan60', '4.5 s', '+59.1°  /  −59.1°'],
    ['putar_balik', '9.0 s', '+196°'],
    ['mundur  /  maju_kecil', '2.6 s', '−0.10 m  /  +0.10 m'],
], [6.0 * cm, 2.8 * cm, 7.4 * cm], 'Primitif gerak hasil gait engine (diukur di simulasi, tanpa jatuh)')

# ---------------------------------------------------------------------------
P('5. Perancangan Arena', h1)
P('Arena berukuran 5 × 5 m dengan 12 obstacle setinggi 0.8 m. Obstacle harus lebih tinggi dari Lidar '
  '(0.57 m) agar terlihat. Jarak antar obstacle bervariasi: sebagian celah bisa dilewati humanoid, '
  'sebagian sengaja terlalu sempit, termasuk sudut cekung siku-L dan kantong sempit di dekat tiang.')
fig('top_view.jpg', 'Tampak atas arena 5 × 5 m dengan 12 obstacle.', W * 0.6)

# ---------------------------------------------------------------------------
P('6. Algoritma Navigasi', h1)
P('6.1 Pemilihan Arah dengan Koridor', h2)
P('Keputusan diambil setiap kali satu gerakan selesai. Saat berjalan, keputusan diambil di setiap batas '
  'siklus (setiap 2.04 s). Untuk 36 kandidat arah θ (−180° sampai 170°, kelipatan 10°) dihitung jarak '
  'bebas koridor selebar 2w (w = 0.25 m, yaitu setengah lebar bahu dan lengan humanoid ditambah margin). '
  'Setiap titik Lidar (x, y) diproyeksikan:')
F('ℓ = x cos θ + y sin θ   (searah θ),     d = −x sin θ + y cos θ   (menyamping)')
F('bebas(θ) = min { ℓ : ℓ &gt; 0 dan |d| &lt; w },   dibatasi maksimum 3.5 m')
fig('corridor_concept.png', 'Koridor kandidat arah. Arah lurus terhalang obstacle, arah 35° bebas.', W * 0.55)
P('6.2 Skor Arah dan Eksplorasi Kebaruan', h2)
P('Arah dengan bebas(θ) &lt; 0.85 m tidak dipertimbangkan (0.6 m jika robot sudah berputar 360° tanpa '
  'menemukan jalan). Untuk arah lainnya dihitung skor berikut, lalu '
  'dipilih arah θ* dengan skor terbesar:')
F('skor(θ) = min(bebas, 2)/2 + 0.6 · K(θ) − 0.35 · |θ|/π − 0.25 · |wrap(ψ + θ − ψ<sub>tujuan</sub>)|/π')
bullets(['<b>min(bebas, 2)/2</b>: mengutamakan arah yang lapang. Nilainya 0 sampai 1 dan jarak di atas 2 m '
         'dianggap sama.',
         '<b>K(θ), kebaruan</b>: rata-rata 1/(1 + n<sub>c</sub>) untuk sel grid 0.25 m yang dilalui garis '
         'arah θ, mulai 0.5 m sampai min(bebas, 2.5 m). n<sub>c</sub> adalah jumlah kunjungan sel c (dicatat '
         'setiap 0.5 s dari posisi GPS). Sel yang belum pernah dikunjungi bernilai 1.',
         '<b>|θ|/π</b>: penalti belok, karena humanoid lambat berbelok.',
         '<b>Persistensi</b>: ψ adalah arah hadap robot (yaw IMU) dan ψ<sub>tujuan</sub> adalah arah tujuan '
         'pada keputusan sebelumnya (frame dunia). Suku ini mencegah tujuan berganti-ganti sehingga robot tidak '
         'berputar bolak-balik. Fungsi wrap(·) memetakan sudut ke rentang (−π, π].'])
P('Sebagai pembanding, <b>mode acak</b> mengganti suku kebaruan dengan −0.3·|wrap(ψ + θ − ψ<sub>acak</sub>)|/π, '
  'dengan ψ<sub>acak</sub> arah acak yang diganti setiap 20 s. Semua aturan keselamatan sama untuk kedua mode.')
P('6.3 State Machine', h2)
fig('state_machine.png', 'State machine humanoid.', W)
P('6.4 Aturan Keselamatan', h2)
table([
    ['Aturan', 'Ambang', 'Alasan'],
    ['Lanjut satu siklus jalan', 'koridor ≥ 0.85 m searah langkah, koridor lurus ≥ 0.70 m saat berbelok',
     'Satu siklus (0.18 m) + fase berhenti (0.18 m) + badan + margin'],
    ['Mulai jalan', 'koridor depan ≥ 0.60 m, atau ≥ 0.45 m jika samping (30°–120°) ≥ 0.35 m',
     'Fase mulai 0.10 m + berhenti 0.18 m. Lengan bisa menyenggol obstacle di samping'],
    ['Berputar di tempat', 'semua titik ≥ 0.33 m. Jika tidak: mundur atau maju kecil dulu',
     'Lengan dan ayunan badan saat berputar'],
    ['Mundur', 'obstacle di depan (±50°) &lt; 0.30 m dan belakang ≥ 0.45 m', 'Terlalu dekat untuk berbelok'],
    ['Sonar', '&lt; 0.30 m, berlaku hanya jika Lidar depan &lt; 0.6 m', 'Pancaran sonar lebar sehingga sering '
     'menangkap obstacle di samping'],
    ['Belokan besar (|θ| &gt; 90°)', 'putar ke sisi yang lebih lega, arah dikunci',
     'Mencegah putar kiri-kanan bolak-balik'],
    ['Watchdog macet', 'pindah &lt; 0.15 m dalam 30 s → putar 60°', 'Keluar dari kebuntuan'],
    ['Watchdog wilayah', 'selalu dalam radius 0.5 m selama 60 s → mode lolos 25 s',
     'Keluar dari kantong sempit dengan memilih arah paling lega'],
    ['Jatuh', '|roll| atau |pitch| &gt; 45° → gerakan bangun', 'Pemulihan'],
], [3.6 * cm, 6.4 * cm, 6.2 * cm], 'Aturan keselamatan dan ambangnya')

# ---------------------------------------------------------------------------
P('7. Pengujian dan Hasil', h1)
P('7.1 Metode', h2)
P('World dilengkapi robot <b>evaluator</b> (Supervisor) yang hanya mengamati. <b>Tabrakan</b> dideteksi dari '
  'titik kontak fisik robot yang lebih tinggi dari 3 cm, karena telapak kaki menyentuh lantai di z ≈ 0. Metode '
  'ini sudah divalidasi dengan robot uji yang sengaja ditabrakkan. <b>Jatuh</b> dideteksi saat ketinggian '
  'torso turun di bawah 0.22 m (tinggi saat berdiri sekitar 0.30 m). <b>Clearance</b> adalah jarak analitik '
  'dari pusat robot ke permukaan obstacle terdekat, dikurangi radius pembungkus 0.18 m. <b>Coverage</b> '
  'adalah persentase sel grid 20 cm yang dapat dilalui dan pernah dikunjungi.')
P(f'Matriks uji: 16 posisi awal (2 set × 8) × 2 mode (kebaruan dan acak) × 10 menit = {TOT_RUNS} uji, '
  f'total {TOT_MIN / 60:.1f} jam simulasi, dijalankan otomatis dengan <font face="DVM">tools/stress_test.sh</font>.')
P('7.2 Hasil', h2)
table([
    ['Mode', 'Uji', 'Tabrakan', 'Jatuh', 'Jarak total', 'Clearance min*', 'Coverage rata-rata (min–maks)'],
    ['<b>Kebaruan</b>', str(len(N['runs'])), f"<b>{N['tabrakan']}</b>", f"<b>{N['jatuh']}</b>",
     f"{N['jarak_total_m']:.0f} m", f"{N['clearance_min_m'] * 100:.1f} cm",
     f"<b>{N['coverage_rata']:.1f} %</b> ({N['coverage_min']:.1f}–{N['coverage_max']:.1f})"],
    ['Acak', str(len(A['runs'])), str(A['tabrakan']), str(A['jatuh']), f"{A['jarak_total_m']:.0f} m",
     f"{A['clearance_min_m'] * 100:.1f} cm",
     f"{A['coverage_rata']:.1f} % ({A['coverage_min']:.1f}–{A['coverage_max']:.1f})"],
], [2.2 * cm, 1.2 * cm, 1.8 * cm, 1.4 * cm, 2.2 * cm, 2.4 * cm, 5.0 * cm], 'Ringkasan hasil uji')
P('<font size="8">Jarak dihitung dari posisi setiap 1 detik, sehingga ayunan badan ke kiri dan kanan '
  'tidak ikut terhitung.</font>')
P('<font size="8">*Terhadap lingkaran pembungkus 0.18 m. Nilai mendekati 0 atau sedikit negatif tidak '
  'berarti tabrakan, karena badan humanoid lebih ramping dari lingkaran tersebut. Tabrakan diukur terpisah '
  'dari kontak fisik.</font>')
P(f'Selama {TOT_MIN / 60:.1f} jam simulasi dengan total jarak tempuh {TOT_DIST:.0f} m, humanoid '
  f'<b>tidak pernah menabrak ({TOT_COL}) dan tidak pernah jatuh ({TOT_FALL})</b>. Eksplorasi kebaruan '
  f'menghasilkan coverage rata-rata {N["coverage_rata"]:.1f} %, sedangkan mode acak {A["coverage_rata"]:.1f} %. '
  f'Artinya coverage <b>naik {UP:.0f} %</b> dengan posisi awal, durasi, dan aturan keselamatan yang sama.')
fig('trajectory_compare.png', 'Lintasan 8 uji (set 1). Kiri: mode acak. Kanan: mode kebaruan, yang '
    'menjangkau lebih banyak area dan celah di antara obstacle.', W)
fig('coverage_time.png', 'Coverage terhadap waktu, rata-rata 16 uji per mode.', W * 0.8)
fig('coverage_bar.png', 'Coverage setiap uji dengan posisi awal yang sama untuk kedua mode.', W)
fig('clearance.png', 'Distribusi jarak aman seluruh uji.', W * 0.75)
rows = [['#', 'Posisi awal', 'Kebaruan: jarak', 'tabrakan/jatuh', 'coverage', 'Acak: coverage']]
for i, (n, a) in enumerate(zip(N['runs'], A['runs'])):
    rows.append([str(i + 1), STARTS[i], f"{n['jarak_tempuh_m']:.1f} m", f"{n['tabrakan']} / {n['jatuh']}",
                 f"{n['coverage_persen']:.1f} %", f"{a['coverage_persen']:.1f} %"])
table(rows, [0.9 * cm, 3.6 * cm, 3.0 * cm, 2.8 * cm, 2.6 * cm, 3.3 * cm], 'Hasil per uji (10 menit)')

# ---------------------------------------------------------------------------
P('8. Masalah yang Ditemukan dan Solusinya', h1)
P('Pengembangan dilakukan secara iteratif. Setiap perubahan diuji ulang dengan uji ketahanan 8 posisi awal. '
  'Tabel berikut merangkum masalah nyata yang ditemukan dari data uji beserta perbaikannya.')
table([
    ['Masalah (dari data)', 'Penyebab', 'Solusi'],
    ['Robot jatuh di detik 1.2 (Forwards50)', 'Motion melompat ke pose lutut 1.22 rad', 'Transisi smoothstep 0.4 s'],
    ['Belok hanya bisa sambil diam (lambat)', 'Tidak ada motion belok sambil jalan', 'Pulsa HipYawPitch per siklus'],
    ['Belok tidak konsisten pada amplitudo besar', 'Kaki tergelincir', 'Amplitudo dibatasi 0.25 rad'],
    ['Lengan menyenggol dinding saat berputar', 'Clearance putar terlalu kecil', 'Clearance 0.33 m dan '
     'putar ke sisi lega'],
    ['Berputar kiri-kanan di sudut ruang (9 menit)', 'Target di belakang berpindah sisi', 'Kunci arah putar'],
    ['Overshoot target kecil (±20°)', 'Putar minimum 40°', 'Putar 20° (HipYawPitch × 0.5)'],
    ['Putar ±20° bolak-balik di dekat celah', 'Resolusi kandidat arah 10° lebih halus dari putar 20°', 'Putar 10° '
     '(HipYawPitch × 0.25)'],
    ['Senggolan saat mulai jalan lalu berhenti', 'Syarat mulai jalan terlalu longgar', 'Mulai jalan perlu '
     '0.60 m, atau 0.45 m jika samping lega'],
    ['Maju-mundur di dekat tiang', 'Sonar menangkap obstacle di samping', 'Sonar perlu konfirmasi Lidar'],
    ['Terjebak di kantong sempit (63–71 % waktu)', 'Skor tidak pernah memilih jalan keluar', 'Watchdog '
     'wilayah dan mode lolos'],
    ['43 % waktu habis untuk putar di tempat', 'Belok hanya saat berhenti', 'Belok sambil jalan sampai ±75°'],
], [5.2 * cm, 5.2 * cm, 5.8 * cm], 'Masalah, penyebab, dan solusi')

# ---------------------------------------------------------------------------
P('9. Visualisasi Semua Sensor di RViz2 (ROS 2)', h1)
P('Controller memiliki jembatan ROS 2 opsional (<font face="DVM">ros_bridge.py</font>) yang aktif otomatis '
  'jika Webots dijalankan dari terminal yang sudah men-<i>source</i> ROS 2 Jazzy. Model robot ditampilkan dari '
  'URDF. Webots dapat mengekspor URDF, tetapi sendi bahu dan leher (Hinge2Joint) belum didukung, sehingga '
  'lengan, kepala, Lidar, dan kamera ditambahkan oleh <font face="DVM">tools/make_urdf.py</font> memakai '
  'dimensi kinematika NAO. Hasilnya, model humanoid di RViz2 bergerak sesuai sudut sendi asli robot.')
table([
    ['Topic', 'Tipe', 'Isi', 'Tampilan RViz2'],
    ['/scan', 'LaserScan', 'Lidar 360°', 'titik merah + jejak 60 s'],
    ['/sonar/left, /sonar/right', 'Range', 'Sonar dada', 'kerucut kuning'],
    ['/imu', 'Imu', 'Orientasi + gyro + accelerometer', 'sumbu imu_body + panel teks'],
    ['/fsr/left, /fsr/right', 'WrenchStamped', 'Gaya telapak kaki', 'panah gaya'],
    ['/camera/image_raw', 'Image', 'Kamera atas NAO', 'panel gambar'],
    ['/joint_states', 'JointState', '24 sudut sendi', 'model robot bergerak'],
    ['/odom, /tf', 'Odometry, tf2', 'GPS + IMU, frame semua link', 'lintasan'],
    ['/oa/decision', 'MarkerArray', 'Koridor, arah, state, sel dikunjungi', 'marker berwarna'],
], [3.8 * cm, 2.7 * cm, 4.8 * cm, 4.9 * cm], 'Topic ROS 2 yang dipublish')
P('Hasil verifikasi: semua topic sensor terkirim sekitar 24.5 Hz (kamera sekitar 5 Hz). Accelerometer '
  'membaca +9.93 m/s² pada sumbu z saat berdiri (sudah disesuaikan dengan orientasi pemasangan sensor yang '
  'terbalik). FSR kaki membaca sekitar 50 N saat satu kaki menumpu. Frame Lidar berada 0.57 m di atas '
  'lantai, sesuai rancangan.')
fig('rviz2.png', 'Tangkapan layar RViz2 saat simulasi berjalan: model humanoid (URDF + joint_states), '
    'jejak Lidar, kerucut sonar, panah gaya kaki, lintasan, sel yang dikunjungi, panel nilai sensor, dan '
    'gambar kamera NAO (kiri atas).', W)
fig('ros_scan_view.png', 'Data /scan dan /odom yang direkam dari robot. Jejak Lidar membentuk peta arena.',
    W * 0.62)

# ---------------------------------------------------------------------------
P('10. Cara Menjalankan', h1)
bullets(['Instal Webots R2025a dan Python 3. Untuk RViz2, instal juga ROS 2 Jazzy.',
         f'<font face="DVM">git clone {REPO}.git</font>',
         'Webots: <font face="DVM">File → Open World</font>, pilih <font face="DVM">worlds/obstacle_avoidance.wbt</font>, lalu tekan Play.',
         'RViz2 dengan semua sensor: <font face="DVM">tools/rviz.sh</font>.',
         'Uji otomatis: <font face="DVM">tools/stress_test.sh 600 kebaruan</font> dan '
         '<font face="DVM">tools/stress_test.sh 600 acak</font> (gunakan <font face="DVM">STARTS_SET=2</font> '
         'untuk set posisi awal kedua), lalu <font face="DVM">python3 tools/plot_results.py</font>.'])

P('11. Kesimpulan', h1)
bullets(['Robot humanoid NAO 25 DOF berhasil berjalan stabil memakai gait engine buatan sendiri. Gait engine ini '
         'mengendalikan setiap sendi dengan transisi smoothstep, siklus jalan kontinu, dan belok sambil '
         f'berjalan. Dalam {TOT_MIN / 60:.1f} jam uji, robot tidak pernah jatuh.',
         f'Lidar 360° di atas kepala dengan pemilihan arah berbasis koridor selebar badan menghasilkan '
         f'<b>{TOT_COL} tabrakan</b> dari {TOT_RUNS} uji, dengan total jarak tempuh {TOT_DIST:.0f} m.',
         f'Eksplorasi kebaruan menaikkan coverage dari {A["coverage_rata"]:.1f} % menjadi '
         f'{N["coverage_rata"]:.1f} % (+{UP:.0f} %).',
         'Semua sensor (Lidar, sonar, IMU, gyro, accelerometer, FSR, kamera, posisi sendi) dan model robot '
         'dapat dipantau langsung di RViz2.',
         'Pengembangan selanjutnya: lokalisasi tanpa GPS (SLAM), gait dengan umpan balik keseimbangan (ZMP), '
         'dan obstacle bergerak.'])

story.append(PageBreak())
P('Lampiran A. Controller humanoid_avoidance.py', h1)
codeblock(open(os.path.join(ROOT, 'controllers', 'humanoid_avoidance', 'humanoid_avoidance.py')).read())
story.append(PageBreak())
P('Lampiran B. Gait engine gait.py', h1)
codeblock(open(os.path.join(ROOT, 'controllers', 'humanoid_avoidance', 'gait.py')).read())


def on_page(c, doc):
    c.saveState()
    c.setFont('DV', 8)
    c.setFillColor(colors.HexColor('#666'))
    if doc.page > 1:
        c.drawString(2 * cm, 1.2 * cm, 'Tugas Pelatihan Lab B401 - Robot Humanoid Obstacle Avoidance')
        c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f'Halaman {doc.page}')
        c.setStrokeColor(colors.HexColor('#c8ccd4'))
        c.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    c.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                        bottomMargin=2 * cm, title='Laporan Robot Humanoid Obstacle Avoidance - Lab B401',
                        author='Ahnaf')
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print('PDF:', OUT)
