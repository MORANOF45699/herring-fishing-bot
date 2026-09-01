"""
config.py - ค่าพิกัด/ปุ่ม/เวลา ของ Stone Bot

รองรับทุกจอ 16:9 อัตโนมัติ:
  พิกัดทั้งหมดเก็บเป็น "สัดส่วน" (0.0-1.0) อิงจอ แล้วคูณด้วยขนาดจอจริงตอนรัน
  template (ภาพ) จะถูกย่อ/ขยายตาม SCALE ในตัว detector เอง
  → ใช้ได้กับ 1280x720 / 1920x1080 / 2560x1440 / 3840x2160 โดยไม่ต้องแก้อะไร

ถ้าจอไม่ใช่ 16:9 เป๊ะ หรือพิกัดเพี้ยน → รัน calibrate.py เพื่อบันทึกพิกัดจริง
(calibration.json จะ override ทั้งหมด)
"""

import json
import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*mss.mss is deprecated.*")

import mss

# ===== ตรวจขนาดจอจริง (primary monitor) =====
with mss.mss() as _sct:
    _mon = _sct.monitors[1]
SCREEN_W = _mon["width"]
SCREEN_H = _mon["height"]
SCREEN_LEFT = _mon["left"]
SCREEN_TOP = _mon["top"]

# สเกลเทียบจออ้างอิง 1080p (ใช้ย่อ/ขยาย template + ค่าที่เป็น px)
SCALE = SCREEN_H / 1080.0


def _pt(fx, fy):
    """สัดส่วน (0-1) → พิกัดจอจริง (px)"""
    return (int(SCREEN_LEFT + fx * SCREEN_W), int(SCREEN_TOP + fy * SCREEN_H))


def _region(fl, ft, fw, fh):
    """สัดส่วน (0-1) → region dict สำหรับ mss.grab"""
    return {
        "left": int(SCREEN_LEFT + fl * SCREEN_W),
        "top": int(SCREEN_TOP + ft * SCREEN_H),
        "width": int(fw * SCREEN_W),
        "height": int(fh * SCREEN_H),
    }


# ===== บริเวณตัวเลข Stone บน HUD (ล่างกลางจอ) =====
# อ้างอิง 1920x1080: left=850 top=970 w=175 h=30
COUNTER_REGION = _region(850 / 1920, 970 / 1080, 175 / 1920, 30 / 1080)

# ===== พิกัดคลิก (สัดส่วนอิง 1920x1080) =====
BTN_OPEN_TRUNK = _pt(1212 / 1920, 752 / 1080)   # ปุ่ม "เปิดหลังรถ"
DROP_POINT = _pt(1440 / 1920, 520 / 1080)        # จุดปล่อยของ ฝั่ง SECONDARY
# ขนาดช่องไอเทม (อ้างอิง 1920x1080) — ใช้คำนวณจุดปล่อยสำรอง
SLOT_W = 117 / 1920
SLOT_H = 117 / 1080
DEPOSIT_RETRIES = 4     # ลากฝากไม่ติด ลองจุดปล่อยอื่นได้กี่ครั้ง (ในหน้าต่างเดิม)


def drop_candidates():
    """
    จุดปล่อยของ เรียงตามลำดับที่จะลอง
    ครั้งแรกช่องว่าง ลากลงได้ แต่รอบต่อไปช่องนั้นมีของแล้ว → ต้องมีช่องสำรอง
    """
    dx = int(SLOT_W * SCREEN_W)
    dy = int(SLOT_H * SCREEN_H)
    x, y = DROP_POINT
    return [
        (x, y),
        (x + dx, y),
        (x + 2 * dx, y),
        (x, y + dy),
        (x + dx, y + dy),
        (x + 2 * dx, y + dy),
    ]

BTN_MAX = _pt(1102 / 1920, 559 / 1080)           # ปุ่ม Max ใน dialog
BTN_CONFIRM = _pt(920 / 1920, 618 / 1080)        # ปุ่ม O (ยืนยัน)

# ===== บริเวณค้นหาช่อง Stone ใน INVENTORY (ฝั่งซ้าย) =====
# อ้างอิง 1920x1080: left=140 top=270 w=730 h=520
INVENTORY_REGION = _region(140 / 1920, 270 / 1080, 730 / 1920, 520 / 1080)
STONE_TEMPLATE = os.path.join(os.path.dirname(__file__), "stone_template.png")
TEMPLATE_MATCH_THRESHOLD = 0.70
INV_SCROLL_RETRIES = 4       # หาช่อง Stone ไม่เจอ → เลื่อนขึ้นแล้วหาใหม่ได้กี่รอบ

