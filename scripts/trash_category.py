"""Peta kelas YOLO ke Organik / Anorganik, sama seperti detect_trash.py di IoTong.

Sudut wadah 360 derajat:
  B3 0, organik 120, anorganik 240.
"""

from __future__ import annotations

# Servo 2 = 360 derajat, tiga sektor 120 derajat.
ANGLE_B3 = 0
ANGLE_ORGANIK = 120
ANGLE_ANORGANIK = 240
ANGLE_KERTAS = ANGLE_ANORGANIK

EXPLICIT_TRASH_MAP = {
    "cable": ("Kabel Listrik / USB", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "cables": ("Kabel Listrik / USB", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "wire": ("Kabel / Kawat", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "wires": ("Kabel / Kawat", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "cable charger": ("Kabel Charger", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "patch cord": ("Kabel Jaringan LAN", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "charger": ("Charger / Adaptor", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "battery": ("Baterai Bekas", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "batteries": ("Baterai Bekas", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "e-waste": ("Sampah Elektronik", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "electronics": ("Komponen Elektronik", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "electronic": ("Komponen Elektronik", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "pcb": ("Papan Sirkuit PCB", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "circuit board": ("Papan Sirkuit PCB", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "cell phone": ("Handphone / Gadget", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "phone": ("Handphone / Gadget", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "mouse": ("Mouse Komputer", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "keyboard": ("Keyboard Komputer", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "hazardous waste": ("Limbah Berbahaya (B3)", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "medical-waste": ("Limbah Medis / Masker", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "aerosols": ("Kaleng Semprot / Aerosol", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    "stainless": ("Stainless Steel", "Anorganik (Logam)", ANGLE_ANORGANIK, (220, 220, 220)),
    "stainless steel": ("Stainless Steel", "Anorganik (Logam)", ANGLE_ANORGANIK, (220, 220, 220)),
    "metal": ("Logam / Besi", "Anorganik (Logam)", ANGLE_ANORGANIK, (200, 200, 200)),
    "scrap metal": ("Besi / Logam Bekas", "Anorganik (Logam)", ANGLE_ANORGANIK, (200, 200, 200)),
    "metal shavings": ("Serpihan Logam", "Anorganik (Logam)", ANGLE_ANORGANIK, (200, 200, 200)),
    "aluminum can": ("Kaleng Aluminium", "Anorganik (Logam)", ANGLE_ANORGANIK, (200, 200, 200)),
    "aluminum caps": ("Tutup Aluminium", "Anorganik (Logam)", ANGLE_ANORGANIK, (200, 200, 200)),
    "tin": ("Kaleng Timah", "Anorganik (Logam)", ANGLE_ANORGANIK, (200, 200, 200)),
    "iron utensils": ("Peralatan Besi", "Anorganik (Logam)", ANGLE_ANORGANIK, (200, 200, 200)),
    "foil": ("Aluminium Foil", "Anorganik (Logam)", ANGLE_ANORGANIK, (200, 200, 200)),
    "fork": ("Garpu Logam", "Anorganik (Logam)", ANGLE_ANORGANIK, (200, 200, 200)),
    "knife": ("Pisau Logam", "Anorganik (Logam)", ANGLE_ANORGANIK, (200, 200, 200)),
    "spoon": ("Sendok Logam", "Anorganik (Logam)", ANGLE_ANORGANIK, (200, 200, 200)),
    "plastic": ("Plastik", "Anorganik", ANGLE_ANORGANIK, (255, 191, 0)),
    "plastic bottle": ("Botol Plastik", "Anorganik", ANGLE_ANORGANIK, (255, 191, 0)),
    "bottle": ("Botol Plastik", "Anorganik", ANGLE_ANORGANIK, (255, 191, 0)),
    "cup": ("Gelas Plastik", "Anorganik", ANGLE_ANORGANIK, (255, 191, 0)),
    "plastic cup": ("Gelas Plastik", "Anorganik", ANGLE_ANORGANIK, (255, 191, 0)),
    "plastic bag": ("Kantong Plastik", "Anorganik", ANGLE_ANORGANIK, (255, 191, 0)),
    "plastic caps": ("Tutup Botol Plastik", "Anorganik", ANGLE_ANORGANIK, (255, 191, 0)),
    "glass": ("Kaca", "Anorganik", ANGLE_ANORGANIK, (255, 144, 30)),
    "glass bottle": ("Botol Kaca", "Anorganik", ANGLE_ANORGANIK, (255, 144, 30)),
    "ceramic": ("Keramik", "Anorganik", ANGLE_ANORGANIK, (255, 144, 30)),
    "recyclable": ("Sampah Daur Ulang", "Anorganik", ANGLE_ANORGANIK, (255, 191, 0)),
    "trash": ("Sampah Anorganik", "Anorganik", ANGLE_ANORGANIK, (180, 105, 255)),
    "clothes": ("Kain / Tekstil", "Anorganik", ANGLE_ANORGANIK, (180, 105, 255)),
    "textile": ("Kain / Tekstil", "Anorganik", ANGLE_ANORGANIK, (180, 105, 255)),
    "paper": ("Kertas", "Kertas / Karton", ANGLE_KERTAS, (0, 215, 255)),
    "cardboard": ("Kardus", "Kertas / Karton", ANGLE_KERTAS, (0, 165, 255)),
    "book": ("Buku / Kertas", "Kertas / Karton", ANGLE_KERTAS, (0, 215, 255)),
    "paper bag": ("Kantong Kertas", "Kertas / Karton", ANGLE_KERTAS, (0, 215, 255)),
    "paper cups": ("Gelas Kertas", "Kertas / Karton", ANGLE_KERTAS, (0, 215, 255)),
    "tetra pack": ("Karton Kemasan", "Kertas / Karton", ANGLE_KERTAS, (0, 165, 255)),
    "organic": ("Sisa Makanan", "Organik", ANGLE_ORGANIK, (0, 255, 0)),
    "biological": ("Sampah Organik", "Organik", ANGLE_ORGANIK, (0, 255, 0)),
    "food": ("Sisa Makanan", "Organik", ANGLE_ORGANIK, (0, 255, 0)),
    "banana": ("Kulit Buah", "Organik", ANGLE_ORGANIK, (0, 255, 0)),
    "apple": ("Sisa Buah", "Organik", ANGLE_ORGANIK, (0, 255, 0)),
    "orange": ("Sisa Buah", "Organik", ANGLE_ORGANIK, (0, 255, 0)),
    "sandwich": ("Sisa Makanan", "Organik", ANGLE_ORGANIK, (0, 255, 0)),
    "pizza": ("Sisa Makanan", "Organik", ANGLE_ORGANIK, (0, 255, 0)),
    "donut": ("Sisa Makanan", "Organik", ANGLE_ORGANIK, (0, 255, 0)),
    "vegetable": ("Sayuran", "Organik", ANGLE_ORGANIK, (0, 255, 0)),
    "wood": ("Kayu / Ranting", "Organik", ANGLE_ORGANIK, (0, 255, 0)),
}

KEYWORD_RULES = [
    (["cable", "wire", "cord", "charger", "usb", "patch", "lan", "lead"], "Kabel / Kabel Charger", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    (["battery", "batteries", "accumulator", "cell", "powerbank"], "Baterai / Sel Daya", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    (["electronic", "pcb", "circuit", "chip", "phone", "hardware", "laptop", "mouse", "keyboard", "e-waste", "display", "screen"], "Elektronik / E-Waste", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    (["hazardous", "toxic", "chemical", "medical", "mask", "syringe", "aerosol"], "Limbah B3 Berbahaya", "B3 / Elektronik", ANGLE_B3, (0, 0, 255)),
    (["stainless", "steel", "metal", "iron", "aluminum", "aluminium", "tin", "can", "cans", "foil", "copper", "brass", "scrap"], "Stainless / Logam", "Anorganik (Logam)", ANGLE_ANORGANIK, (220, 220, 220)),
    (["paper", "cardboard", "carton", "book", "box", "magazine", "newspaper", "cellulose"], "Kertas & Karton", "Kertas / Karton", ANGLE_KERTAS, (0, 215, 255)),
    (["plastic", "bottle", "cup", "straw", "poly", "film", "bag", "pet", "hdpe", "pvc"], "Plastik", "Anorganik", ANGLE_ANORGANIK, (255, 191, 0)),
    (["glass", "jar", "ceramic", "porcelain"], "Kaca & Keramik", "Anorganik", ANGLE_ANORGANIK, (255, 144, 30)),
    (["organic", "food", "fruit", "vegetable", "leaf", "leaves", "wood", "biological", "bread", "meat", "rice"], "Sampah Organik", "Organik", ANGLE_ORGANIK, (0, 255, 0)),
]


# Tiga kelompok saja. Kertas/kardus dari dataset TrashType masuk Anorganik.
# BGR: Organik hijau, Anorganik dan B3 kuning supaya terbaca di gambar gelap.
COLOR_ORGANIK = (0, 255, 0)
COLOR_ANORGANIK = (0, 255, 255)
COLOR_B3 = (0, 255, 255)


def as_three_groups(nama, jenis, angle, _color):
    if str(jenis).startswith("B3") or angle == ANGLE_B3:
        return nama, "B3", ANGLE_B3, COLOR_B3
    if jenis == "Organik" or angle == ANGLE_ORGANIK:
        return nama, "Organik", ANGLE_ORGANIK, COLOR_ORGANIK
    return nama, "Anorganik", ANGLE_ANORGANIK, COLOR_ANORGANIK


def resolve_trash_category(raw_class_name: str):
    """Nama, jenis, sudut, warna. None kalau bukan sampah yang dikenali."""
    clean_name = str(raw_class_name).strip().lower()
    if clean_name in EXPLICIT_TRASH_MAP:
        return as_three_groups(*EXPLICIT_TRASH_MAP[clean_name])
    for keywords, display_name, kategori, angle, color in KEYWORD_RULES:
        if any(kw in clean_name for kw in keywords):
            return as_three_groups(f"{display_name} ({clean_name})", kategori, angle, color)
    return None


def sort_line(angle: int) -> str:
    return f"sort {angle}\n"
