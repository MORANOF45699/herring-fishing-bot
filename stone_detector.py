"""
stone_detector.py - อ่านตัวเลขไอเทมจาก HUD + หาช่องไอเทมใน inventory

หลักการอ่าน counter:
  template matching ภาพตอนเต็ม เช่น "100/100" หรือ "40/40" (full_template.png)
  กับบริเวณตัวเลขบน HUD
  - score สูง = เต็ม
  - score ต่ำ = ยังไม่เต็ม (เลขอื่นรูปร่างไม่เหมือน)
  ความกว้างข้อความขั้นต่ำคำนวณจาก template เอง → รองรับความจุ 40/60/100 ฯลฯ
  (เปลี่ยนความจุ = ถ่าย full_template ใหม่ตอนเลขเต็ม ด้วย calibrate ปุ่ม 8)
  หมายเหตุ: นับ contour ใช้ไม่ได้เพราะฟอนต์เกมตัว "00" ติดกันเป็นก้อนเดียว
"""

import os
import time

import cv2
import numpy as np

import config

DEBUG_DIR = os.path.join(os.path.dirname(__file__), "debug_images")


def _grab(sct, region):
    """จับภาพ region (dict left/top/width/height) → BGR"""
    shot = sct.grab(region)
    img = np.array(shot)
    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