# ===== เกณฑ์ตัดสินว่าเต็ม 100/100 (ต้องผ่านทั้งสองข้อ) =====
FULL_TEMPLATE = os.path.join(os.path.dirname(__file__), "full_template.png")
FULL_MATCH_THRESHOLD = 0.80              # template matching mask "100/100"
FULL_TEXT_MIN_WIDTH = int(59 * SCALE)    # ความกว้างข้อความ px (สเกลตามจอ)

# ===== ตรวจว่าแผนที่/เมนู pause เปิดค้างไหม (กัน ESC พลาดไปเปิดแผนที่) =====
# region ครอบโลโก้ "FiveM" + แถบแท็บ ด้านบนซ้าย (โผล่เฉพาะตอนเมนูเปิด)
# อ้างอิง 1920x1080: left=300 top=115 w=380 h=120
MAP_CHECK_REGION = _region(300 / 1920, 115 / 1080, 380 / 1920, 120 / 1080)
MAP_TEMPLATE = os.path.join(os.path.dirname(__file__), "map_template.png")
MAP_MATCH_THRESHOLD = 0.65

# ===== ตรวจว่าหน้าท้ายรถ (INVENTORY/SECONDARY) เปิดจริงหลังกด L =====
# region ครอบหัวข้อ "INVENTORY" ด้านบนซ้ายของหน้าต่าง
# อ้างอิง 1920x1080: left=370 top=180 w=250 h=90
GARAGE_CHECK_REGION = _region(370 / 1920, 180 / 1080, 250 / 1920, 90 / 1080)
GARAGE_TEMPLATE = os.path.join(os.path.dirname(__file__), "garage_template.png")
GARAGE_MATCH_THRESHOLD = 0.70
GARAGE_OPEN_RETRIES = 3      # กด L ซ้ำได้กี่ครั้งถ้าเมนูยังไม่เปิด

# ===== โหมดเมื่อของเต็ม 100/100 =====
# "trunk"   = ฝากเข้าท้ายรถ (กด L → ลากของ → Max → O)
# "discard" = ทิ้งของ (กด T เปิดกระเป๋า → คลิกขวาช่องของ → Delete → Max → O)
DEPOSIT_MODE = "discard"

# โหมด trunk: ถ้าท้ายรถเต็ม (ฝากไม่ลง) ให้ทิ้งของแทน แล้วฟาร์มต่อ
# ปิดตัวนี้ = ฝากไม่ได้ก็ยกเลิกรอบ รอผู้ใช้มาเคลียร์ท้ายรถเอง
DISCARD_WHEN_TRUNK_FULL = True

# เจอว่าท้ายรถเต็มแล้ว จำไว้กี่วินาที ระหว่างนี้ข้ามการฝากไปทิ้งเลย
# ไม่ต้องเสียเวลาเปิดท้ายรถลากของทุกรอบ (ครบเวลาแล้วจะกลับไปลองฝากใหม่
# เผื่อผู้ใช้เอาของออกจากท้ายรถแล้ว)
TRUNK_FULL_MEMORY = 600      # วินาที (10 นาที)
DEPOSIT_ATTEMPTS_BEFORE_DISCARD = 2   # ลากไม่ลงกี่ครั้งถึงสรุปว่าท้ายรถเต็ม

# --- ค่าเฉพาะโหมด discard ---
# บริเวณช่องของในกระเป๋าส่วนตัว (หน้า INVENTORY กลางจอ หลังกด T)
# อ้างอิง 1920x1080: left=610 top=270 w=700 h=510
BAG_REGION = _region(610 / 1920, 270 / 1080, 700 / 1920, 510 / 1080)
# ปุ่ม "Delete" ในเมนูคลิกขวา = จุดคลิกขวา + offset (px อ้างอิง 1080p คูณ SCALE)
DELETE_OFFSET = (int(60 * SCALE), int(72 * SCALE))
BAG_OPEN_DELAY = 2.5    # รอหน้ากระเป๋าเปิดหลังกด T
MENU_OPEN_DELAY = 0.8   # รอเมนูคลิกขวา (Use/Give/Delete) เด้ง
BAG_OPEN_RETRIES = 5    # กด T ซ้ำได้กี่ครั้งถ้ากระเป๋ายังไม่เปิด
# region ครอบหัวข้อ "INVENTORY" ของหน้ากระเป๋า (กลางจอ) — ใช้ garage_template.png เดิม
# อ้างอิง 1920x1080: left=840 top=180 w=250 h=90
BAG_CHECK_REGION = _region(840 / 1920, 180 / 1080, 250 / 1920, 90 / 1080)

