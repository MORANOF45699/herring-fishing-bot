"""
stone_actions.py - ลำดับการฝากหินเข้าท้ายรถ

ขั้นตอน (ตัวละครต้องยืนใกล้รถ):
  1. กด L → เปิดท้ายรถ (INVENTORY / SECONDARY) เช็คด้วย template หัวข้อ INVENTORY
     ถ้ายังไม่เปิด กด L ซ้ำ (บางทีต้องกดสองครั้ง) ไม่ต้องใช้เมาส์
  2. หา slot Stone แล้วลากไปฝั่ง SECONDARY
  3. คลิก Max → คลิก O (ยืนยัน)
  4. กด ESC ปิดหน้าต่าง
  5. กด G เริ่มออโต้ฟาร์มต่อ
"""

import time

import config
import stone_input as inp
from stone_detector import (find_stone_slot, is_stone_empty, is_garage_open,
                            is_bag_open, is_drinking, is_eating, is_map_open,
                            is_dialog_open, template_available,
                            save_debug_screenshot)


def _recover(sct):
    """กู้สถานะก่อนลองใหม่: แผนที่/เมนูค้าง → ESC, โฟกัสหลุด → ดึงเกมกลับ"""
    if not inp.is_game_focused():
        inp.focus_game()
        return
    if is_map_open(sct):
        print("[กู้] เจอแผนที่/เมนูค้าง → กด ESC ปิด")
        inp.press_esc()
        time.sleep(1.0)
    inp.focus_game()


_last_drink = [time.time()]   # เริ่มนับตั้งแต่เปิดโปรแกรม → กินครั้งแรกหลังครบกำหนด
_last_eat = [time.time()]     # เริ่มนับตั้งแต่เปิดโปรแกรม → กินข้าวครั้งแรกหลังครบกำหนด


def drink_remaining():
    """เหลือกี่วินาทีถึงรอบกินน้ำถัดไป"""
    return max(0.0, config.DRINK_INTERVAL - (time.time() - _last_drink[0]))


def eat_remaining():
    """เหลือกี่วินาทีถึงรอบกินข้าวถัดไป"""
    return max(0.0, config.EAT_INTERVAL - (time.time() - _last_eat[0]))


def _find_slot_with_scroll(sct, region, tag):
    """หา slot ในบริเวณ region — ไม่เจอ: เลื่อนขึ้นบนสุด แล้วไล่เลื่อนลงหาทีละนิด"""
    cx = region["left"] + region["width"] // 2
    cy = region["top"] + region["height"] // 2

    slot = find_stone_slot(sct, region)
    if slot is not None:
        return slot

    print(f"[{tag}] หาช่องไม่เจอ → เลื่อนขึ้นบนสุดแล้วหาใหม่")
    inp.scroll_up(notches=10, x=cx, y=cy)
    time.sleep(0.4)
    slot = find_stone_slot(sct, region)
    if slot is not None:
        return slot

    print(f"[{tag}] ยังไม่เจอ → ไล่เลื่อนลงหาทีละนิด")
    for i in range(1, config.INV_SCROLL_RETRIES + 1):
        inp.scroll_down(notches=2, x=cx, y=cy)
        time.sleep(0.4)
        slot = find_stone_slot(sct, region)
        if slot is not None:
            print(f"[{tag}] เจอหลังเลื่อนลง (ครั้งที่ {i})")
            return slot
    return None


def drink_if_due(sct=None):
    """
    กินน้ำถ้าครบกำหนด — เรียกได้ทุกจังหวะที่กระเป๋า/หน้าต่างไม่เปิด (ฟาร์มอยู่ก็กินได้)
    กด 1 ย้ำ 2 ทีต่อรอบ แล้วเช็คแถบ Loading.. ว่ากินติดจริง — ไม่ขึ้นลองใหม่
    """
    if not config.ENABLE_DRINK:
        return

    now = time.time()
    remaining = config.DRINK_INTERVAL - (now - _last_drink[0])
    if remaining > 0:
        return

    for attempt in range(1, config.DRINK_RETRIES + 1):
        print(f"[น้ำ] ครบกำหนด — กด 1 ย้ำ 2 ที (รอบที่ {attempt})")
        inp.press_1()
        time.sleep(0.3)
        inp.press_1()
        time.sleep(config.DRINK_CHECK_DELAY)
        if sct is None:                # ไม่มี sct → เช็คไม่ได้ กดรอบเดียวพอ
            break
        if is_drinking(sct):
            print("[น้ำ] ✓ แถบ Loading ขึ้น — กินติดแล้ว")
            break
        print("[น้ำ] ⚠ แถบ Loading ไม่ขึ้น — ลองใหม่")

    _last_drink[0] = now
    time.sleep(config.AFTER_DRINK_DELAY)