def _orange_mask(bgr):
    """threshold ข้อความสีส้มของ HUD"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    # ส้ม: hue ~10-30, อิ่มตัวสูง, สว่าง
    return cv2.inRange(hsv, (8, 100, 140), (35, 255, 255))


def _scale_template(img):
    """ย่อ/ขยาย template (จับที่ 1080p) ให้ตรงสเกลจอปัจจุบัน"""
    if abs(config.SCALE - 1.0) < 0.01:
        return img
    h, w = img.shape[:2]
    nw, nh = max(1, int(w * config.SCALE)), max(1, int(h * config.SCALE))
    interp = cv2.INTER_AREA if config.SCALE < 1 else cv2.INTER_CUBIC
    return cv2.resize(img, (nw, nh), interpolation=interp)


def count_counter_glyphs(sct, debug=False):
    """
    นับจำนวน glyph ในบริเวณตัวเลข Stone
    Returns: (จำนวน glyph, ภาพ mask)
    """
    bgr = _grab(sct, config.COUNTER_REGION)
    mask = _orange_mask(bgr)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h_region = config.COUNTER_REGION["height"]
    glyphs = 0
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        # กรอง noise: glyph ต้องสูงพอสมควรเทียบกับ region
        if h >= h_region * 0.35 and w >= 2:
            glyphs += 1

    if debug:
        os.makedirs(DEBUG_DIR, exist_ok=True)
        cv2.imwrite(os.path.join(DEBUG_DIR, "counter_raw.png"), bgr)
        cv2.imwrite(os.path.join(DEBUG_DIR, "counter_mask.png"), mask)

    return glyphs, mask


FULL_TEMPLATE = os.path.join(os.path.dirname(__file__), "full_template.png")
_full_template_mask = None
_full_min_width = None


def full_min_width():
    """ความกว้างข้อความขั้นต่ำที่ถือว่าเต็ม (คำนวณจาก template — รองรับทุกความจุ)"""
    return _full_min_width if _full_min_width is not None else config.FULL_TEXT_MIN_WIDTH


def full_match_score(sct, debug=False):
    """
    เทียบบริเวณ counter กับภาพตอนเต็ม (full_template.png)
    match บน mask สีส้ม (ตัดพื้นหลังโปร่งใสของ HUD ทิ้ง)
    Returns: (score 0.0-1.0, ความกว้างข้อความเป็น px)
    """
    global _full_template_mask, _full_min_width
    if _full_template_mask is None:
        tmpl = cv2.imread(FULL_TEMPLATE)
        if tmpl is None:
            raise FileNotFoundError(f"ไม่พบ {FULL_TEMPLATE}")
        _full_template_mask = _orange_mask(_scale_template(tmpl))
        xs = np.where(_full_template_mask.any(axis=0))[0]
        if len(xs):
            _full_min_width = int((xs[-1] - xs[0] + 1) * 0.85)

    bgr = _grab(sct, config.COUNTER_REGION)
    mask = _orange_mask(bgr)

    result = cv2.matchTemplate(mask, _full_template_mask, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)

    # วัดความกว้างข้อความ (เฉพาะ contour ที่สูงพอ = ตัวเลข ไม่ใช่ noise)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours if cv2.boundingRect(c)[3] >= 10]
    width = (max(b[0] + b[2] for b in boxes) - min(b[0] for b in boxes)) if boxes else 0

    if debug:
        os.makedirs(DEBUG_DIR, exist_ok=True)
        cv2.imwrite(os.path.join(DEBUG_DIR, "counter_raw.png"), bgr)
        cv2.imwrite(os.path.join(DEBUG_DIR, "counter_mask.png"), mask)

    return max_val, width


def is_stone_full(sct):
    """ไอเทมเต็มความจุหรือยัง (ต้องผ่านทั้ง score และความกว้าง)"""
    score, width = full_match_score(sct)
    return score >= config.FULL_MATCH_THRESHOLD and width >= full_min_width()


def is_stone_empty(sct):
    """counter ไม่เต็มแล้ว (ใช้ยืนยันว่าฝาก/ทิ้งสำเร็จ)"""
    return not is_stone_full(sct)


def find_stone_slot(sct, region=None):
    """
    หาตำแหน่งช่อง Stone ใน inventory ด้วย template matching
    region: บริเวณค้นหา (default = INVENTORY_REGION ฝั่งท้ายรถ)
    Returns: (x, y) กลางช่อง หรือ None ถ้าไม่เจอ
    """
    if region is None:
        region = config.INVENTORY_REGION
    if not os.path.exists(config.STONE_TEMPLATE):
        print(f"[detector] ⚠ ไม่พบ {config.STONE_TEMPLATE} — รัน calibrate.py ก่อน")
        return None

    template = _scale_template(cv2.imread(config.STONE_TEMPLATE))
    scene = _grab(sct, region)

    result = cv2.matchTemplate(scene, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < config.TEMPLATE_MATCH_THRESHOLD:
        print(f"[detector] ⚠ หาช่องไอเทมไม่เจอ (score={max_val:.2f})")
        return None

    th, tw = template.shape[:2]
    x = region["left"] + max_loc[0] + tw // 2
    y = region["top"] + max_loc[1] + th // 2
    print(f"[detector] เจอช่องไอเทมที่ ({x}, {y}) score={max_val:.2f}")
    return (x, y)


_template_cache = {}   # path -> ภาพ template (scaled) หรือ None ถ้าไม่มีไฟล์


def _screen_has_template(sct, template_path, region, threshold):
    """
    เช็คว่าบริเวณ region บนจอ ตรงกับ template หรือไม่ (คืน True/False)
    ถ้ายังไม่มีไฟล์ template → คืน False (ข้ามฟีเจอร์ ไม่กระทบงานอื่น)
    """
    if template_path not in _template_cache:
        img = cv2.imread(template_path)
        _template_cache[template_path] = _scale_template(img) if img is not None else None
    tmpl = _template_cache[template_path]
    if tmpl is None:
        return False

    scene = _grab(sct, region)
    if tmpl.shape[0] > scene.shape[0] or tmpl.shape[1] > scene.shape[1]:
        return False
    result = cv2.matchTemplate(scene, tmpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    return max_val >= threshold


def template_available(template_path):
    """มีไฟล์ template นี้ให้ใช้ไหม (โหลดเข้า cache ครั้งแรก)"""
    if template_path not in _template_cache:
        img = cv2.imread(template_path)
        _template_cache[template_path] = _scale_template(img) if img is not None else None
    return _template_cache[template_path] is not None


def is_map_open(sct):
    """เมนู pause / แผนที่ เปิดค้างอยู่ไหม (ต้องมี map_template.png จาก calibrate)"""
    return _screen_has_template(sct, config.MAP_TEMPLATE,
                                config.MAP_CHECK_REGION, config.MAP_MATCH_THRESHOLD)


_counter_prev_mask = [None]


def counter_changed(sct):
    """ตัวเลข counter บน HUD เปลี่ยนจากครั้งก่อนไหม (เทียบ mask สีส้ม — ใช้จับฟาร์มค้าง)"""
    mask = _orange_mask(_grab(sct, config.COUNTER_REGION))
    prev = _counter_prev_mask[0]
    _counter_prev_mask[0] = mask
    if prev is None or prev.shape != mask.shape:
        return True
    diff = cv2.absdiff(mask, prev)
    return cv2.countNonZero(diff) > config.COUNTER_DIFF_MIN_PX   # เลขเปลี่ยนจริง ไม่ใช่ noise ขอบตัวอักษร


def is_drinking(sct):
    """แถบ Loading.. (กำลังกินน้ำ) ขึ้นอยู่ไหม — นับ px สีส้มในบริเวณแถบ"""
    mask = _orange_mask(_grab(sct, config.DRINK_CHECK_REGION))
    return cv2.countNonZero(mask) >= config.DRINK_LOADING_MIN_PX


def is_eating(sct):
    """แถบ Loading.. (กำลังกินข้าว) ขึ้นอยู่ไหม — ใช้เงื่อนไขเดียวกับกินน้ำเพราะใช้แถบ Loading เดียวกัน"""
    return is_drinking(sct)


def is_bag_open(sct):
    """หน้ากระเป๋าส่วนตัว (กด T) เปิดอยู่ไหม (ใช้ template หัวข้อ INVENTORY เดิม)"""
    return _screen_has_template(sct, config.GARAGE_TEMPLATE,
                                config.BAG_CHECK_REGION, config.GARAGE_MATCH_THRESHOLD)


def is_garage_open(sct):
    """หน้า GARAGE (เมนูรถ) เปิดอยู่ไหม (ต้องมี garage_template.png จาก calibrate)"""
    return _screen_has_template(sct, config.GARAGE_TEMPLATE,
                                config.GARAGE_CHECK_REGION, config.GARAGE_MATCH_THRESHOLD)


def save_debug_screenshot(sct, name):
    """save ภาพเต็มจอไว้ดูตอนบอทพัง"""
    os.makedirs(DEBUG_DIR, exist_ok=True)
    monitor = sct.monitors[1]
    bgr = _grab(sct, monitor)
    path = os.path.join(DEBUG_DIR, f"{name}_{int(time.time())}.png")
    cv2.imwrite(path, bgr)
    print(f"[detector] บันทึก debug: {path}")


if __name__ == '__main__':
    import mss
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("=== ทดสอบอ่าน Stone counter (Ctrl+C เพื่อหยุด) ===")
    with mss.mss() as sct:
        while True:
            score, width = full_match_score(sct, debug=True)
            full = score >= config.FULL_MATCH_THRESHOLD and width >= config.FULL_TEXT_MIN_WIDTH
            print(f"score={score:.3f} width={width}px {'🔴 เต็ม!' if full else '⏳ ยังไม่เต็ม'}")
            time.sleep(1)
