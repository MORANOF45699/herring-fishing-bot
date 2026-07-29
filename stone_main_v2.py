"""
stone_main_v2.py - บอทเก็บไอเทม เวอร์ชันไม่มีหน้าคอนโซล + HUD เล็กบนจอ

รันผ่าน run_v2.bat (pythonw = ไม่มีหน้าต่างดำ)
  - HUD มุมบนซ้าย บอกสถานะ ลากย้ายตำแหน่งได้
  - กด F10 เริ่ม/พัก เหมือนเดิม
  - ดับเบิลคลิกขวาที่ HUD = ปิดโปรแกรม
  - log ทั้งหมดเขียนลง bot_log.txt แทนคอนโซล
หมายเหตุ: เกมต้องเป็น Borderless/Windowed — Fullscreen แท้ HUD จะไม่ลอยทับ
"""

import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

# pythonw ไม่มี stdout → เขียน log ลงไฟล์แทน (print เดิมทุกไฟล์ไปลงนี่)
_log = open(os.path.join(HERE, "bot_log.txt"), "a", encoding="utf-8", buffering=1)
sys.stdout = _log
sys.stderr = _log

import tkinter as tk

import keyboard
import mss

import config
import stone_input as inp
from stone_detector import (full_match_score, full_min_width, is_map_open,
                            counter_changed)
from stone_actions import (deposit_to_trunk, discard_items, drink_if_due,
                           drink_remaining)

MAX_DEPOSIT_FAILS = 2

status = {"text": "พร้อม — กด F10 เริ่ม", "color": "#cccccc"}
stop_flag = [False]


def set_status(text, color="#2ecc71"):
    status["text"] = text
    status["color"] = color
    print(f"[v2] {text}")


def bot_loop():
    state = {"active": False, "last_change": time.time()}

    def toggle():
        state["active"] = not state["active"]
        if state["active"]:
            set_status("▶ เริ่ม — กด G ออโต้ฟาร์ม", "#2ecc71")
            time.sleep(0.3)
            inp.press_g()
            state["last_change"] = time.time()
        else:
            set_status("⏸ พัก — กด F10 เริ่มต่อ", "#f39c12")

    keyboard.add_hotkey(config.KEY_TOGGLE, toggle)

    deposit_fails = 0
    with mss.mss() as sct:
        while not stop_flag[0]:
            if not state["active"]:
                time.sleep(0.2)
                continue

            if is_map_open(sct):
                set_status("⚠ เมนูค้าง — ปิดแล้วฟาร์มต่อ", "#f39c12")
                inp.press_esc()
                time.sleep(1.0)
                inp.press_g()
                time.sleep(1.5)
                continue

            drink_if_due(sct)

            score, width = full_match_score(sct)
            full = (score >= config.FULL_MATCH_THRESHOLD
                    and width >= full_min_width())

            mins = drink_remaining() / 60
            water = f"💧{int(mins // 60)}:{int(mins % 60):02d}"
            if full:
                set_status(f"🔴 เต็ม! กำลังจัดการ | {water}", "#e74c3c")
            else:
                set_status(f"⛏ ฟาร์ม {score:.2f} | {water}", "#2ecc71")

            if counter_changed(sct):
                state["last_change"] = time.time()
            elif (not full and
                  time.time() - state["last_change"] > config.STUCK_TIMEOUT):
                set_status("⚠ ค้าง — กด G ย้ำ", "#f39c12")
                inp.press_g()
                state["last_change"] = time.time()

            if full:
                time.sleep(config.FULL_DETECTED_DELAY)
                set_status("📦 กำลังฝาก/ทิ้งของ...", "#3498db")
                if config.DEPOSIT_MODE == "discard":
                    ok = discard_items(sct)
                else:
                    ok = deposit_to_trunk(sct)
                state["last_change"] = time.time()
                if ok:
                    deposit_fails = 0
                else:
                    deposit_fails += 1
                    set_status(f"⚠ ฝากพลาด ({deposit_fails}) — ลองใหม่เรื่อย ๆ", "#e74c3c")
                time.sleep(1.0)

            time.sleep(config.CHECK_INTERVAL)


def main():
    root = tk.Tk()
    root.overrideredirect(True)          # ไม่มีกรอบหน้าต่าง
    root.attributes("-topmost", True)    # ลอยทับเกม (borderless)
    root.attributes("-alpha", 0.85)
    root.configure(bg="#111111")
    root.geometry("+8+8")

    label = tk.Label(root, text=status["text"], fg=status["color"],
                     bg="#111111", font=("Segoe UI", 10, "bold"),
                     padx=10, pady=4)
    label.pack()

    # ลากย้าย HUD ได้
    drag = {"x": 0, "y": 0}

    def press(e):
        drag["x"], drag["y"] = e.x, e.y

    def move(e):
        root.geometry(f"+{e.x_root - drag['x']}+{e.y_root - drag['y']}")

    label.bind("<Button-1>", press)
    label.bind("<B1-Motion>", move)

    # ดับเบิลคลิกขวา = ปิดโปรแกรม
    def quit_app(_e=None):
        stop_flag[0] = True
        root.destroy()

    label.bind("<Double-Button-3>", quit_app)

    def refresh():
        label.config(text=status["text"], fg=status["color"])
        root.after(300, refresh)

    def keep_top():
        # เกมชอบแย่ง z-order → ดัน HUD ขึ้นบนสุดซ้ำเรื่อย ๆ
        root.attributes("-topmost", True)
        root.lift()
        root.after(2000, keep_top)

    threading.Thread(target=bot_loop, daemon=True).start()
    refresh()
    keep_top()
    root.mainloop()


if __name__ == "__main__":
    main()
