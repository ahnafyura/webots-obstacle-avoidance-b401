"""Membuat naskah presentasi: docs/Naskah_Presentasi_B401.pdf.

    python3 tools/make_naskah.py

Naskah mengikuti 25 slide di slides/Presentasi_Obstacle_Avoidance_B401.pdf. Thumbnail tiap
slide dirender dari PDF slide (pdftoppm), dan angka hasil uji dibaca dari docs/stress_results.json.
Jalankan setelah slides/buat_slide.py supaya thumbnail sama dengan slide terbaru.
"""
import glob
import json
import os
import subprocess
import tempfile

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLIDES = os.path.join(ROOT, 'slides', 'Presentasi_Obstacle_Avoidance_B401.pdf')
OUT = os.path.join(ROOT, 'docs', 'Naskah_Presentasi_B401.pdf')
REPO = 'github.com/ahnafyura/webots-obstacle-avoidance-b401'

R = json.load(open(os.path.join(ROOT, 'docs', 'stress_results.json')))
N, A = R['kebaruan'], R['acak']
V = dict(
    runs=len(N['runs']) + len(A['runs']),
    col=N['tabrakan'] + A['tabrakan'],
    fall=N['jatuh'] + A['jatuh'],
    hours=f"{(N['waktu_total_s'] + A['waktu_total_s']) / 3600:.1f}",
    dist=f"{N['jarak_total_m'] + A['jarak_total_m']:.0f}",
    dist_km=f"{(N['jarak_total_m'] + A['jarak_total_m']) / 1000:.1f}",
    cov_n=f"{N['coverage_rata']:.1f}", cov_a=f"{A['coverage_rata']:.1f}",
    nmin=f"{N['coverage_min']:.1f}", nmax=f"{N['coverage_max']:.1f}",
    amin=f"{A['coverage_min']:.1f}", amax=f"{A['coverage_max']:.1f}",
    dn=f"{N['jarak_total_m']:.0f}", da=f"{A['jarak_total_m']:.0f}",
    cln=f"{N['clearance_min_m'] * 100:.1f}", cla=f"{A['clearance_min_m'] * 100:.1f}",
    up=f"{R['peningkatan_persen']:.0f}",
    per_mode=len(N['runs']),
)

FD = '/usr/share/fonts/truetype/dejavu'
pdfmetrics.registerFont(TTFont('DV', f'{FD}/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DV-B', f'{FD}/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DV-I', f'{FD}/DejaVuSans-Oblique.ttf'))
pdfmetrics.registerFont(TTFont('DVM', f'{FD}/DejaVuSansMono.ttf'))
pdfmetrics.registerFont(TTFont('DVS-I', f'{FD}/DejaVuSerif-Italic.ttf'))
registerFontFamily('DV', normal='DV', bold='DV-B', italic='DV-I', boldItalic='DV-B')

BLUE = colors.HexColor('#1f3f8f')
GREY = colors.HexColor('#5a6472')
body = ParagraphStyle('body', fontName='DV', fontSize=10, leading=14.6, alignment=TA_JUSTIFY,
                      spaceAfter=5)
say = ParagraphStyle('say', parent=body, fontSize=10.6, leading=15.6)
small = ParagraphStyle('small', parent=body, fontSize=8.8, leading=12.4, spaceAfter=2)
bul = ParagraphStyle('bul', parent=small, leftIndent=12, bulletIndent=2)
lab = ParagraphStyle('lab', parent=body, fontName='DV-B', fontSize=8.6, textColor=GREY,
                     spaceBefore=4, spaceAfter=2)
h1 = ParagraphStyle('h1', parent=body, fontName='DV-B', fontSize=16, leading=21, textColor=BLUE,
                    spaceBefore=6, spaceAfter=8, alignment=0)
h2 = ParagraphStyle('h2', parent=body, fontName='DV-B', fontSize=11.5, leading=15, textColor=BLUE,
                    spaceBefore=8, spaceAfter=4, alignment=0)
shead = ParagraphStyle('shead', parent=body, fontName='DV-B', fontSize=12, leading=15,
                       textColor=colors.white, alignment=0, spaceAfter=0)
stime = ParagraphStyle('stime', parent=shead, fontName='DV', fontSize=9, alignment=2)
formula = ParagraphStyle('formula', parent=body, fontName='DV', fontSize=10, alignment=TA_CENTER,
                         backColor=colors.HexColor('#f2f4f8'), borderPadding=4, spaceBefore=3,
                         spaceAfter=7)
cell = ParagraphStyle('cell', parent=body, fontSize=8.6, leading=11.4, alignment=0, spaceAfter=0)
cellb = ParagraphStyle('cellb', parent=cell, fontName='DV-B', textColor=colors.white)
title = ParagraphStyle('title', parent=h1, fontSize=24, leading=31, alignment=TA_CENTER)
sub = ParagraphStyle('sub', parent=body, alignment=TA_CENTER, fontSize=11, leading=16, textColor=GREY)

W = A4[0] - 4 * cm
story = []


def m(t):
    """Variabel matematika (miring, serif)."""
    return f'<font name="DVS-I">{t}</font>'


