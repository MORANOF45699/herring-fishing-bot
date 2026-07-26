"""
stone_main.py - บอทเก็บไอเทมอัตโนมัติ (FiveM Item Farming Bot)
ใช้ได้กับทุกไอเทม/ทุกความจุ (40/60/100 ฯลฯ) — แค่ calibrate template ให้ตรง

วิธีใช้:
  1. รัน: python stone_main.py
  2. สลับไปหน้าเกม แล้วกด F10 เพื่อเริ่ม (บอทจะกด G เริ่มออโต้ฟาร์มให้)
  3. กด F10 อีกครั้งเพื่อหยุดชั่วคราว / Esc ในคอนโซลเพื่อปิดโปรแกรม

Flow:
  ออโต้ฟาร์ม (G) → อ่านเลขไอเทมจาก HUD ทุก 2 วิ → เต็มความจุ →
  โหมด trunk:   กด L เปิดท้ายรถ → ลากไอเทม → Max → O → ESC → G → วนต่อ
  โหมด discard: กด T เปิดกระเป๋า → คลิกขวา → Delete → Max → O → ESC → G → วนต่อ
"""

import sys
import time

import keyboard
import mss

sys.stdout.reconfigure(encoding='utf-8')

import config
import stone_input as inp
from stone_detector import full_match_score, full_min_width, is_map_open, counter_changed
from stone_actions import (deposit_to_trunk, discard_items, drink_if_due,
                           drink_remaining)

MAX_DEPOSIT_FAILS = 2  # ฝากพลาดติดกันกี่ครั้งถึงหยุดบอท


def print_banner():
    print("=" * 55)
    print("    🤖  FiveM Item Farming Bot (บอทเก็บไอเทม) 🤖    ")
    print("=" * 55)
    print("วิธีใช้งาน:")
    print(f"  - กด [ {config.KEY_TOGGLE.upper()} ] เพื่อ เปิด/ปิด บอท")
    print("  - กด [ Esc ] ในคอนโซลนี้เพื่อปิดโปรแกรม")
    if config.DEPOSIT_MODE == "discard":
        print("โหมด: ทิ้งของ (กด T → คลิกขวา → Delete → Max → O)")
    else:
        print("โหมด: ฝากท้ายรถ — ต้องยืนใกล้รถ (กด L เปิดท้ายรถได้) ตลอดเวลา")
    print(f"  - Check Interval: {config.CHECK_INTERVAL}s")
    print("=" * 55)


def main():
    print_banner()

    state = {"active": False, "last_change": time.time()}

    def toggle():
        state["active"] = not state["active"]
        if state["active"]:
            print("\n[บอท] ▶ เริ่มทำงาน — กด G เริ่มออโต้ฟาร์ม")
            time.sleep(0.3)
            inp.press_g()
            state["last_change"] = time.time()
        else:
            print("\n[บอท] ⏸ หยุดชั่วคราว")

    keyboard.add_hotkey(config.KEY_TOGGLE, toggle)

    deposit_fails = 0

    with mss.mss() as sct:
        while True:
            if keyboard.is_pressed("esc"):
                print("\n[บอท] ปิดโปรแกรม")
                break

            if not state["active"]:
                time.sleep(0.2)
                continue

            # กันเคส ESC พลาดไปเปิดแผนที่/เมนู → ปิดแล้วฟาร์มต่อ
            if is_map_open(sct):
                print("[บอท] ⚠ เจอแผนที่/เมนูเปิดค้าง → กด ESC ปิด แล้วฟาร์มต่อ")
                inp.press_esc()
                time.sleep(1.0)
                inp.press_g()
                time.sleep(1.5)
                continue

            # กินน้ำถ้าครบกำหนด — จังหวะนี้กระเป๋า/หน้าต่างปิดอยู่ (กินระหว่างฟาร์มได้)
            drink_if_due(sct)

            score, width = full_match_score(sct)
            full = score >= config.FULL_MATCH_THRESHOLD and width >= full_min_width()
            mins = drink_remaining() / 60
            print(f"[บอท] score={score:.2f} w={width} {'🔴 เต็ม!' if full else '⏳ ฟาร์มอยู่...'} | 💧 น้ำอีก {int(mins // 60)}:{int(mins % 60):02d} ชม")

            # เช็คฟาร์มค้าง: ตัวเลขนิ่งเกิน STUCK_TIMEOUT → กด G ย้ำ
            if counter_changed(sct):
                state["last_change"] = time.time()
            elif not full and time.time() - state["last_change"] > config.STUCK_TIMEOUT:
                print(f"[บอท] ⚠ counter นิ่งเกิน {config.STUCK_TIMEOUT:.0f} วิ — ฟาร์มอาจค้าง กด G ย้ำ")
                inp.press_g()
                state["last_change"] = time.time()

            if full:
                print(f"\n===== ไอเทมเต็มความจุ → รอ {config.FULL_DETECTED_DELAY} วิ ก่อนจัดการ =====")
                time.sleep(config.FULL_DETECTED_DELAY)
                if config.DEPOSIT_MODE == "discard":
                    ok = discard_items(sct)
                else:
                    ok = deposit_to_trunk(sct)
                state["last_change"] = time.time()   # กันจับค้างผิดหลังฝาก/ทิ้งเสร็จ
                if ok:
                    deposit_fails = 0
                    print("===== ฝากเสร็จ กลับไปฟาร์มต่อ =====\n")
                else:
                    deposit_fails += 1
                    print(f"[บอท] ⚠ ฝากไม่สำเร็จ ({deposit_fails}/{MAX_DEPOSIT_FAILS})")
                    if deposit_fails >= MAX_DEPOSIT_FAILS:
                        print("[บอท] ✗ ฝากพลาดติดกันหลายครั้ง — หยุดบอท (กด F10 เริ่มใหม่)")
                        state["active"] = False
                        deposit_fails = 0
                time.sleep(1.0)

            time.sleep(config.CHECK_INTERVAL)


if __name__ == '__main__':
    main()
