"""
calibrate.py - บันทึกพิกัดปุ่ม + template ช่องไอเทมสำหรับจอของคุณ

วิธีใช้:
  1. รัน: python calibrate.py
  2. เข้าเกม เปิดหน้าต่างที่เกี่ยวข้อง แล้วเอาเมาส์ชี้ตามจุดต่าง ๆ กดปุ่มตัวเลข:
     [1] ชี้กลางไอคอนไอเทมใน INVENTORY      → บันทึก stone_template.png
     [2] ชี้จุดว่างฝั่ง SECONDARY (จุดปล่อยของ) → DROP_POINT
     [3] ชี้ปุ่ม Max ใน dialog                → BTN_MAX
     [4] ชี้ปุ่ม O ยืนยัน ใน dialog            → BTN_CONFIRM
     [5] ชี้ปุ่ม "เปิดหลังรถ" ในหน้า GARAGE     → BTN_OPEN_TRUNK
     [6] เปิดแผนที่/เมนู pause (Esc) ค้างไว้ แล้วกด 6 → map_template.png
     [7] เปิดหน้าท้ายรถ (กด L) ค้างไว้ แล้วกด 7 → garage_template.png
     [8] ตอนไอเทมเต็มความจุ (เช่น 40/40, 100/100) กด 8 → full_template.png
     [0] บันทึก calibration.json แล้วออก
"""

import ctypes
import json
import os
import sys
import time

import cv2
import keyboard
import mss
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(__file__)
TEMPLATE_SIZE = 70  # ขนาด template ที่ crop รอบ cursor


def get_cursor():
    pt = ctypes.wintypes.POINT() if hasattr(ctypes, 'wintypes') else None
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    p = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(p))
    return p.x, p.y


def save_template(sct):
    x, y = get_cursor()
    half = TEMPLATE_SIZE // 2
    region = {"left": x - half, "top": y - half, "width": TEMPLATE_SIZE, "height": TEMPLATE_SIZE}
    img = np.array(sct.grab(region))
    bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    path = os.path.join(HERE, "stone_template.png")
    cv2.imwrite(path, bgr)
    print(f"[1] ✓ บันทึก template ช่อง Stone ที่ ({x},{y}) → {path}")


def main():
    data = {}
    print(__doc__)

    with mss.mss() as sct:
        def rec(key, name):
            pos = get_cursor()
            data[name] = pos
            print(f"[{key}] ✓ {name} = {pos}")

        def save_region_template(region, filename, label):
            import config
            img = np.array(sct.grab(getattr(config, region)))
            bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            path = os.path.join(HERE, filename)
            cv2.imwrite(path, bgr)
            print(f"✓ บันทึก template {label} → {path}")

        keyboard.add_hotkey("1", lambda: save_template(sct))
        keyboard.add_hotkey("2", lambda: rec("2", "DROP_POINT"))
        keyboard.add_hotkey("3", lambda: rec("3", "BTN_MAX"))
        keyboard.add_hotkey("4", lambda: rec("4", "BTN_CONFIRM"))
        keyboard.add_hotkey("5", lambda: rec("5", "BTN_OPEN_TRUNK"))
        keyboard.add_hotkey("6", lambda: save_region_template("MAP_CHECK_REGION", "map_template.png", "แผนที่/เมนู"))
        keyboard.add_hotkey("7", lambda: save_region_template("GARAGE_CHECK_REGION", "garage_template.png", "หน้าท้ายรถ"))
        keyboard.add_hotkey("8", lambda: save_region_template("COUNTER_REGION", "full_template.png", "counter ตอนเต็ม"))

        print("รอการกดปุ่ม... (กด 0 เพื่อบันทึกและออก)")
        keyboard.wait("0")

    path = os.path.join(HERE, "calibration.json")
    existing = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    existing.update(data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
    print(f"✓ บันทึก {path} แล้ว: {existing}")


if __name__ == '__main__':
    main()
