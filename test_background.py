"""
test_background.py - เทสส่งปุ่มเข้า FiveM ตอนอยู่พื้นหลัง (ไม่ focus)

วิธีเทส:
  1. เปิดเกม ยืนเฉย ๆ
  2. รัน: python test_background.py
  3. สลับไปหน้าต่างอื่น (เช่น Notepad) ภายใน 5 วิ — อย่าคลิกกลับเกม
  4. สคริปต์จะส่งปุ่ม G เข้า FiveM ทุก 2 วิ 5 ครั้ง
  5. ดูว่าตัวละครในเกมเริ่มฟาร์มไหม / ตัว g เด้งใน Notepad แทนไหม
     - ตัวละครขยับ = พื้นหลังกดได้ (PostMessage ผ่าน)
     - ไม่ขยับ = FiveM ไม่รับ input พื้นหลัง (ใช้ raw input)
"""

import ctypes
import time

user32 = ctypes.windll.user32

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_G = 0x47
SC_G = 0x22


def find_fivem_window():
    """หา hwnd ของหน้าต่าง FiveM"""
    result = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def enum_cb(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if "FiveM" in buf.value:
                result.append((hwnd, buf.value))
        return True

    user32.EnumWindows(enum_cb, None)
    return result


def post_key(hwnd, vk, scan):
    """ส่ง WM_KEYDOWN/WM_KEYUP เข้า window ตรง ๆ (ไม่ต้อง focus)"""
    lparam_down = 1 | (scan << 16)
    lparam_up = 1 | (scan << 16) | (1 << 30) | (1 << 31)
    user32.PostMessageW(hwnd, WM_KEYDOWN, vk, lparam_down)
    time.sleep(0.08)
    user32.PostMessageW(hwnd, WM_KEYUP, vk, lparam_up)


def main():
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    windows = find_fivem_window()
    if not windows:
        print("ไม่เจอหน้าต่าง FiveM — เปิดเกมก่อน")
        return
    hwnd, title = windows[0]
    print(f"เจอ: {title} (hwnd={hwnd})")
    print("สลับไปหน้าต่างอื่นภายใน 5 วิ (อย่า focus เกม)...")
    time.sleep(5)

    for i in range(1, 6):
        print(f"ส่งปุ่ม G ครั้งที่ {i}/5 ...")
        post_key(hwnd, VK_G, SC_G)
        time.sleep(2)

    print("จบเทส — ถ้าตัวละครเริ่มฟาร์ม = พื้นหลังกดได้, ถ้าไม่ = FiveM ไม่รับ")


if __name__ == "__main__":
    main()
