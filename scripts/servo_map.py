"""Peta kelas TrashType IoTong ke baris serial ESP32.

Sumber: detect_trash.py di commit 8625083.
Perintah deteksi: `sort <sudut>\\n`
Itu memutar wadah (GPIO 19) ke sudut kelas, lalu firmware membuka
trapdoor (GPIO 18) ke 0 dan menutupnya ke 180.

Sudut bawaan di kode baru:
  kertas/kardus 135, anorganik 90, organik 45, B3 180.
Dataset TrashType tidak berisi organik atau B3.
"""

from __future__ import annotations

CLASS_TO_ANGLE = {
    "cardboard": 135,
    "glass": 90,
    "metal": 90,
    "paper": 135,
    "plastic": 90,
    "trash": 90,
}

NOT_IN_DATASET = {
    "organic": 45,
    "cable": 180,
    "battery": 180,
}


def serial_line(class_name: str) -> str | None:
    """Baris yang dikirim detect_trash.py, atau None jika kelas asing."""
    angle = CLASS_TO_ANGLE.get(str(class_name).strip().lower())
    if angle is None:
        return None
    return f"sort {angle}\n"


def main() -> None:
    print("Kelas TrashType -> sort (wadah GPIO 19, lalu trapdoor GPIO 18):")
    for name, angle in CLASS_TO_ANGLE.items():
        print(f"  {name:12} {serial_line(name).strip()}   # {angle} derajat")
    print("Tidak ada di dataset TrashType:")
    for name, angle in NOT_IN_DATASET.items():
        print(f"  {name:12} sort {angle}")


if __name__ == "__main__":
    main()
