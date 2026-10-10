# IoTong — cara pakai dari zip Metland

Folder `Metland` di-zip, lalu dibuka di laptop lain. Nomor kamera dan nomor COM **tidak sama** dengan laptop asal. Jangan menyalin angka COM3 atau index 1 mentah-mentah.


| Item | Nilai |
|------|--------|
| Isi yang dijalankan | folder `Metland` setelah di-extract |
| Python | **3.11**, 64-bit, Windows |
| Pratinjau | http://127.0.0.1:43123 di laptop yang menjalankan skrip |
| Model bawaan | `yolo11n.pt` di akar folder Metland |
| Servo | ESP32, serial **115200**. Perintah `sort <derajat>` |
| Servo 1, tutup jatuh | kabel sinyal ke pin **D18**. Tertutup 180°, terbuka 0° |
| Servo 2, tong | kabel sinyal ke pin **D19**. B3 0°, Organik 120°, Anorganik 240° |
| Daya motor | kabel merah kedua servo ke **adaptor 5 V 2 A** |


---

## 1. Isi zip

Ikutkan:

- `scripts\`
- `devnote\`
- `requirements.txt`
- `yolo11n.pt`
- `dataset\` dan `runs\` kalau model sampah terlatih mau ikut

Jangan ikutkan:

- `.venv\` — ini milik laptop asal, besar, dan tidak jalan di laptop lain. Dibuat ulang di laptop tujuan.

---

## 2. Setup sekali di laptop lain

1. Pasang Python 3.11 dari python.org. Centang **Add python.exe to PATH**.
2. Extract zip. Misal hasilnya `D:\Metland`.
3. PowerShell:

```powershell
cd D:\Metland
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Unduhan pertama agak lama karena PyTorch ikut terpasang.

4. Colok webcam dan ESP32. Cari nomor kamera:

```powershell
.\.venv\Scripts\python.exe -c "import cv2
for i in range(4):
 c=cv2.VideoCapture(i, cv2.CAP_DSHOW); print(i, c.isOpened()); c.release()"
```

Angka yang `True` dan gambarnya webcam yang dipakai dicatat sebagai `--camera`.

5. Cari port ESP di Device Manager → **Ports (COM & LPT)**. Nama yang ada tulisan **USB-SERIAL CH340** adalah ESP. Contoh `COM9`. Itu nilai `--port`.

---

## 3. Menjalankan

Ganti `1` dan `COM9` dengan angka laptop itu.

```powershell
cd D:\Metland
$env:PYTHONUNBUFFERED = "1"
# Mode Native OpenCV (Default, 30 FPS, Latensi <5ms):
.\.venv\Scripts\python.exe scripts\live_webcam.py --camera 0 --model yolo11n.pt --conf 0.25 --servo-conf 0.50 --cooldown 8 --port COM9

# Mode Dual (Native + Pratinjau Web di http://127.0.0.1:43123):
.\.venv\Scripts\python.exe scripts\live_webcam.py --camera 0 --model yolo11n.pt --conf 0.25 --servo-conf 0.50 --cooldown 8 --port COM9 --web
```

Jendela OpenCV muncul di layar dengan FPS counter dan status servo. Tunjukkan sampah ke tengah kamera.
Tekan **Q** atau **ESC** pada jendela kamera untuk berhenti.
Tanpa `--port`, kamera tetap jalan, servo berjalan simulasi di terminal.

Berhenti dengan `Ctrl+C`. Jangan jalankan skrip ini dua kali bersamaan.

### Urutan, sama seperti tong yang muter dulu baru sampah jatuh

1. Kamera menentukan B3, Organik, atau Anorganik.
2. Servo 2 memutar tong ke sektor kelas itu dan berhenti.
3. Tunggu 2 detik.
4. Servo 1 membuka, sampah jatuh, lalu menutup.
5. Tong tetap di sektor itu sampai kelas berikutnya.

| Kelas | Sudut servo 2 |
|-------|----------------|
| B3 | 0° |
| Organik | 120° |
| Anorganik | 240° |

Servo baru gerak kalau confidence minimal 0,50 dan kelasnya sama selama 3 frame. Benda yang tidak dikenal tidak menggerakkan servo.

---

## 4. Kabel, sama di laptop mana pun

- Servo 1, kabel kuning/oranye → ESP32 pin **D18**
- Servo 2, kabel kuning/oranye → ESP32 pin **D19**, di sebelah D18
- Kedua kabel merah → **5 V adaptor 2 A**, bukan pin 5 V ESP
- Kedua kabel hitam/coklat, GND adaptor, dan GND ESP disatukan

Sinyal ESP 3,3 V. Itu hanya perintah. Tenaga motor ada di kabel merah. Pin 5 V dari USB tidak kuat untuk dua servo: tegangan jatuh, ESP reset, gerakan meleset.

---

## 5. Laptop asal, catatan

Di laptop pembuat zip, ESP sempat pindah dari COM3 ke **COM9** (tetap CH340). Perintahnya `--port COM9`. Kalau dicabut lalu colok lagi, cek Device Manager lagi. Nomor COM bisa berubah.

Firmware yang ada di ESP sudah urutan di bagian 3: servo 2 dulu, jeda 2 detik, baru servo 1 membuka.