# ===== ก่อนเปิดกระเป๋า/ท้ายรถ =====
# ของเต็มแล้วตัวละครอาจยังค้างอยู่ในแอนิเมชันฟาร์ม → กด X ยกเลิกก่อน 1 ครั้ง
# ไม่งั้นกด L/T แล้วหน้าต่างไม่เปิด
CANCEL_BEFORE_OPEN = True
CANCEL_KEY_DELAY = 1.0      # รอหลังกด X ก่อนกด L/T
CANCEL_REPEAT_GUARD = 10.0  # กด X ไปแล้วภายในกี่วิ ไม่ต้องกดซ้ำ

# ===== เวลา (วินาที) — เมนูเกมเปิดช้า ปรับเพิ่ม/ลดตรงนี้ =====
CHECK_INTERVAL = 2.0        # อ่าน counter ทุกกี่วินาทีระหว่างฟาร์ม
FULL_DETECTED_DELAY = 3.0   # เจอเต็ม 100 แล้วรอกี่วิ ก่อนเริ่มกด L
GARAGE_OPEN_DELAY = 3.0     # รอหน้า GARAGE เปิดหลังกด L
TRUNK_OPEN_DELAY = 3.0      # รอหน้า INVENTORY/SECONDARY เปิดหลังคลิก "เปิดหลังรถ"
DIALOG_OPEN_DELAY = 1.5     # รอ dialog "นำเข้าท้ายรถ" เด้งหลังลากไอเทม
CLICK_DELAY = 0.8           # ดีเลย์ระหว่างคลิกแต่ละจุด (Max → O)
DRAG_DURATION = 0.8         # เวลาลากไอเทม
AFTER_DEPOSIT_DELAY = 2.0   # รอหลังยืนยันฝากของ ก่อนกด ESC
AFTER_CLOSE_DELAY = 1.5     # รอหลังกด ESC ก่อนเช็ค counter / กด G

# ===== ตรวจว่า dialog "นำเข้าท้ายรถ" (Min/Max/O) เด้งจริงหลังลากไอเทม =====
# ไม่มีไฟล์ template → ข้ามการเช็ค (ทำงานได้เหมือนเดิม)
# อ้างอิง 1920x1080: left=780 top=430 w=380 h=220
DIALOG_CHECK_REGION = _region(780 / 1920, 430 / 1080, 380 / 1920, 220 / 1080)
DIALOG_TEMPLATE = os.path.join(os.path.dirname(__file__), "dialog_template.png")
DIALOG_MATCH_THRESHOLD = 0.60

# ===== กินน้ำ (กด 1) และ กินข้าว (กด 2) =====
ENABLE_DRINK = True
DRINK_INTERVAL = int(2.5 * 3600)   # วินาที
AFTER_DRINK_DELAY = 1.5     # รอหลังกด 1 ก่อนทำอย่างอื่นต่อ

ENABLE_EAT = True
EAT_INTERVAL = int(2.5 * 3600)     # วินาที
AFTER_EAT_DELAY = 1.5       # รอหลังกด 2 ก่อนทำอย่างอื่นต่อ

# เช็คว่ากินติดจริง: แถบ "Loading.." สีส้มเหนือ HUD จะขึ้นตอนกำลังกิน
# อ้างอิง 1920x1080: left=830 top=898 w=260 h=26
DRINK_CHECK_REGION = _region(830 / 1920, 898 / 1080, 260 / 1920, 26 / 1080)
DRINK_LOADING_MIN_PX = max(20, int(80 * SCALE * SCALE))   # px สีส้มขั้นต่ำ (สเกลตามพื้นที่จอ)
DRINK_RETRIES = 3           # กด 1 ซ้ำได้กี่ครั้งถ้าแถบไม่ขึ้น
DRINK_CHECK_DELAY = 1.0     # รอแถบขึ้นหลังกด 1

# ===== วิธีจับภาพ =====
# "screen" = จับจากหน้าจอ (mss) — เกมต้องอยู่บนจอ ไม่โดนอะไรทับ (ค่าเดิม ปลอดภัยสุด)
# "window" = จับจากหน้าต่างเกมตรง ๆ (Windows Graphics Capture)
#            เอาหน้าต่างอื่นทับเกมได้ / จอดเกมไว้นอกจอได้
#            *** ย่อ (minimize) ไม่ได้ — Windows หยุด render หน้าต่างที่ย่อ ***
#            ต้องลง: pip install windows-capture
CAPTURE_MODE = "screen"

# จอดหน้าต่างเกมไว้นอกจอระหว่างฟาร์ม (ใช้ได้เฉพาะ CAPTURE_MODE = "window")
# เกมหายจากจอ ใช้เดสก์ท็อปทำอย่างอื่นได้เต็มจอ
# ตอนฝากของบอทจะดึงเกมกลับเข้าจอชั่วคราว (ต้องใช้เมาส์ลาก) แล้วส่งกลับออกไป
PARK_GAME_OFFSCREEN = False

