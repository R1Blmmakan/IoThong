"""Kirim sudut ke dua servo ESP32.

Perintah teks dari firmware IoTong, bukan protokol baru:
  src/main.cpp membaca Serial.readStringUntil('\\n')
  detect_trash.py di commit 8625083 menulis:  sort <derajat>\\n
  contoh byte: b"sort 90\\n"
  Firmware juga menerima `pos <derajat>` sebagai urutan sort yang sama.
  Servo 1 (trapdoor) GPIO18 / D18, buka 0 tutup 180.
  Servo 2 (wadah) GPIO13 / D13, sudut 0-360.
  B3 0, Organik 120, Anorganik 240.

Port COM3, baud 115200, 8N1. Sama dengan Serial.begin(115200) di firmware.

COM3 bukan port halaman pratinjau. Halaman YOLO ada di 127.0.0.1:43123.
Mesin cloud tidak membuka COM3.
"""

from __future__ import annotations

import argparse
import sys
import time

from servo_map import CLASS_TO_ANGLE, serial_line

PORT = "COM3"
BAUD = 115200
FIRMWARE_BAUD = 115200


def pos_bytes(angle: int) -> bytes:
    if not isinstance(angle, int) or isinstance(angle, bool) or not 0 <= angle <= 360:
        raise SystemExit("Sudut harus bilangan 0 sampai 360.")
    return f"sort {angle}\n".encode("ascii")


def describe_link() -> None:
    print(f"Serial laptop: {PORT} @ {BAUD} 8N1")
    print("mode COM3: parity None, data 8, stop 1, timeout OFF, XON/XOFF OFF, CTS OFF, DSR OFF, DTR ON, RTS ON")
    print(f"Firmware IoTong: Serial.begin({FIRMWARE_BAUD}).")
    print("Halaman pratinjau YOLO, saat live_webcam.py jalan: http://127.0.0.1:43123")
    print("43123 adalah HTTP di laptop. Bukan baud, bukan COM3.")


def open_port(port: str | None = None):
    """Buka port serial di Windows. Nomor COM beda di tiap laptop."""
    name = port or PORT
    if sys.platform != "win32":
        raise SystemExit(
            f"Port serial {name} ada di laptop Windows pada 115200 8N1. Mesin ini tidak membuka port serial."
        )
    import serial

    ser = serial.Serial()
    ser.port = name
    ser.baudrate = BAUD
    ser.bytesize = serial.EIGHTBITS
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE
    ser.timeout = None
    ser.write_timeout = None
    ser.xonxoff = False
    ser.rtscts = False
    ser.dsrdtr = False
    ser.dtr = True
    ser.rts = True
    try:
        ser.open()
    except Exception as exc:
        raise SystemExit(f"Gagal membuka {name}: {exc}. Port tidak dianggap terbuka.") from exc
    ser.dtr = True
    ser.rts = True
    return ser


def list_ports() -> None:
    describe_link()
    try:
        from serial.tools import list_ports
    except ImportError as exc:
        raise SystemExit("pyserial belum terpasang. pip install -r requirements.txt") from exc
    ports = list(list_ports.comports())
    if not ports:
        print("Tidak ada port serial terdeteksi di mesin ini.")
        return
    names = []
    for port in ports:
        print(f"  {port.device}  {port.description}")
        names.append(port.device)
    if PORT in names:
        print(f"{PORT} ada di daftar.")
    else:
        print(f"{PORT} tidak ada di mesin ini. Di laptop, port yang dipakai adalah {PORT}.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kirim `sort <derajat>` ke ESP32 lewat COM3.")
    parser.add_argument("--list", action="store_true", help="Tampilkan port serial.")
    parser.add_argument("--port", choices=(PORT,), help="Hanya COM3.")
    parser.add_argument("--class", dest="class_name", choices=sorted(CLASS_TO_ANGLE), help="Kelas TrashType.")
    parser.add_argument("--angle", type=int, help="Sudut 0-180. Menggantikan --class.")
    parser.add_argument("--dry-run", action="store_true", help="Cetak byte. Jangan buka port.")
    parser.add_argument("--ping", action="store_true", help="Kirim status\\n bawaan firmware, lalu baca balasan.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.list:
        list_ports()
        if args.class_name is None and args.angle is None and not args.ping:
            return

    if args.ping and args.class_name is None and args.angle is None:
        payload = b"status\n"
    elif args.class_name is not None:
        line = serial_line(args.class_name)
        assert line is not None
        payload = line.encode("ascii")
    elif args.angle is not None:
        payload = pos_bytes(args.angle)
    else:
        raise SystemExit("Isi --class, --angle, atau --ping. Contoh: --dry-run --port COM3 --class plastic")

    describe_link()
    print(f"byte: {payload!r}")

    if args.dry_run or args.port is None:
        print("dry-run: COM3 tidak dibuka.")
        return

    ser = open_port()
    try:
        ser.write(payload)
        ser.flush()
        print(f"terkirim ke {PORT}")
        if args.ping:
            time.sleep(0.3)
            reply = ser.read(256)
            print("balasan:", reply.decode("utf-8", errors="replace") or "(kosong)")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