def table(rows, widths):
    data = [[Paragraph(str(c), cellb if i == 0 else cell) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#b8bec8')),
        ('BACKGROUND', (0, 0), (-1, 0), BLUE), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f6fa')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
    story.extend([t, Spacer(1, 8)])


# ---------------------------------------------------------------- thumbnail slide
tmp = tempfile.mkdtemp(prefix='naskah_')
subprocess.run(['pdftoppm', '-r', '48', '-png', SLIDES, os.path.join(tmp, 's')], check=True)
THUMBS = sorted(glob.glob(os.path.join(tmp, 's-*.png')))


def slide(no, judul, durasi, ucapan, teknis=None, rumus=None, transisi=None):
    """Satu blok naskah: header, thumbnail + ucapan, rumus, detail teknis cadangan."""
    head = Table([[Paragraph(f'SLIDE {no} · {judul}', shead), Paragraph(durasi, stime)]],
                 colWidths=[W * 0.78, W * 0.22])
    head.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), BLUE),
                              ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                              ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    tw = 5.4 * cm
    thumb = Image(THUMBS[no - 1], width=tw, height=tw * 810 / 1440)
    first = [Paragraph('YANG DIUCAPKAN', lab)] + [Paragraph(u.format(**V), say) for u in ucapan[:1]]
    top = Table([[thumb, first]], colWidths=[tw + 0.4 * cm, W - tw - 0.4 * cm])
    top.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                             ('LEFTPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 6)]))
    block = [head, top]
    block += [Paragraph(u.format(**V), say) for u in ucapan[1:]]
    for f in rumus or []:
        block.append(Paragraph(f, formula))
    if transisi:
        block.append(Paragraph(f'<i>Transisi:</i> “{transisi.format(**V)}”', small))
    if teknis:
        block.append(Paragraph('DETAIL TEKNIS (CADANGAN UNTUK TANYA JAWAB)', lab))
        block += [Paragraph(t.format(**V), bul, bulletText='•') for t in teknis]
    story.append(KeepTogether(block[:3]))
    story.extend(block[3:])
    story.append(Spacer(1, 12))


# ---------------------------------------------------------------- sampul
story += [Spacer(1, 3 * cm), Paragraph('NASKAH PRESENTASI', sub), Spacer(1, 0.3 * cm),
          Paragraph('Robot Humanoid Obstacle Avoidance', title),
          Paragraph('Sensor: Lidar 360° · Sonar · IMU · Gyro · Accelerometer · GPS · FSR Kaki · Kamera', sub),
          Spacer(1, 0.4 * cm), Paragraph('Tugas Pelatihan Lab B401', sub), Spacer(1, 1.2 * cm),
          Paragraph('Pendamping slide <b>Presentasi_Obstacle_Avoidance_B401.pdf</b> (25 slide). '
                    'Setiap slide berisi teks yang diucapkan, rumus yang dibacakan, dan detail teknis '
                    'cadangan untuk sesi tanya jawab.', sub),
          Spacer(1, 1.2 * cm), Paragraph('Ahnaf Al Ghiffarri Ahtasyafi', sub), Paragraph(REPO, sub), PageBreak()]

# ---------------------------------------------------------------- panduan
story.append(Paragraph('Panduan memakai naskah', h1))
story.append(Paragraph(
    'Target durasi <b>±15 menit</b> presentasi, lalu demo 2–3 menit dan tanya jawab. Bagian '
    '<b>YANG DIUCAPKAN</b> ditulis sebagai kalimat lisan, jadi boleh dibaca langsung atau '
    'diparafrasekan. Bagian <b>DETAIL TEKNIS</b> tidak perlu dibacakan; isinya jawaban kalau penguji '
    'bertanya lebih dalam. Semua angka di naskah sama dengan kode dan dengan '
    '<font name="DVM">docs/stress_results.json</font>.', body))
table([['Bagian', 'Slide', 'Durasi'],
       ['Pembuka dan ketentuan tugas', '1–4', '±2 menit'],
       ['01 Robot: sendi dan sensor', '5–6', '±2 menit'],
       ['02 Gait engine', '7–11', '±3,5 menit'],
       ['03 Navigasi', '12–15', '±3,5 menit'],
       ['04 Pengujian, hasil, RViz2', '16–22', '±3 menit'],
       ['Demo, kesimpulan, Q&amp;A', '23–25', '±1 menit + demo']],
      [W * 0.55, W * 0.2, W * 0.25])

story.append(Paragraph('Persiapan sebelum maju', h2))
for t in ['Buka slide PDF dalam mode layar penuh (F5 / Ctrl+L di penampil PDF).',
          'Siapkan demo di jendela lain: <font name="DVM">cd ~/Documents/Barunastra/obstacle-avoidance-b401 '
          '&amp;&amp; tools/rviz.sh</font>. Perintah ini membuka Webots, robot_state_publisher, dan RViz2 '
          'sekaligus. Di Webots, pause dulu dan reset (Ctrl+Shift+T) supaya robot mulai dari pojok.',
          'Di Webots aktifkan <i>View → Optional Rendering → Show Lidar Point Cloud</i> agar sinar Lidar '
          'terlihat penonton.',
          'Kalau jendela RViz2 kecil, klik dua kali judul jendelanya untuk maximize.',
          'Kalau ROS bermasalah saat presentasi, cukup buka <font name="DVM">worlds/obstacle_avoidance.wbt</font> '
          'di Webots lalu tekan Play. Controller tetap jalan tanpa ROS.']:
        story.append(Paragraph(t, bul, bulletText='•'))

story.append(Paragraph('Perjalanan pengerjaan (cerita di balik slide)', h2))
story.append(Paragraph(
    'Kalau ditanya “bagaimana prosesnya”, ceritakan urutan ini. Pengerjaan dimulai dari modul line '
    'tracer dan contoh Khepera IV. <b>Versi 1</b> adalah robot beroda differential drive (badan Box, roda '
    'HingeJoint, caster BallJoint, seperti modul) dengan Lidar 360° dan sensor ultrasonik; versi ini masih '
    'tersimpan di tag git <font name="DVM">v1-robot-roda</font>. Setelah itu dibuat slide, lalu ROS 2 bridge '
    'dan RViz2 untuk melihat point cloud Lidar. <b>Versi 2</b> (yang dipresentasikan) mengganti robot '
    'menjadi humanoid NAO 25 sendi dengan Lidar di kepala. Tantangannya jauh lebih besar: motion bawaan '
    'membuat NAO jatuh, sehingga saya membuat gait engine sendiri. Setelah robot bisa berjalan, saya '
    'membuat navigasi koridor, menambah memori kebaruan untuk menaikkan coverage, lalu menjalankan stress '
    'test berulang. Setiap kegagalan di data (menyenggol, bolak-balik di sudut, terjebak) saya perbaiki '
    'satu per satu dan diuji ulang, sampai {runs} uji terakhir tanpa tabrakan dan tanpa jatuh. Terakhir, '
    'semua sensor dipublikasikan ke RViz2, dan laporan serta slide dibangun otomatis dari data uji.'
    .format(**V), body))
story.append(PageBreak())

story.append(Paragraph('Naskah per slide', h1))

# ---------------------------------------------------------------- 1–4 pembuka
slide(1, 'Sampul', '±20 dtk', [
    'Assalamualaikum dan selamat pagi/siang. Saya Ahnaf Al Ghiffarri Ahtasyafi. Untuk tugas pelatihan Lab B401, saya membuat '
    '<b>robot humanoid obstacle avoidance</b> di Webots. Robotnya berjalan dengan dua kaki. Sensor yang '
    'dipakai adalah Lidar 360 derajat, dua sonar, IMU, gyro, accelerometer, GPS, sensor gaya di telapak '
    'kaki, dan kamera, dan seluruhnya bisa dipantau lewat ROS 2 di RViz2.'],
    teknis=['Simulator Webots R2025a, controller Python 3, ROS 2 Jazzy (opsional; tanpa rclpy controller tetap jalan).'])

slide(2, 'Apa yang dibuat?', '±30 dtk', [
    'Singkatnya, ini robot humanoid yang menjelajahi arena 5 × 5 meter tanpa menabrak 12 obstacle. '
    'Robotnya punya 25 sendi, dan semuanya digerakkan oleh <b>gait engine</b> yang saya tulis sendiri. '
    'Matanya Lidar 360 derajat di kepala. Dari {runs} kali pengujian, jumlah tabrakannya {col}.'],
    teknis=['Bagian yang saya buat sendiri: gait engine, navigasi + state machine + watchdog, evaluator '
            'otomatis, ROS 2 bridge, URDF tambahan, generator world, laporan, dan slide.',
            'Model NAO sendiri adalah PROTO bawaan Webots; file .motion juga bawaan Webots (Apache 2.0).'])

slide(3, 'Ketentuan tugas', '±40 dtk', [
    'Tugasnya punya empat ketentuan. Pertama, robot harus menghindari obstacle: sudah diuji {runs} kali '
    'masing-masing 10 menit, hasilnya {col} tabrakan dan {fall} kali jatuh. Kedua, bentuk robot bebas: saya '
    'pilih humanoid NAO 25 sendi. Ketiga, obstacle harus ada di dalam arena, bukan hanya dinding pinggir: '
    'ada 12 obstacle berupa kotak, tabung, dinding miring, dan siku-L. Keempat, sensor bebas: saya memakai '
    'Lidar di kepala, sonar, IMU, gyro, accelerometer, GPS, sensor gaya di kaki, dan kamera.'],
    teknis=['Tabrakan dihitung oleh Supervisor terpisah yang melihat kontak fisik, bukan oleh robot itu sendiri, '
            'jadi robot tidak bisa “mengaku” aman.'])

slide(4, 'Alur presentasi', '±15 dtk', [
    'Presentasi saya bagi empat bagian: robotnya dulu, yaitu sendi dan sensor; lalu gait, bagaimana '
    'membuat robot bisa berjalan; lalu navigasi, bagaimana memilih arah; dan terakhir hasil pengujian, '
    'RViz2, dan demo.'])

# ---------------------------------------------------------------- 5–6 robot
slide(5, 'Robot humanoid', '±1 menit', [
    'Robotnya NAO, tingginya 57 cm. Kotak merah di atas kepala itu Lidar. Ada 12 sendi di kaki: '
    'HipYawPitch, HipRoll, HipPitch, Knee, AnklePitch, dan AnkleRoll di masing-masing kaki. Lengan punya '
    '8 sendi, dan kepala 2 sendi. Sendi kepala sengaja ditahan supaya Lidar tetap datar.',
    'Di kotak hijau ada empat tantangan utama selama membuat humanoid ini. Pertama, <b>jatuh</b>: motion '
    'bawaan Webots langsung menjatuhkan robot di detik 1,2, sehingga saya harus menulis gait engine '
    'sendiri dengan transisi halus. Ini akan saya jelaskan di bagian berikutnya. Kedua, <b>belok</b>: '
    'humanoid tidak punya roda, jadi belok dilakukan dengan memutar pinggul sedikit di setiap langkah, dan '
    'paling banyak hanya 17 derajat setiap dua langkah.',
    'Ketiga, <b>berhenti</b>: humanoid tidak bisa berhenti mendadak. Robot beroda bisa direm kapan saja, sedangkan humanoid harus '
    'menyelesaikan langkahnya dulu supaya tetap seimbang. Keputusan baru bisa diambil di akhir siklus, '
    'sehingga ambang jarak amannya harus lebih jauh, yaitu 0,85 m untuk lanjut berjalan. Keempat, '
    '<b>lengan</b>: lengan ikut berayun, dan saat berputar di tempat, lengan sempat menyenggol dinding. Karena itu koridor '
    'dibuat selebar 0,5 m dan putar di tempat hanya boleh bila semua sisi lega minimal 0,33 m.'],
    teknis=['Total 25 DOF termasuk sendi tangan/jari; 24 sudut sendi dipublikasikan ke /joint_states.',
            'HipYawPitch kiri dan kanan pada NAO sebenarnya satu motor yang terkopel; sendi inilah yang '
            'dipakai untuk membelokkan langkah.',
            'Lidar dipasang di headSlot pada z = 0,085 m dari kepala, sehingga tingginya ±0,57 m dari lantai.'])

slide(6, 'Sensor', '±1 menit', [
    'Sensor utamanya Lidar 360 derajat: 360 sinar, jangkauan 6 cm sampai 4 m, di ketinggian 0,57 m. '
    'Karena di atas kepala, pandangannya tidak terhalang badan sendiri. Sonar di dada dipakai sebagai '
    'konfirmasi untuk obstacle yang sangat dekat. IMU, gyro, dan accelerometer memberi arah hadap dan '
    'mendeteksi jatuh, yaitu bila roll atau pitch melebihi 45 derajat. GPS dipakai untuk mencatat sel '
    'arena yang sudah dikunjungi. Sensor gaya di telapak kaki menunjukkan kaki mana yang sedang menumpu. '
    'Kamera dan sensor sendi dikirim ke RViz2.'],
    rumus=[f'Sudut sinar ke-{m("i")}:  {m("θ")}<sub>{m("i")}</sub> = π − {m("i")} · 2π / {m("N")},   '
           f'{m("N")} = 360  (indeks 0 = belakang, berurutan searah jarum jam)'],
    teknis=['IMU bawaan NAO tidak punya sumbu yaw, jadi saya menambah InertialUnit “imu_body” di bodySlot.',
            'Accelerometer NAO terpasang terbalik 180° di sumbu x, sehingga tanda y dan z dibalik '
            '(sebelumnya terbaca −9,9 m/s² saat berdiri).',
            'Alarm sonar (&lt; 0,30 m) hanya dihitung jika Lidar sektor depan juga &lt; 0,6 m; sonar NAO '
            'sering memberi alarm palsu karena pancarannya lebar.',
            'Penghindaran obstacle murni dari Lidar + sonar. GPS hanya untuk memori eksplorasi dan odometri '
            'RViz; ketentuan tugas membebaskan pilihan sensor.'])

# ---------------------------------------------------------------- 7–11 gait
slide(7, 'Bagian 02: Gait Engine', '±10 dtk', [
    'Bagian kedua: bagaimana membuat setiap sendi bergerak dengan benar sehingga robot bisa berjalan.'])

slide(8, 'Masalah pertama: robot jatuh', '±1 menit', [
    'Masalah pertama yang saya temui: dengan motion bawaan Webots, robot langsung jatuh. File Forwards50 '
    'langsung melompat ke pose lutut ditekuk 1,22 radian, padahal robot sedang berdiri tegak. Lompatan '
    'pose ini membuat robot jatuh di detik 1,2 dengan pitch badan 68 derajat. Ini terukur di simulasi.',
    'Solusinya adalah transisi halus. Sebelum gerakan baru dimulai, setiap sendi dipindahkan dari pose '
    'sekarang ke pose awal gerakan selama 0,4 detik memakai fungsi smoothstep:'],
    rumus=[f'{m("s")}({m("u")}) = 3{m("u")}² − 2{m("u")}³,     {m("u")} = {m("t")} / 0,4 s',
           f'{m("q")}({m("t")}) = {m("q")}<sub>awal</sub> + ({m("q")}<sub>1</sub> − {m("q")}<sub>awal</sub>) · {m("s")}({m("u")})'],
    transisi='Turunan smoothstep, 6u − 6u², bernilai nol di u = 0 dan u = 1. Artinya kecepatan sendi nol di '
             'awal dan akhir transisi, jadi tidak ada sentakan. Hasilnya semua gerakan berjalan tanpa jatuh.',
    teknis=['File .motion berisi keyframe setiap 40 ms. Gait engine menginterpolasi linear di antara keyframe '
            'dan memanggil setPosition untuk semua motor setiap step simulasi.',
            'Motion.play() bawaan juga bermasalah bila diputar berulang (macet dan timing tidak pasti), '
            'sehingga saya menulis pemutar Clip sendiri di gait.py.',
            'Klip yang berantai (jalan_lurus → jalan_kiri → jalan_berhenti) memakai blend 0 supaya langkah '
            'tidak patah; smoothstep hanya dipakai saat berpindah ke jenis gerakan lain.'])

slide(9, 'Jalan terus dan belok sambil jalan', '±1 menit', [
    'Agar bisa jalan terus, saya memeriksa file Forwards50 dan menemukan bahwa frame 51 dan frame 102 '
    'identik, selisihnya nol radian. Jadi potongan frame 51 sampai 102 bisa diulang tanpa sambungan. '
    'Satu siklus berisi dua langkah, durasinya 2,04 detik, dan maju 0,18 meter.',
    'Untuk belok sambil jalan, caranya mirip saat kita berbelok: kaki diputar ke arah belokan sebelum '
    'menapak. Di NAO, sendi putar pinggul yang bernama HipYawPitch saya putar sedikit, 0,25 radian atau '
    'sekitar 14 derajat, saat kaki sedang terangkat. Saat kaki menapak, pinggul dikembalikan lurus. Jadi '
    'kaki mendarat sudah menghadap arah baru, dan badan ikut berbelok. Hasilnya 17 derajat ke kiri atau 13 '
    'derajat ke kanan setiap dua langkah. Saya juga mencoba memutar pinggul lebih besar, 0,4 sampai 0,5 '
    'radian, tetapi kaki malah tergelincir, jadi dipilih 0,25.'],
    rumus=['siklus = frame 51–102 dari Forwards50  →  2 langkah, 51 × 40 ms = 2,04 s, +0,18 m'],
    teknis=['Klip mulai jalan: frame 0–51; klip berhenti: frame 102–170.',
            'Waktu putaran pinggul: belok kiri diputar di frame 7–20 dan dikembalikan di 20–33; belok kanan '
            'diputar di frame 20–33 dan dikembalikan di 33–46 (dihitung dari awal siklus). Angka 17° dan 13° '
            'adalah hasil ukur di simulasi; kiri dan kanan tidak sama karena langkah kaki kiri dan kanan '
            'di file motion tidak persis simetris.',
            'Saya sempat mencoba menskalakan panjang langkah kiri/kanan (seperti differential drive), tetapi '
            'robot hampir tidak berbelok. Karena itu dipakai putaran pinggul.'])

slide(10, 'Gerakan yang tersedia', '±40 dtk', [
    'Hasilnya, ada satu set gerakan primitif yang semuanya terukur. Jalan lurus 2,04 detik untuk 18 cm. '
    'Jalan belok maju 16 cm sambil berbelok 17 atau 13 derajat. Putar di tempat 10, 20, 40, dan 60 '
    'derajat. Putar balik 196 derajat dalam 9 detik. Ada juga mundur dan maju kecil 10 cm. Putar 10 dan '
    '20 derajat saya buat sendiri dengan menskalakan HipYawPitch dari gerakan putar 40 derajat dengan '
    'faktor 0,25 dan 0,5.'],
    teknis=['Putar 10°/20° ditambahkan karena putar 40° sering kebablasan untuk koreksi kecil sehingga robot '
            'putar bolak-balik.',
            'putar_balik memakai TurnLeft180 bawaan; mundur dan maju_kecil untuk keluar dari posisi terlalu dekat.',
            'Ada juga gerakan “bangun” (StandUpFromFront) yang dipicu watchdog bila robot jatuh; dalam uji '
            'akhir gerakan ini tidak pernah terpakai karena tidak ada kejadian jatuh.'])

slide(11, 'Arena 5 × 5 m', '±40 dtk', [
    'Ini arena ujinya dari atas. Ada 12 obstacle setinggi 0,8 meter. Tingginya sengaja melebihi posisi '
    'Lidar di 0,57 meter supaya bisa terlihat. Bentuknya beragam: kotak, kotak miring, tabung, dinding '
    'panjang, dan siku-L. Siku-L membentuk sudut cekung yang bisa menjebak robot. Beberapa celah juga '
    'sengaja dibuat terlalu sempit untuk humanoid. Tujuannya menguji kasus sulit, bukan hanya mengikuti '
    'dinding arena.'],
    teknis=['World dibuat oleh tools/make_world.py (tidak diedit manual), dinding arena 0,8 m.',
            'Nama obstacle: kotak_1, dinding_miring, tabung_1, tabung_2, dinding_tengah, kotak_berlian, '
            'tabung_besar, dinding_utara, tiang, kotak_2, siku_L_a, siku_L_b.',
            'Posisi awal default (−2, −2) menghadap 45°. Uji memakai 16 posisi awal berbeda.'])

# ---------------------------------------------------------------- 12–15 navigasi
slide(12, 'Bagian 03: Navigasi', '±10 dtk', [
    'Bagian ketiga adalah navigasi: bagaimana robot memilih arah dengan koridor Lidar dan eksplorasi '
    'kebaruan.'])

slide(13, 'Pilih arah: cek koridor', '±1 menit', [
    'Robot mengevaluasi 36 kandidat arah, setiap 10 derajat. Untuk setiap arah θ, semua titik Lidar '
    'diproyeksikan ke sumbu arah itu. ℓ adalah jarak di sepanjang arah, d adalah jarak menyamping. '
    'Jarak bebas arah θ adalah titik terdekat di depan yang jatuh di dalam koridor selebar 0,5 meter.'],
    rumus=[f'{m("ℓ")} = {m("x")} cos {m("θ")} + {m("y")} sin {m("θ")}        '
           f'{m("d")} = −{m("x")} sin {m("θ")} + {m("y")} cos {m("θ")}',
           f'bebas({m("θ")}) = min {{ {m("ℓ")} : {m("ℓ")} &gt; 0, |{m("d")}| &lt; 0,25 m }}   (maksimal 3,5 m)'],
    transisi='Kenapa koridor dan bukan satu sinar? Satu sinar bisa lolos lewat celah kecil yang tidak muat '
             'badan. Koridor selebar badan humanoid (2 × 0,25 m) membuat celah sempit otomatis tidak dipilih.',
    teknis=['Titik (x, y) dihitung dari jarak sinar r: x = r cos θᵢ, y = r sin θᵢ di frame robot.',
            'HALF_W = 0,25 m: bahu + lengan NAO ±0,16 m ditambah margin untuk ayunan badan.',
            'FREE_CAP = 3,5 m membatasi perhitungan; jangkauan Lidar sendiri 4 m.'])

slide(14, 'Skor arah dan kebaruan', '±1,5 menit', [
    'Setiap arah diberi skor dari empat suku. Suku pertama menyukai jalan lapang, sampai 2 meter. Suku '
    'kedua adalah <b>kebaruan K</b>, yaitu rata-rata 1/(1+n) dari sel-sel 0,25 m di arah itu, dengan n '
    'adalah jumlah kunjungan. Area yang belum pernah didatangi bernilai 1, dan semakin sering dikunjungi '
    'nilainya semakin kecil. Suku ketiga adalah penalti belok karena humanoid lambat berbelok. Suku '
    'keempat adalah persistensi, yaitu penalti bila berbeda jauh dengan arah tujuan sebelumnya, supaya '
    'robot tidak bolak-balik.',
    'Arah yang jarak bebasnya di bawah 0,85 m tidak dipertimbangkan sama sekali. Sebagai pembanding, '
    'mode acak mengganti suku kebaruan dengan arah acak yang diundi ulang setiap 20 detik.'],
    rumus=[f'skor({m("θ")}) = min(bebas, 2)/2 + 0,6·{m("K")}({m("θ")}) − 0,35·|{m("θ")}|/π '
           f'− 0,25·|wrap({m("ψ")} + {m("θ")} − {m("ψ")}<sub>tujuan</sub>)|/π',
           f'{m("K")}({m("θ")}) = rata-rata 1/(1 + {m("n")}<sub>sel</sub>) di sepanjang {m("θ")}, '
           f'dari 0,5 m sampai min(bebas, 2,5 m)'],
    teknis=['ψ = yaw robot dari IMU; ψ_tujuan = arah tujuan sebelumnya dalam frame dunia; wrap() membungkus '
            'sudut ke (−π, π].',
            'Jumlah kunjungan sel dicatat dari GPS setiap 0,5 s.',
            'Mode acak: suku kebaruan diganti −0,3·|wrap(ψ+θ−ψ_wander)|/π, ψ_wander diacak tiap 20 s.',
            'Bobot dapat diubah lewat variabel lingkungan OA_W_NOV, OA_K_TURN, OA_K_KEEP, OA_NOV_RANGE '
            '(default 0,6 / 0,35 / 0,25 / 2,5).'])

slide(15, 'State machine dan keselamatan', '±1 menit', [
    'Pilihan arah lalu dijalankan oleh state machine ini. Pusatnya adalah <b>SIAP</b>, yaitu saat robot '
    'berdiri dan Lidar memilih arah. Dari SIAP ada tiga kemungkinan. Kalau arah terbaik ada di depan, '
    'paling jauh 35 derajat, dan depan lega minimal 0,6 m, robot masuk <b>JALAN</b>. Kalau arahnya ke '
    'samping atau ke belakang, robot <b>PUTAR</b> di tempat, tetapi hanya jika semua sisi lega minimal 0,33 m '
    'karena lengan ikut berayun. Kalau obstacle kurang dari 0,3 m di depan, atau tidak ada ruang untuk '
    'berputar, robot <b>MUNDUR</b> atau maju sedikit dulu. Setelah putar atau mundur selesai, robot kembali '
    'ke SIAP dan memilih lagi.',
    'Saat JALAN, robot memeriksa koridor di setiap akhir siklus. Kalau koridor masih minimal 0,85 m, '
    'robot melanjutkan satu siklus lagi, bisa lurus, belok kiri, atau belok kanan. Kalau koridor kurang '
    'dari 0,85 m, belokan yang dibutuhkan lebih dari 75 derajat, atau sonar dan Lidar sama-sama melihat '
    'obstacle dekat, robot masuk <b>BERHENTI</b>: ia menyelesaikan langkahnya dulu supaya tetap seimbang, '
    'baru kembali ke SIAP. Kalau robot jatuh dari state mana pun, ia masuk <b>BANGUN</b>. Di bawah diagram '
    'ada dua watchdog: kalau robot macet 30 detik ia putar 60 derajat, dan kalau 60 detik tetap di radius '
    '0,5 m ia masuk mode lolos selama 25 detik.',
    'Semua ambang ini hasil tuning dari kasus tabrakan nyata di data uji, bukan tebakan.'],
    teknis=['Saat berbelok sambil jalan, koridor lurus ke depan juga harus ≥ 0,70 m.',
            'Mulai jalan juga boleh bila depan ≥ 0,45 m asalkan kedua sisi (30–120°) ≥ 0,35 m.',
            'Belok sambil jalan diizinkan sampai ±75°, deadband 7°. Di luar itu robot berhenti lalu putar di tempat.',
            'Mundur jika sektor depan (±50°) &lt; 0,30 m dan belakang ≥ 0,45 m; bila putar tidak aman, robot '
            'mundur atau maju kecil dulu.',
            'Turn-lock: arah putar dikunci hanya bila tujuan ada di belakang (|θ| &gt; 90°), mencegah kiri-kanan di sudut.',
            'Watchdog macet: bergerak &lt; 0,15 m dalam 30 s → putar 60°. Mode lolos: 25 s menuju arah dengan '
            'jarak bebas terbesar (minimal 1,2 m). Jatuh: |roll| atau |pitch| &gt; 45° → bangun.'])

# ---------------------------------------------------------------- 16–22 hasil
slide(16, 'Bagian 04: Pengujian', '±10 dtk', [
    'Bagian terakhir adalah pengujian: {runs} uji masing-masing 10 menit, semuanya dinilai otomatis.'])

slide(17, 'Cara mengukur', '±1 menit', [
    'Penilaian dilakukan oleh robot evaluator, yaitu Supervisor Webots yang hanya mengamati dan tidak '
    'membantu robot. Tabrakan dihitung dari kontak fisik robot di atas 3 cm, sehingga telapak kaki yang '
    'menapak lantai tidak dihitung. Jatuh dihitung bila torso turun di bawah 0,22 m. Coverage adalah '
    'persentase sel bebas 20 cm yang pernah dilewati.',
    'Detektornya saya validasi dulu memakai humanoid “buta” yang hanya berjalan lurus. Robot itu langsung '
    'tercatat menabrak dan jatuh di dinding miring. Jadi kalau hasilnya 0, memang tidak ada tabrakan. '
    'Matriks ujinya 16 posisi awal × 2 mode × 10 menit.'],
    rumus=[f'coverage = |sel dikunjungi ∩ sel bebas| / |sel bebas| × 100 %,   sel bebas = sel 0,2 m dengan clearance &gt; {m("r")} = 0,18 m'],
    teknis=['Uji berjalan headless: webots --batch --mode=fast --minimize --no-rendering lewat '
            'tools/stress_test.sh (8 posisi awal per set, set 1 dan set 2).',
            'Evaluator juga mencatat clearance minimum, CSV trajektori (termasuk z), screenshot, dan ringkasan tiap 10 s.',
            'Jarak tempuh dihitung dari posisi yang disampel setiap 1 s supaya goyangan badan tidak ikut terhitung.'])

slide(18, 'Hasil uji', '±40 dtk', [
    'Hasilnya: {col} tabrakan dan {fall} kali jatuh selama {hours} jam simulasi dari {runs} uji, dengan '
    'total jarak berjalan {dist_km} km. Coverage mode acak rata-rata {cov_a} %, sedangkan mode kebaruan '
    '{cov_n} %. Artinya coverage naik {up} %.'],
    teknis=['Mode kebaruan: rata-rata {cov_n} % (rentang {nmin}–{nmax} %), jarak {dn} m, clearance minimum {cln} cm.',
            'Mode acak: rata-rata {cov_a} % (rentang {amin}–{amax} %), jarak {da} m, clearance minimum {cla} cm.',
            'Peningkatan {up} % adalah relatif: ({cov_n} − {cov_a}) / {cov_a}. Selisih absolutnya ±12,6 poin persen.',
            'Clearance = jarak analitik pusat robot ke permukaan obstacle/dinding dikurangi radius pembungkus '
            '0,18 m. Nilai beberapa cm berarti dekat; kontak fisik tetap 0.'])

slide(19, 'Kebaruan vs acak', '±30 dtk', [
    'Ini lintasan 8 uji dari posisi awal yang sama untuk kedua mode. Terlihat mode kebaruan masuk ke lebih '
    'banyak celah dan menyebar ke seluruh arena, sedangkan mode acak cenderung berputar di area yang sama.'])

slide(20, 'Coverage naik', '±30 dtk', [
    'Rata-rata dari {per_mode} uji per mode, coverage naik {up} %. Perbandingannya adil: setiap uji memakai '
    'posisi awal yang sama untuk kedua mode, dan aturan keselamatannya sama persis. Satu-satunya yang '
    'berbeda adalah cara memilih arah.'],
    teknis=['Coverage terendah mode kebaruan {nmin} % (set 2, posisi awal ke-3); ini kasus yang ingin saya '
            'perbaiki berikutnya.'])

slide(21, 'Masalah yang ditemukan dari data', '±1,5 menit', [
    'Hasil 0 tabrakan ini tidak langsung didapat. Saya menjalankan uji berulang, membaca datanya, dan '
    'memperbaiki masalah satu per satu. Lengan menyenggol dinding saat berputar, jadi saya menambah syarat '
    'ruang putar 0,33 m dan memilih sisi yang lebih lega. Robot pernah putar kiri-kanan di sudut selama 9 '
    'menit karena target di belakang berpindah sisi, jadi arah putarnya saya kunci. Putar 40 derajat sering '
    'kebablasan, jadi saya tambah putar 20 dan 10 derajat. Ada senggolan saat mulai jalan, jadi syarat '
    'mulai jalan diperketat. Sonar melihat tiang di samping dan membuat robot maju-mundur, jadi sonar '
    'harus dikonfirmasi Lidar. Robot terjebak di kantong sempit, jadi saya tambah watchdog wilayah dan '
    'mode lolos. Terakhir, 43 % waktu habis untuk berputar karena robot hanya bisa belok saat diam, '
    'sehingga saya menambah belok sambil jalan sampai 75 derajat.'],
    teknis=['Setiap perbaikan diikuti stress test ulang; angka akhir di slide berasal dari kode yang sama '
            'dengan yang ada di repo.',
            'Masalah perangkat lunak lain: bridge ROS sempat segfault karena TouchSensor.getValues() '
            'mengembalikan pointer ctypes (solusi: ambil indeks 0..2, jangan list()); RViz2 crash di Wayland '
            '(solusi: QT_QPA_PLATFORM=xcb).'])

slide(22, 'Semua sensor di RViz2', '±1 menit', [
    'Semua sensor dipublikasikan ke ROS 2 dan ditampilkan di RViz2: /scan untuk Lidar 360 derajat, dua '
    'sonar, IMU dengan orientasi, gyro, dan accelerometer, gaya telapak kaki kiri dan kanan, kamera NAO, '
    'joint_states bersama URDF sehingga model humanoid bergerak sesuai sendinya, serta odometri dan marker '
    'keputusan berisi koridor, panah arah, state, dan sel yang sudah dikunjungi. Semuanya dijalankan '
    'dengan satu perintah, tools/rviz.sh.'],
    teknis=['Bridge publish setiap 2 step (±25 Hz); kamera setiap publish ke-5 (±5 Hz, bgra8).',
            '/scan: urutan sinar Webots dibalik agar sesuai konvensi ROS (berlawanan jarum jam), '
            'angle_min = −π + step. LaserScan ditampilkan bersama jejak 60 s.',
            '/fsr/left dan /fsr/right bertipe WrenchStamped; saat berdiri terbaca ±50 N per kaki.',
            'URDF berasal dari ekspor Webots getUrdf (hanya kaki, karena ekspor belum mendukung Hinge2Joint) '
            'yang dilengkapi lengan, kepala, lidar, dan kamera oleh tools/make_urdf.py.',
            'TF odom → base_link dari GPS + yaw IMU; robot_state_publisher menghitung TF tiap link dari /joint_states.'])

# ---------------------------------------------------------------- 23–25
slide(23, 'Demo', '2–3 menit', [
    'Sekarang demonya. (Pindah ke Webots, tekan Play.) Robot NAO mulai dari pojok kiri bawah dan berjalan '
    'menjelajah. Di console terlihat state-nya: JALAN_KIRI, PUTAR, dan seterusnya, dan setiap 10 detik '
    'evaluator mencetak jumlah tabrakan, jatuh, dan coverage. (Pindah ke RViz2.) Di sini titik merah adalah '
    'scan Lidar, koridor dan panah menunjukkan arah yang dipilih, dan model robot ikut bergerak sesuai '
    'sendinya. Kode, laporan PDF, dan slide ada di GitHub.'],
    teknis=['Tips demo: aktifkan View → Optional Rendering → Show Lidar Point Cloud; klik dua kali robot agar '
            'kamera mengikutinya; tombol ⏩ untuk mempercepat; Ctrl+Shift+T untuk reset.',
            'Cadangan bila ROS gagal: buka worlds/obstacle_avoidance.wbt langsung di Webots (controller tetap '
            'jalan tanpa ROS).'])

slide(24, 'Kesimpulan', '±45 dtk', [
    'Kesimpulannya ada empat. Satu, humanoid 25 sendi berjalan stabil dengan gait engine sendiri: transisi '
    'halus, siklus jalan kontinu, dan belok sambil jalan. Dua, Lidar 360 derajat di kepala dengan koridor '
    'selebar badan menghasilkan {col} tabrakan dan {fall} kali jatuh dalam {hours} jam uji. Tiga, eksplorasi '
    'kebaruan menaikkan coverage dari {cov_a} % menjadi {cov_n} %, naik {up} %. Empat, semua sensor dan '
    'model robot bisa dipantau di RViz2.',
    'Untuk pengembangan berikutnya: lokalisasi tanpa GPS dengan SLAM, gait dengan umpan balik '
    'keseimbangan, dan obstacle yang bergerak.'])

slide(25, 'Terima kasih / Q&amp;A', '—', [
    'Sekian presentasi dari saya. Terima kasih, saya persilakan jika ada pertanyaan.'])

# ---------------------------------------------------------------- Q&A
story.append(PageBreak())
story.append(Paragraph('Persiapan tanya jawab', h1))
qa = [
    ('Kenapa memakai GPS? Bukankah itu curang?',
     'Ketentuan tugas membebaskan sensor. GPS hanya dipakai untuk memori eksplorasi (sel yang sudah '
     'dikunjungi) dan odometri di RViz. Keputusan menghindari obstacle 100 % dari Lidar dan sonar. Kalau GPS '
     'dimatikan, robot tetap tidak menabrak; yang hilang hanya peningkatan coverage. Pengembangan berikutnya '
     'adalah menggantinya dengan SLAM atau odometri Lidar.'),
    ('Model robot NAO ini dari mana? Buatan sendiri?',
     'Model fisik NAO saya ambil dari library bawaan Webots. NAO aslinya adalah robot humanoid sungguhan buatan '
     'Aldebaran (Prancis) yang kemudian dimiliki SoftBank Robotics, tinggi ±57 cm, dan banyak dipakai untuk riset '
     'dan RoboCup. Model simulasinya (badan 3D, engsel, motor, sensor) dibuat oleh Cyberbotics, pengembang Webots. '
     'World saya memanggilnya langsung dari repositori resmi Webots lewat baris EXTERNPROTO …/softbank/nao/protos/'
     'Nao.proto, lalu saya tambahkan Lidar di headSlot dan IMU di bodySlot. File gerakan .motion juga dari contoh '
     'Webots dengan lisensi Apache 2.0, jadi boleh dipakai dan dimodifikasi. Yang saya kerjakan sendiri adalah '
     'semua yang membuatnya hidup: gait engine yang menggerakkan 22 sendi, navigasi Lidar, state machine, watchdog, '
     'evaluator, ROS 2 bridge, URDF untuk RViz2, dan generator arena. Memakai model robot yang sudah ada lalu fokus '
     'pada kendali dan navigasi adalah praktik umum di robotika, dan ketentuan tugas membebaskan bentuk robot. '
     'Versi pertama proyek ini adalah robot beroda yang saya rakit sendiri dari Box, HingeJoint, dan BallJoint.'),
    ('Bagaimana engsel per engselnya dibuat?',
     'Di dalam model NAO, setiap sendi adalah sebuah HingeJoint (engsel dengan sumbu putar dan titik tumpu) yang '
     'berisi RotationalMotor sebagai penggerak dan PositionSensor untuk membaca sudutnya, misalnya motor '
     '“LKneePitch” dan sensor “LKneePitchS”. Ujung engsel menempel ke bagian badan berikutnya, dan di bagian itu '
     'menempel engsel berikutnya. Jadi engselnya berantai seperti pohon: torso → pinggul → paha → lutut → tulang '
     'kering → pergelangan → telapak kaki. Kalau pinggul berputar, seluruh kaki di bawahnya ikut berputar.'),
    ('Bagaimana cara menggerakkan setiap engsel?',
     'Lewat gait engine yang saya tulis di gait.py. Pertama, motor dan sensor ke-22 sendi diambil dengan '
     'robot.getDevice(nama). Robot dimulai dari pose siap: lutut ditekuk 1,047 rad, pinggul dan pergelangan '
     '−0,524 rad, supaya pusat massanya rendah. Sudut-sudut gerakan dibaca dari file .motion yang berisi sudut '
     'semua sendi setiap 40 ms. File itu saya baca sendiri, sudut di antara keyframe diinterpolasi untuk setiap '
     'step, perpindahan antargerakan diberi transisi halus 0,4 s, siklus jalan dipotong supaya bisa diulang, dan '
     'pinggul diputar sedikit untuk berbelok. Setiap step, sudut target dikirim ke motor dengan setPosition(). '
     'Motor Webots punya pengendali posisi internal yang memutar engsel ke sudut itu, dan mesin fisika menghitung '
     'gaya, gesekan kaki dengan lantai, dan keseimbangan badan.'),
    ('Bagaimana semua bagiannya terhubung?',
     'Setiap step simulasi, controller membaca Lidar, sonar, IMU, dan GPS. Fungsi decide() memilih arah dengan '
     'koridor dan kebaruan, lalu memilih state (JALAN, PUTAR, MUNDUR, dan seterusnya). State itu memilih klip '
     'gerakan di gait engine, gait engine menghitung sudut 22 sendi, motor menggerakkan engsel, dan fisika Webots '
     'membuat robot berpindah. Sensor lalu terbaca lagi di step berikutnya. Keputusan baru hanya diambil setelah '
     'satu klip selesai, supaya langkah tidak terputus di tengah. Kalau IMU membaca roll atau pitch lebih dari 45°, '
     'robot langsung masuk gerakan bangun. Di saat yang sama, ROS 2 bridge mengirim semua sensor ke RViz2. Sudut '
     'sendi dikirim lewat /joint_states, lalu robot_state_publisher menggabungkannya dengan URDF (deskripsi engsel '
     'yang sama dalam format ROS) sehingga model NAO di RViz2 bergerak persis seperti di Webots.'),
    ('Kenapa tidak pakai motion bawaan saja?',
     'Motion bawaan langsung melompat ke pose awal sehingga robot jatuh di detik 1,2 (pitch 68°). Motion.play() '
     'yang diulang juga macet dan timing-nya tidak pasti. Karena itu saya membuat pemutar keyframe sendiri '
     'dengan transisi smoothstep.'),
    ('Bagaimana robot berbelok kalau tidak punya roda?',
     'Seperti manusia: pinggul (sendi HipYawPitch) diputar sedikit, 0,25 rad atau ±14°, saat kaki terangkat, '
     'lalu dikembalikan saat kaki menapak, sehingga kaki mendarat menghadap arah baru. Hasilnya +17° ke kiri '
     'atau −13° ke kanan setiap dua langkah. Untuk sudut besar robot berhenti lalu memutar di '
     'tempat 10°, 20°, 40°, 60°, atau 196°.'),
    ('Apa arti peningkatan {up} %?'.format(**V),
     'Coverage rata-rata naik dari {cov_a} % ke {cov_n} %, dihitung relatif: ({cov_n} − {cov_a}) / {cov_a} ≈ '
     '{up} %. Kedua mode diuji dari 16 posisi awal yang sama, dengan aturan keselamatan yang sama.'.format(**V)),
    ('Kenapa coverage tidak mendekati 100 %?',
     'Humanoid lambat, sekitar 9 cm/s. Dalam 10 menit robot hanya berjalan ±43 m. Sebagian sel juga tidak '
     'mungkin dimasuki: ditempati obstacle, celah yang lebih sempit dari badan, dan pojok yang tidak aman '
     'untuk berputar. Coverage dihitung terhadap sel bebas, yaitu sel yang pusatnya berjarak lebih dari 0,18 m '
     'dari obstacle, tetapi banyak sel bebas berada di celah yang tetap tidak aman bagi humanoid.'),
    ('Bagaimana memastikan 0 tabrakan itu benar?',
     'Evaluator adalah Supervisor terpisah yang membaca titik kontak fisik dari mesin fisika. Detektornya '
     'divalidasi dengan humanoid “buta”, yang langsung tercatat menabrak dan jatuh. Selain itu {runs} uji '
     'dari 16 posisi awal berbeda, total {hours} jam.'.format(**V)),
    ('Kenapa koridor 0,5 m dan ambang 0,85 m?',
     'Bahu dan lengan NAO selebar ±0,32 m, ditambah margin ayunan badan, sehingga setengah lebar koridor '
     '0,25 m. 0,85 m kira-kira jarak yang dibutuhkan satu siklus jalan (0,18 m) ditambah jarak berhenti dan '
     'margin. Semua ambang dituning dari kasus tabrakan nyata di data uji.'),
    ('Apa kelemahan sistem ini?',
     'Bergantung pada GPS untuk memori eksplorasi, gait open-loop (tanpa umpan balik keseimbangan aktif), '
     'obstacle statis saja, dan coverage terendah masih {nmin} % pada satu posisi awal.'.format(**V)),
]
for q, a in qa:
    story.append(KeepTogether([Paragraph(f'<b>T:</b> {q}', body), Paragraph(f'<b>J:</b> {a}', small),
                               Spacer(1, 6)]))

story.append(Paragraph('Angka penting (hafalkan)', h2))
table([['Besaran', 'Nilai'],
       ['Lidar', '360 sinar, 0,06–4 m, tinggi 0,57 m'],
       ['Siklus jalan', '2 langkah, 2,04 s, +0,18 m'],
       ['Belok sambil jalan', 'putar pinggul 0,25 rad (±14°) saat kaki terangkat → +17° / −13° per 2 langkah'],
       ['Transisi', 'smoothstep 3u² − 2u³ selama 0,4 s'],
       ['Koridor', 'lebar 0,5 m (HALF_W 0,25), 36 arah tiap 10°'],
       ['Ambang', 'lanjut 0,85 · mulai 0,60 · putar 0,33 · mundur 0,30 m'],
       ['Pengujian', '{runs} uji × 10 menit = {hours} jam, {dist_km} km'.format(**V)],
       ['Hasil', '{col} tabrakan, {fall} jatuh, coverage {cov_a} % → {cov_n} % (+{up} %)'.format(**V)]],
      [W * 0.3, W * 0.7])


def on_page(c, doc):
    if doc.page == 1:
        return
    c.saveState()
    c.setFont('DV', 8)
    c.setFillColor(GREY)
    c.drawString(2 * cm, 1.2 * cm, 'Naskah Presentasi · Robot Humanoid Obstacle Avoidance')
    c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, str(doc.page))
    c.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                        bottomMargin=1.8 * cm, title='Naskah Presentasi Obstacle Avoidance B401',
                        author='Ahnaf Al Ghiffarri Ahtasyafi')
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
for f in THUMBS:
    os.remove(f)
os.rmdir(tmp)
print('OK', OUT)