# ===== ทำงานตอนเกมไม่ได้โฟกัส =====
# อ่าน counter จากภาพหน้าจอได้โดยไม่ต้องโฟกัสเกม ขอแค่หน้าต่างเกม "ไม่โดนบัง"
# ตอนของเต็มถึงจะดึงเกมขึ้นมาเพื่อกดปุ่ม/ลากของ แล้วคืนหน้าต่างเดิมให้
RESTORE_FOCUS_AFTER = True   # ฝาก/ทิ้งเสร็จ คืนโฟกัสให้หน้าต่างที่ใช้อยู่ก่อนหน้า

# ===== ภาพ debug ตอนบอทพลาด =====
DEBUG_KEEP_PER_NAME = 5     # เก็บภาพล่าสุดกี่ไฟล์ต่อชนิดปัญหา (0 = ไม่เซฟเลย)

# ===== เช็คฟาร์มค้าง =====
STUCK_TIMEOUT = 10.0        # ตัวเลข counter นิ่งเกินกี่วิ → กด G ย้ำ
COUNTER_DIFF_MIN_PX = max(6, int(20 * SCALE * SCALE))   # px ต่างขั้นต่ำ = เลขเปลี่ยนจริง (สเกลตามจอ)

# ===== ปุ่ม =====
KEY_TOGGLE = "f10"          # เปิด/ปิดบอท
KEY_TOGGLE_HUD = "f11"      # เปิด/ปิด HUD (toggle)


def _load_calibration():
    """โหลด calibration.json ถ้ามี มา override ค่าที่คำนวณจากสัดส่วน"""
    path = os.path.join(os.path.dirname(__file__), "calibration.json")
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    g = globals()
    for key in ("BTN_OPEN_TRUNK", "DROP_POINT", "BTN_MAX", "BTN_CONFIRM"):
        if key in data:
            g[key] = tuple(data[key])
    for key in ("COUNTER_REGION", "INVENTORY_REGION"):
        if key in data:
            g[key] = data[key]


_load_calibration()


def _load_user_config():
    """โหลด user_config.json เพื่อ override ค่ากินข้าว/น้ำ และโหมดฝากของ"""
    path = os.path.join(os.path.dirname(__file__), "user_config.json")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        g = globals()
        
        # Override Boolean flags
        for key in ("ENABLE_DRINK", "ENABLE_EAT"):
            if key in data:
                g[key] = bool(data[key])
        
        # Override intervals (in minutes in JSON, convert to seconds in config)
        if "DRINK_INTERVAL_MIN" in data:
            g["DRINK_INTERVAL"] = int(float(data["DRINK_INTERVAL_MIN"]) * 60)
        if "EAT_INTERVAL_MIN" in data:
            g["EAT_INTERVAL"] = int(float(data["EAT_INTERVAL_MIN"]) * 60)
            
        # Override deposit mode & scan interval
        if "DEPOSIT_MODE" in data:
            g["DEPOSIT_MODE"] = str(data["DEPOSIT_MODE"])
        if "CHECK_INTERVAL" in data:
            g["CHECK_INTERVAL"] = float(data["CHECK_INTERVAL"])

        # วิธีจับภาพ + จอดเกมนอกจอ
        if "CAPTURE_MODE" in data:
            g["CAPTURE_MODE"] = str(data["CAPTURE_MODE"])
        if "PARK_GAME_OFFSCREEN" in data:
            g["PARK_GAME_OFFSCREEN"] = bool(data["PARK_GAME_OFFSCREEN"])
        if "DISCARD_WHEN_TRUNK_FULL" in data:
            g["DISCARD_WHEN_TRUNK_FULL"] = bool(data["DISCARD_WHEN_TRUNK_FULL"])
    except Exception as e:
        print(f"[config] ⚠ ไม่สามารถโหลด user_config.json ได้: {e}")


_load_user_config()

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"จอ: {SCREEN_W}x{SCREEN_H}  SCALE={SCALE:.3f}")
    print(f"COUNTER_REGION   = {COUNTER_REGION}")
    print(f"INVENTORY_REGION = {INVENTORY_REGION}")
    print(f"BTN_OPEN_TRUNK   = {BTN_OPEN_TRUNK}")
    print(f"DROP_POINT       = {DROP_POINT}")
    print(f"BTN_MAX          = {BTN_MAX}")
    print(f"BTN_CONFIRM      = {BTN_CONFIRM}")
    print(f"FULL_TEXT_MIN_WIDTH = {FULL_TEXT_MIN_WIDTH}")