def eat_if_due(sct=None):
    """
    กินข้าวถ้าครบกำหนด — เรียกได้ทุกจังหวะที่กระเป๋า/หน้าต่างไม่เปิด
    กด 2 ย้ำ 2 ทีต่อรอบ แล้วเช็คแถบ Loading.. ว่ากินติดจริง
    """
    if not config.ENABLE_EAT:
        return

    now = time.time()
    remaining = config.EAT_INTERVAL - (now - _last_eat[0])
    if remaining > 0:
        return

    for attempt in range(1, config.DRINK_RETRIES + 1):
        print(f"[ข้าว] ครบกำหนด — กด 2 ย้ำ 2 ที (รอบที่ {attempt})")
        inp.press_2()
        time.sleep(0.3)
        inp.press_2()
        time.sleep(config.DRINK_CHECK_DELAY)
        if sct is None:
            break
        if is_eating(sct):
            print("[ข้าว] ✓ แถบ Loading ขึ้น — กินติดแล้ว")
            break
        print("[ข้าว] ⚠ แถบ Loading ไม่ขึ้น — ลองใหม่")

    _last_eat[0] = now
    time.sleep(config.AFTER_EAT_DELAY)


def deposit_to_trunk(sct):
    """
    ฝากหินทั้งหมดเข้าท้ายรถ แล้วกลับไปฟาร์ม
    Returns: True ถ้าสำเร็จ
    """
    if not inp.focus_game():
        save_debug_screenshot(sct, "no_focus")
        print("[ฝาก] ✗ เกมไม่ได้อยู่หน้าจอ — ข้ามรอบนี้ (ไม่กดปุ่มมั่ว)")
        return False

    # Step 1: กด L เปิดท้ายรถ + ยืนยันว่าเปิดจริง (กด L ซ้ำถ้ายังไม่ขึ้น)
    check_garage = template_available(config.GARAGE_TEMPLATE)
    if not check_garage:
        print("[ฝาก] (ข้ามการยืนยันหน้าท้ายรถ — ยังไม่มี garage_template.png)")

    opened = False
    for attempt in range(1, config.GARAGE_OPEN_RETRIES + 1):
        print(f"[ฝาก] กด L เปิดท้ายรถ (ครั้งที่ {attempt})...")
        inp.press_l()
        time.sleep(config.TRUNK_OPEN_DELAY)
        if not check_garage:          # ไม่มี template → เชื่อว่าเปิดแล้ว เดินหน้าต่อ
            opened = True
            break
        if is_garage_open(sct):
            print("[ฝาก] ✓ หน้าท้ายรถเปิดแล้ว")
            opened = True
            break
        print("[ฝาก] ⚠ หน้าท้ายรถยังไม่เปิด — กู้สถานะแล้วลองกด L ใหม่")
        _recover(sct)

    if not opened:
        save_debug_screenshot(sct, "garage_not_open")
        print("[ฝาก] ✗ เปิดท้ายรถไม่ได้ — ยกเลิกรอบนี้")
        inp.press_esc()
        return False

    # Step 2-3: ลากไอเทม → dialog → Max → O
    # รอบแรกช่องปลายทางว่าง ลากลงได้ แต่รอบต่อไปช่องนั้นมีของแล้ว ลากไม่ลง
    # → วนลองจุดปล่อยสำรองในหน้าต่างเดิม ไม่ต้องปิดเปิดท้ายรถใหม่
    check_dialog = template_available(config.DIALOG_TEMPLATE)
    if not check_dialog:
        print("[ฝาก] (ข้ามการยืนยัน dialog — ยังไม่มี dialog_template.png)")

    candidates = config.drop_candidates()
    for attempt in range(1, config.DEPOSIT_RETRIES + 1):
        slot = _find_slot_with_scroll(sct, config.INVENTORY_REGION, "ฝาก")
        if slot is None:
            save_debug_screenshot(sct, "no_stone_slot")
            print("[ฝาก] ✗ หาช่องไอเทมไม่เจอ (เลื่อนหาแล้วก็ไม่เจอ) — ปิดหน้าต่าง")
            inp.press_esc()
            return False

        drop = candidates[(attempt - 1) % len(candidates)]
        print(f"[ฝาก] ลากไอเทม {slot} → {drop} (ครั้งที่ {attempt}/{config.DEPOSIT_RETRIES})")
        inp.drag(*slot, *drop, duration=config.DRAG_DURATION)
        time.sleep(config.DIALOG_OPEN_DELAY)

        if check_dialog and not is_dialog_open(sct):
            print("[ฝาก] ⚠ dialog ไม่เด้ง (ช่องปลายทางน่าจะมีของอยู่) — ลองจุดปล่อยถัดไป")
            continue

        print("[ฝาก] คลิก Max...")
        inp.click(*config.BTN_MAX)
        time.sleep(config.CLICK_DELAY)
        print("[ฝาก] คลิกยืนยัน O...")
        inp.click(*config.BTN_CONFIRM)
        time.sleep(config.AFTER_DEPOSIT_DELAY)

        # counter บน HUD ยังเห็นได้ทั้งที่หน้าต่างเปิดอยู่ → เช็คได้เลย
        if is_stone_empty(sct):
            break
        print("[ฝาก] ⚠ counter ยังไม่ลด — ลองจุดปล่อยถัดไป")
    else:
        save_debug_screenshot(sct, "deposit_failed")
        print("[ฝาก] ✗ ลากฝากไม่สำเร็จทุกจุดปล่อย — ปิดหน้าต่าง")
        inp.press_esc()
        return False

    # Step 4: ปิดหน้าต่าง
    print("[ฝาก] กด ESC ปิดหน้าต่าง")
    inp.press_esc()
    time.sleep(config.AFTER_CLOSE_DELAY)

    # ตรวจว่า counter กลับเป็น 0/100 จริง
    if not is_stone_empty(sct):
        save_debug_screenshot(sct, "deposit_not_empty")
        print("[ฝาก] ⚠ counter ยังไม่เป็น 0 — ฝากอาจไม่สำเร็จ")
        return False

    # Step 5: ฟาร์มต่อ
    print("[ฝาก] ✓ ฝากสำเร็จ — กด G ฟาร์มต่อ")
    inp.press_g()
    return True


