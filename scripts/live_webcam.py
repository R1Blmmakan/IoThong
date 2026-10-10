"""Deteksi YOLO dari webcam laptop dengan antarmuka Native (OpenCV) dan Web Preview (Dual-Mode).

Default: Jendela Native OpenCV (latency < 5ms, 30 FPS lancar tanpa stutter).
Opsi Web: Tambahkan flag --web untuk menyalakan pratinjau browser di http://127.0.0.1:43123.
Servo: Serial COM3/COM9, 115200 8N1. Bukan port HTTP 43123.
"""

from __future__ import annotations

import argparse
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
from ultralytics import YOLO

from send_servo import open_port
from trash_category import resolve_trash_category, sort_line

PREVIEW_HOST = "127.0.0.1"
PREVIEW_PORT = 43123
PREVIEW_URL = f"http://{PREVIEW_HOST}:{PREVIEW_PORT}"

PAGE = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<title>IoTong — pratinjau webcam</title>
<style>
html, body { height: 100%; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #121212; color: #f2f2f2; margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 24px; box-sizing: border-box; }
img { display: block; width: min(960px, 92vw); max-height: 78vh; object-fit: contain; object-position: center; background: #000; margin: 12px auto 0; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.6); }
p { max-width: 720px; line-height: 1.45; }
.badge { display: inline-block; padding: 4px 10px; border-radius: 12px; background: #2e7d32; color: #fff; font-size: 0.85rem; font-weight: 600; margin-bottom: 8px; }
.muted { color: #bdbdbd; font-size: 0.9rem; }
</style>
</head>
<body>
<span class="badge">Siaran Langsung Dual-Mode (30 FPS)</span>
<h1>Pratinjau YOLO IoTong</h1>
<p>Gambar ditransmisikan langsung dari webcam laptop dengan pemrosesan asynchronous.</p>
<p class="muted">Halaman ini di 127.0.0.1:43123. Servo ESP32 menggunakan port serial COM terpisah pada 115200 baud.</p>
<img src="/stream" alt="Frame webcam dengan deteksi YOLO">
</body>
</html>
"""

SAMPLE_PAGE = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<title>IoTong — contoh deteksi, bukan webcam</title>
<style>
html, body { height: 100%; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #161616; color: #f2f2f2; margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 24px; box-sizing: border-box; }
img { display: block; width: min(960px, 92vw); max-height: 78vh; object-fit: contain; object-position: center; background: #000; margin: 12px auto 0; border-radius: 8px; }
p { max-width: 720px; line-height: 1.45; }
.warn { color: #ffd27a; }
</style>
</head>
<body>
<h1>Contoh deteksi, bukan webcam laptop</h1>
<p class="warn">Sumber gambar berasal dari file statis (--source), bukan webcam siaran langsung.</p>
<img src="/stream" alt="Contoh deteksi pada satu gambar statis">
</body>
</html>
"""

NO_CAMERA_PAGE = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<title>IoTong — webcam tidak terbuka</title>
<style>
html, body { height: 100%; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #161616; color: #f2f2f2; margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 24px; box-sizing: border-box; }
p { max-width: 720px; line-height: 1.45; }
</style>
</head>
<body>
<h1>Webcam tidak terbuka</h1>
<p>Server web berjalan, tetapi frame kamera belum diterima. Pastikan webcam terhubung dan tidak sedang dipakai program lain.</p>
</body>
</html>
"""

PAGE_KIND = "camera"
WEB_ENABLED = False


class Frames:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jpeg: bytes | None = None
        self.camera_open = False

    def set_jpeg(self, data: bytes) -> None:
        with self._lock:
            self._jpeg = data
            self.camera_open = True

    def get_jpeg(self) -> bytes | None:
        with self._lock:
            return self._jpeg


FRAMES = Frames()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            if PAGE_KIND == "sample":
                html = SAMPLE_PAGE
            elif FRAMES.camera_open or FRAMES.get_jpeg():
                html = PAGE
            else:
                html = NO_CAMERA_PAGE
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/stream":
            self.send_response(200)
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()
            try:
                while True:
                    jpeg = FRAMES.get_jpeg()
                    if jpeg is None:
                        time.sleep(0.01)
                        continue
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n")
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")
                    # 30 FPS target (33ms) per frame update
                    time.sleep(1 / 30)
            except (BrokenPipeError, ConnectionResetError):
                return
        self.send_error(404)

    def log_message(self, fmt: str, *args) -> None:
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deteksi YOLO webcam untuk IoTong (Native OpenCV & Web Preview Dual-Mode)."
    )
    parser.add_argument("--model", default="yolo11n.pt", help="File bobot model YOLO.")
    parser.add_argument("--camera", type=int, default=0, help="Index webcam (0 internal laptop, 1 external USB).")
    parser.add_argument("--source", default="", help="Uji satu gambar diam tanpa webcam.")
    parser.add_argument("--port", default="", help="Port serial ESP32, contoh COM3 atau COM9. Kosong = simulasi.")
    parser.add_argument("--conf", type=float, default=0.25, help="Ambang batas confidence deteksi.")
    parser.add_argument("--servo-conf", type=float, default=0.80, help="Ambang batas confidence pemicu servo.")
    parser.add_argument("--cooldown", type=float, default=3.0, help="Jeda detik sebelum servo bisa dipicu ulang.")
    parser.add_argument("--stable-frames", type=int, default=3, help="Jumlah frame konsisten sebelum servo dipicu.")
    parser.add_argument("--fps", type=int, default=30, help="Target FPS hardware kamera (default: 30).")
    parser.add_argument("--width", type=int, default=640, help="Lebar resolusi kamera (default: 640).")
    parser.add_argument("--height", type=int, default=480, help="Tinggi resolusi kamera (default: 480).")
    parser.add_argument("--imgsz", type=int, default=320, help="Ukuran inferensi YOLO untuk latensi rendah (default: 320).")
    parser.add_argument("--web", action="store_true", help="Nyalakan pratinjau browser di http://127.0.0.1:43123.")
    parser.add_argument("--no-gui", action="store_true", help="Matikan jendela Native OpenCV (mode headless / browser saja).")
    return parser.parse_args()


def start_preview() -> ThreadingHTTPServer:
    if PREVIEW_PORT in (3000, 5173, 8080):
        raise SystemExit("Port pratinjau tidak boleh 3000, 5173, atau 8080.")
    try:
        server = ThreadingHTTPServer((PREVIEW_HOST, PREVIEW_PORT), Handler)
    except OSError as exc:
        raise SystemExit(f"Tidak bisa bind {PREVIEW_URL}: {exc}") from exc
    thread = threading.Thread(target=server.serve_forever, name="preview", daemon=True)
    thread.start()
    print(f"[Web Preview] Berjalan di: {PREVIEW_URL}")
    print(f"[Servo Info] Serial terpisah: 115200 8N1. Bukan port HTTP {PREVIEW_PORT}.")
    return server


def publish(frame) -> None:
    if not WEB_ENABLED:
        return
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    if ok:
        FRAMES.set_jpeg(buf.tobytes())


MIN_BOX_AREA_RATIO = 0.008
MAX_BOX_AREA_RATIO = 0.90
HOLD_SECONDS = 0.7


def consider_servo(best, args, state, ser) -> None:
    now = time.time()
    if best and best["conf"] >= args.servo_conf:
        label = best["jenis"]
        if state["name"] == label:
            state["count"] += 1
        else:
            state["name"] = label
            state["count"] = 1
        if state["count"] >= args.stable_frames and now - state["last"] >= args.cooldown:
            payload = sort_line(best["angle"]).encode("ascii")
            if ser is None:
                print(f"  [Simulasi Serial] {payload!r}  ({label}, port serial tidak dibuka)")
            else:
                ser.write(payload)
                ser.flush()
                print(f"  [Kirim Serial ke {args.port}] {payload!r}")
            state["last"] = now
            state["count"] = 0
            state["last_sent_angle"] = best["angle"]
            state["last_sent_label"] = label
    else:
        state["count"] = 0


def draw_item(canvas, item) -> None:
    x1, y1, x2, y2 = item["box"]
    color = item["color"]
    cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)
    text = f"{item['jenis']} {item['conf']:.2f}"
    origin = (x1, max(y1 - 8, 22))
    cv2.putText(canvas, text, origin, cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 3)
    cv2.putText(canvas, text, origin, cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)


def draw_hud(canvas, fps: float, infer_ms: float, args, state, best) -> None:
    h, w = canvas.shape[:2]
    # Semi-transparent top banner
    overlay = canvas.copy()
    cv2.rectangle(overlay, (0, 0), (w, 40), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.6, canvas, 0.4, 0, canvas)

    # Status FPS & Latency
    fps_color = (0, 255, 120) if fps >= 25 else ((0, 215, 255) if fps >= 15 else (0, 70, 255))
    fps_text = f"FPS: {fps:4.1f} | Latensi: {infer_ms:3.0f}ms"
    cv2.putText(canvas, fps_text, (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 3)
    cv2.putText(canvas, fps_text, (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.58, fps_color, 1)

    # Status Servo
    now = time.time()
    last_send = state.get("last", 0.0)
    cooldown_left = max(0.0, args.cooldown - (now - last_send))
    port_label = args.port.upper() if args.port else "SIMULASI"

    if cooldown_left > 0:
        servo_text = f"Servo: {port_label} (Cooldown {cooldown_left:.1f}s)"
        s_color = (0, 215, 255)
    elif best and best["conf"] >= args.servo_conf:
        servo_text = f"Servo: {port_label} -> SORT {best['angle']} [{state.get('count', 0)}/{args.stable_frames}]"
        s_color = (0, 255, 120)
    else:
        servo_text = f"Servo: {port_label} [Standby]"
        s_color = (200, 200, 200)

    cv2.putText(canvas, servo_text, (max(10, w - 380), 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3)
    cv2.putText(canvas, servo_text, (max(10, w - 380), 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, s_color, 1)


class CameraStream:
    """Thread pembaca kamera mandiri untuk menghilangkan buffer lag dan stuttering."""

    def __init__(self, camera_index: int, width: int = 640, height: int = 480, fps: int = 30) -> None:
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.target_fps = fps
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(camera_index)

        if self.cap.isOpened():
            # MJPG codec sangat krusial di Windows DirectShow agar tidak bottleneck di USB 2.0
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)

        self.stopped = False
        self.lock = threading.Lock()
        self.ret = False
        self.frame = None
        if self.cap.isOpened():
            self.ret, self.frame = self.cap.read()

    def start(self) -> "CameraStream":
        if self.cap.isOpened():
            t = threading.Thread(target=self._update, name="CameraWorker", daemon=True)
            t.start()
        return self

    def _update(self) -> None:
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            with self.lock:
                self.ret = ret
                self.frame = frame

    def read(self) -> tuple[bool, any]:
        with self.lock:
            if self.frame is None:
                return False, None
            return self.ret, self.frame.copy()

    def is_opened(self) -> bool:
        return self.cap.isOpened()

    def get_actual_fps(self) -> float:
        if self.cap.isOpened():
            val = self.cap.get(cv2.CAP_PROP_FPS)
            return val if val > 0 else float(self.target_fps)
        return 0.0

    def stop(self) -> None:
        self.stopped = True
        if self.cap.isOpened():
            self.cap.release()


class AsyncDetector:
    """Menjalankan inferensi YOLO di background thread agar display rendering tetap 30+ FPS."""

    def __init__(self, model, args, state, ser) -> None:
        self.model = model
        self.args = args
        self.state = state
        self.ser = ser
        self.lock = threading.Lock()
        self.new_frame = None
        self.has_new_frame = threading.Event()
        self.stopped = False
        self.latest_found: list = []
        self.best_item = None
        self.infer_ms: float = 0.0

    def start(self) -> "AsyncDetector":
        t = threading.Thread(target=self._worker, name="YOLOWorker", daemon=True)
        t.start()
        return self

    def submit(self, frame) -> None:
        with self.lock:
            self.new_frame = frame
        self.has_new_frame.set()

    def _worker(self) -> None:
        while not self.stopped:
            self.has_new_frame.wait()
            self.has_new_frame.clear()
            with self.lock:
                frame_to_process = self.new_frame
            if frame_to_process is None or self.stopped:
                continue

            t0 = time.perf_counter()
            result = self.model.predict(
                frame_to_process,
                conf=self.args.conf,
                imgsz=self.args.imgsz,
                verbose=False,
            )[0]
            infer_duration = (time.perf_counter() - t0) * 1000.0

            found = []
            boxes = result.boxes
            height, width = frame_to_process.shape[:2]
            total_area = max(1, width * height)
            if boxes is not None:
                for box in boxes:
                    raw = str(self.model.names[int(box.cls[0])])
                    if raw.strip().lower() == "person":
                        continue
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    area_ratio = max(0, x2 - x1) * max(0, y2 - y1) / total_area
                    if area_ratio < MIN_BOX_AREA_RATIO or area_ratio > MAX_BOX_AREA_RATIO:
                        continue
                    mapped = resolve_trash_category(raw)
                    if mapped is None:
                        continue
                    nama, jenis, angle, color = mapped
                    found.append(
                        {
                            "box": (x1, y1, x2, y2),
                            "nama": nama,
                            "jenis": jenis,
                            "angle": angle,
                            "color": color,
                            "conf": conf,
                            "raw": raw,
                        }
                    )

            best = None
            if found:
                for item in found:
                    if best is None or item["conf"] > best["conf"]:
                        best = item
                if best:
                    print(f"  [Deteksi] {best['raw']} -> {best['jenis']} ({best['conf']:.2f}) -> Sudut {best['angle']}°")

            consider_servo(best, self.args, self.state, self.ser)

            with self.lock:
                self.latest_found = found
                self.best_item = best
                self.infer_ms = infer_duration

    def get_results(self) -> tuple[list, any, float]:
        with self.lock:
            return list(self.latest_found), self.best_item, self.infer_ms

    def stop(self) -> None:
        self.stopped = True
        self.has_new_frame.set()


def annotate_single(model, frame, args, state, ser):
    result = model.predict(frame, conf=args.conf, imgsz=args.imgsz, verbose=False)[0]
    canvas = frame.copy()
    height, width = canvas.shape[:2]
    total_area = max(1, width * height)
    found = []
    boxes = result.boxes
    if boxes is not None:
        for box in boxes:
            raw = str(model.names[int(box.cls[0])])
            if raw.strip().lower() == "person":
                continue
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            area_ratio = max(0, x2 - x1) * max(0, y2 - y1) / total_area
            if area_ratio < MIN_BOX_AREA_RATIO or area_ratio > MAX_BOX_AREA_RATIO:
                continue
            mapped = resolve_trash_category(raw)
            if mapped is None:
                continue
            nama, jenis, angle, color = mapped
            found.append(
                {
                    "box": (x1, y1, x2, y2),
                    "nama": nama,
                    "jenis": jenis,
                    "angle": angle,
                    "color": color,
                    "conf": conf,
                    "raw": raw,
                }
            )
    best = None
    for item in found:
        draw_item(canvas, item)
        if best is None or item["conf"] > best["conf"]:
            best = item
    consider_servo(best, args, state, ser)
    return canvas


def main() -> None:
    global PAGE_KIND, WEB_ENABLED
    args = parse_args()

    # Validasi port serial
    if args.port and not str(args.port).upper().startswith("COM"):
        raise SystemExit("Port serial berbentuk COM lalu angka, contoh COM3 atau COM9. Bukan 43123.")
    ser = open_port(args.port) if args.port else None
    state = {"name": None, "count": 0, "last": 0.0, "hold_items": [], "hold_until": 0.0}

    # Jika --no-gui dipakai tanpa --web, aktifkan web otomatis agar tidak berjalan buta
    if args.no_gui and not args.web:
        print("[Info] Flag --no-gui aktif tanpa --web. Mengaktifkan --web otomatis untuk pratinjau browser.")
        args.web = True

    WEB_ENABLED = args.web
    server = None
    if args.web:
        if args.source:
            PAGE_KIND = "sample"
        server = start_preview()

    print("=" * 60)
    print("  IoTong YOLO Real-Time Classification")
    print(f"  Mode Tampilan: {'Native (OpenCV)' if not args.no_gui else 'Headless'}" + (" + Web Preview" if args.web else ""))
    print(f"  Target Kamera: Index {args.camera} @ {args.fps} FPS ({args.width}x{args.height})")
    print(f"  Serial Servo : {args.port if args.port else 'Simulasi (tanpa koneksi kabel)'}")
    print("=" * 60)

    try:
        model = YOLO(args.model)

        # Mode uji dengan satu gambar diam
        if args.source:
            frame = cv2.imread(args.source)
            if frame is None:
                raise SystemExit(f"Gambar tidak terbaca: {args.source}")
            print(f"[Mode Statis] Menggunakan gambar: {args.source}")
            annotated = annotate_single(model, frame, args, state, ser)
            if args.web:
                publish(annotated)
            if not args.no_gui:
                cv2.imshow("IoTong - Deteksi Sampah (Static Image)", annotated)
                print("Tekan Q atau ESC di jendela untuk keluar.")
                while True:
                    key = cv2.waitKey(50) & 0xFF
                    if key in (27, ord("q"), ord("Q")):
                        break
            else:
                while True:
                    time.sleep(1)
            return

        # Buka kamera dengan worker thread
        stream = CameraStream(args.camera, width=args.width, height=args.height, fps=args.fps)
        if not stream.is_opened():
            print(
                f"\n[ERROR] Webcam index {args.camera} tidak bisa dibuka.\n"
                "Petunjuk:\n"
                "  1. Pastikan nomor index kamera benar (biasanya 0 untuk webcam bawaan laptop, atau 1 untuk USB).\n"
                "  2. Tutup aplikasi lain yang mungkin sedang memakai kamera (Camera app, Zoom, Teams, browser).\n"
            )
            return

        stream.start()
        actual_fps = stream.get_actual_fps()
        print(f"[Kamera] Webcam index {args.camera} berhasil dibuka (~{actual_fps:.0f} FPS).")

        # Inisialisasi detector asynchronous
        detector = AsyncDetector(model, args, state, ser)
        detector.start()

        window_title = "IoTong - Deteksi Sampah YOLO [30 FPS Native]"
        if not args.no_gui:
            cv2.namedWindow(window_title, cv2.WINDOW_AUTOSIZE)

        fps_history: list[float] = []
        last_t = time.perf_counter()
        current_fps = 30.0

        print("[Sistem Siap] Menjalankan loop deteksi. Tekan 'q' atau ESC pada jendela untuk berhenti.\n")

        while True:
            ret, frame = stream.read()
            if not ret or frame is None:
                time.sleep(0.005)
                continue

            # Hitung rolling FPS riil
            t_now = time.perf_counter()
            dt = t_now - last_t
            last_t = t_now
            if dt > 0:
                fps_instant = 1.0 / dt
                fps_history.append(fps_instant)
                if len(fps_history) > 20:
                    fps_history.pop(0)
                current_fps = sum(fps_history) / len(fps_history)

            # Kirim frame terbaru ke background worker jika siap
            detector.submit(frame)
            found, best, infer_ms = detector.get_results()

            # Mekanisme stabilisasi tampilan bounding box (hold)
            now_sec = time.time()
            if found:
                state["hold_items"] = found
                state["hold_until"] = now_sec + HOLD_SECONDS
                visible = found
            elif now_sec < state.get("hold_until", 0.0):
                visible = state.get("hold_items", [])
            else:
                visible = []

            canvas = frame.copy()
            for item in visible:
                draw_item(canvas, item)

            draw_hud(canvas, current_fps, infer_ms, args, state, best)

            if args.web:
                publish(canvas)

            if not args.no_gui:
                cv2.imshow(window_title, canvas)
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q"), ord("Q")):
                    print("\nPengguna menghentikan program.")
                    break
            else:
                time.sleep(1 / args.fps)

    except KeyboardInterrupt:
        print("\nBerhenti (Ctrl+C).")
    finally:
        if "detector" in locals():
            detector.stop()
        if "stream" in locals():
            stream.stop()
        if not args.no_gui:
            cv2.destroyAllWindows()
        if server is not None:
            server.shutdown()
        if ser is not None and ser.is_open:
            ser.write(b"trapdoor close\n")
            ser.write(b"pos2 0\n")
            ser.flush()
            ser.close()
        print("Selesai dan port ditutup dengan aman.")


if __name__ == "__main__":
    main()
