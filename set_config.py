# -*- coding: utf-8 -*-
import json
import os
import sys

# ให้แสดงผลภาษาไทยในคอนโซลถูกต้อง
sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "user_config.json")

# ค่าเริ่มต้นเริ่มต้น
defaults = {
    "ENABLE_DRINK": True,
    "DRINK_INTERVAL_MIN": 150.0,
    "ENABLE_EAT": True,
    "EAT_INTERVAL_MIN": 150.0,
    "DEPOSIT_MODE": "discard",
    "CHECK_INTERVAL": 2.0
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_conf = json.load(f)
                # รวมค่าที่โหลดเข้ากับ defaults เผื่อมีบางค่าหายไป
                merged = defaults.copy()
                for k, v in user_conf.items():
                    merged[k] = v
                return merged
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการโหลดไฟล์ตั้งค่าเดิม: {e}")
    return defaults.copy()


def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("\n[✓] บันทึกการตั้งค่าลงใน user_config.json เรียบร้อยแล้ว!")
        return True
    except Exception as e:
        print(f"\n[✗] เกิดข้อผิดพลาดในการบันทึกไฟล์: {e}")
        return False


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def main():
    config = load_config()

    while True:
        clear_screen()
        print("=" * 60)
        print("         🤖  Item Farming Bot Configurator (ตั้งค่าบอท)  🤖")
        print("=" * 60)
        
        drink_enable_str = "เปิด (ON)" if config["ENABLE_DRINK"] else "ปิด (OFF)"
        eat_enable_str = "เปิด (ON)" if config["ENABLE_EAT"] else "ปิด (OFF)"
        
        mode_str = "ทิ้งของ (discard)" if config["DEPOSIT_MODE"] == "discard" else "ฝากท้ายรถ (trunk)"
        
        print(f"  [1] ระบบกินน้ำ (ปุ่ม 1)       : {drink_enable_str}")
        print(f"  [2] เวลากินน้ำ (นาที)         : {config['DRINK_INTERVAL_MIN']:.1f} นาที")
        print(f"  [3] ระบบกินข้าว (ปุ่ม 2)       : {eat_enable_str}")
        print(f"  [4] เวลากินข้าว (นาที)         : {config['EAT_INTERVAL_MIN']:.1f} นาที")
        print(f"  [5] โหมดเมื่อของเต็ม          : {mode_str}")
        print(f"  [6] ความถี่ในการสแกนภาพ (วิ)   : {config['CHECK_INTERVAL']:.1f} วินาที")
        print("-" * 60)
        print("  [7] บันทึกและออก (Save & Exit)")
        print("  [8] ยกเลิกและออก (Exit without saving)")
        print("=" * 60)

        choice = input("กรุณาเลือกเมนู (1-8): ").strip()

        if choice == "1":
            config["ENABLE_DRINK"] = not config["ENABLE_DRINK"]
        elif choice == "2":
            try:
                val = input(f"ใส่เวลากินน้ำใหม่ (นาที) [เดิม {config['DRINK_INTERVAL_MIN']:.1f}]: ").strip()
                if val:
                    config["DRINK_INTERVAL_MIN"] = float(val)
            except ValueError:
                input("ค่าไม่ถูกต้อง! กรุณาใส่ตัวเลขเท่านั้น (กด Enter เพื่อลองใหม่)")
        elif choice == "3":
            config["ENABLE_EAT"] = not config["ENABLE_EAT"]
        elif choice == "4":
            try:
                val = input(f"ใส่เวลากินข้าวใหม่ (นาที) [เดิม {config['EAT_INTERVAL_MIN']:.1f}]: ").strip()
                if val:
                    config["EAT_INTERVAL_MIN"] = float(val)
            except ValueError:
                input("ค่าไม่ถูกต้อง! กรุณาใส่ตัวเลขเท่านั้น (กด Enter เพื่อลองใหม่)")
        elif choice == "5":
            if config["DEPOSIT_MODE"] == "discard":
                config["DEPOSIT_MODE"] = "trunk"
            else:
                config["DEPOSIT_MODE"] = "discard"
        elif choice == "6":
            try:
                val = input(f"ใส่ความถี่การสแกนใหม่ (วินาที) [เดิม {config['CHECK_INTERVAL']:.1f}]: ").strip()
                if val:
                    config["CHECK_INTERVAL"] = float(val)
            except ValueError:
                input("ค่าไม่ถูกต้อง! กรุณาใส่ตัวเลขเท่านั้น (กด Enter เพื่อลองใหม่)")
        elif choice == "7":
            if save_config(config):
                input("\nกด Enter เพื่อปิดหน้าต่าง...")
                break
        elif choice == "8":
            print("\nยกเลิกการตั้งค่า")
            break
        else:
            input("เลือกเมนูไม่ถูกต้อง! (กด Enter เพื่อลองใหม่)")


if __name__ == "__main__":
    main()