def discard_items(sct):
    """
    ทิ้งของทั้งหมด (โหมด discard) แล้วกลับไปฟาร์ม
    Flow: กด T เปิดกระเป๋า → คลิกขวาช่องของ → Delete → Max → O → ESC → G
    Returns: True ถ้าสำเร็จ
    """
    if not inp.focus_game():
        save_debug_screenshot(sct, "no_focus")
        print("[ทิ้ง] ✗ เกมไม่ได้อยู่หน้าจอ — ข้ามรอบนี้ (ไม่กดปุ่มมั่ว)")
        return False

    # Step 1: กด T เปิดกระเป๋า + ยืนยันว่าเปิดจริง (กด T ซ้ำถ้ายังไม่ขึ้น)
    check_bag = template_available(config.GARAGE_TEMPLATE)
    if not check_bag:
        print("[ทิ้ง] (ข้ามการยืนยันหน้ากระเป๋า — ยังไม่มี garage_template.png)")

    opened = False
    for attempt in range(1, config.BAG_OPEN_RETRIES + 1):
        print(f"[ทิ้ง] กด T เปิดกระเป๋า (ครั้งที่ {attempt})...")
        inp.press_t()
        time.sleep(config.BAG_OPEN_DELAY)
        if not check_bag:             # ไม่มี template → เชื่อว่าเปิดแล้ว เดินหน้าต่อ
            opened = True
            break
        if is_bag_open(sct):
            print("[ทิ้ง] ✓ หน้ากระเป๋าเปิดแล้ว")
            opened = True
            break
        print("[ทิ้ง] ⚠ หน้ากระเป๋ายังไม่เปิด — กู้สถานะแล้วลองกด T ใหม่")
        _recover(sct)

    if not opened:
        save_debug_screenshot(sct, "bag_not_open")
        print("[ทิ้ง] ✗ เปิดกระเป๋าไม่ได้ — ยกเลิกรอบนี้")
        inp.press_esc()
        return False

    # Step 2: หาช่องของในกระเป๋า (เลื่อนขึ้นบนสุด แล้วไล่เลื่อนลงถ้ายังไม่เจอ)
    slot = _find_slot_with_scroll(sct, config.BAG_REGION, "ทิ้ง")

    if slot is None:
        save_debug_screenshot(sct, "no_stone_slot_bag")
        print("[ทิ้ง] ✗ หาช่องของไม่เจอ — ปิดหน้าต่าง")
        inp.press_esc()
        return False

    # Step 3: คลิกขวา → คลิก Delete
    print(f"[ทิ้ง] คลิกขวาช่องของ {slot}")
    inp.right_click(*slot)
    time.sleep(config.MENU_OPEN_DELAY)
    dx, dy = config.DELETE_OFFSET
    del_pt = (slot[0] + dx, slot[1] + dy)
    print(f"[ทิ้ง] คลิก Delete ที่ {del_pt}")
    inp.click(*del_pt)
    time.sleep(config.DIALOG_OPEN_DELAY)

    # Step 4: Max → ยืนยัน O
    print("[ทิ้ง] คลิก Max...")
    inp.click(*config.BTN_MAX)
    time.sleep(config.CLICK_DELAY)
    print("[ทิ้ง] คลิกยืนยัน O...")
    inp.click(*config.BTN_CONFIRM)
    time.sleep(config.AFTER_DEPOSIT_DELAY)

    # Step 5: ปิดหน้าต่าง
    print("[ทิ้ง] กด ESC ปิดหน้าต่าง")
    inp.press_esc()
    time.sleep(config.AFTER_CLOSE_DELAY)

    # ตรวจว่า counter กลับเป็น 0/100 จริง
    if not is_stone_empty(sct):
        save_debug_screenshot(sct, "discard_not_empty")
        print("[ทิ้ง] ⚠ counter ยังไม่เป็น 0 — ทิ้งอาจไม่สำเร็จ")
        return False

    # Step 6: ฟาร์มต่อ
    print("[ทิ้ง] ✓ ทิ้งสำเร็จ — กด G ฟาร์มต่อ")
    inp.press_g()
    return True
