"""
Shopee Flash Sale Assistant - v3 Final (The Perfect Edition)
======================================================
แก้ไข Bug จาก v3:
  - Fixed Dependency Check: ตรวจสอบ webdriver_manager ถูกต้อง
  - Smart Variant Locking: เลือกตัวเลือกก่อนเริ่มรัวปุ่ม ป้องกันการ Toggle off
  - Captcha Interruption: หยุดรอเมื่อติด Captcha และแจ้งเตือนผู้ใช้
  - Robust Error Handling: ปรับปรุงการจัดการ Exception เพื่อการ Debug
"""

import time
import sys
import platform
import subprocess
import importlib.util
from datetime import datetime, timedelta

# --- Improved Dependency Check ---
def install_dependencies():
    libs = {
        "selenium": "selenium",
        "webdriver_manager": "webdriver-manager",
        "selenium_stealth": "selenium-stealth"
    }
    for module_name, package_name in libs.items():
        if importlib.util.find_spec(module_name) is None:
            print(f"📦 กำลังติดตั้ง {package_name}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

install_dependencies()

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    StaleElementReferenceException, ElementClickInterceptedException
)
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

# ============================================================
#  Configuration & Selectors
# ============================================================
SELECTORS = {
    "buy_now": [
        "//button[not(@disabled) and (contains(.,'ซื้อสินค้า') or contains(.,'Buy Now'))]",
        "//button[contains(@class,'shopee-button-solid--primary')]",
        "//button[contains(@class,'btn-solid-primary')]",
    ],
    "variant": [
        "//*[contains(@class,'product-variation') and normalize-space(.)='{text}' and not(contains(@class,'disabled'))]",
        "//button[normalize-space(.)='{text}' and not(@disabled)]",
    ],
    "captcha": [
        "//*[contains(@class,'captcha') or contains(@class,'slider')]",
        "//*[contains(text(),'Verify') or contains(text(),'ยืนยัน') or contains(text(),'เลื่อน')]",
    ]
}

def alert_beep(times: int = 3):
    os_name = platform.system()
    try:
        if os_name == "Windows":
            import winsound
            for _ in range(times):
                winsound.Beep(1200, 300)
                time.sleep(0.1)
        else:
            print("\a" * times)
    except Exception:
        print("\n🚨 ALERT! (Check Browser)")

class ShopeeFinalBot:
    def __init__(self, url: str, variants: list = None, fs_time: str = ""):
        self.url = url
        self.variants = variants if variants else []
        self.fs_time = fs_time
        self.driver = self._setup_driver()

    def _setup_driver(self):
        opts = Options()
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
        
        stealth(driver,
            languages=["th-TH", "th", "en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        return driver

    def login(self):
        print("\n🔑 Step 1: ล็อกอิน Shopee (5 นาที)")
        self.driver.get("https://shopee.co.th/buyer/login")
        try:
            WebDriverWait(self.driver, 300).until(lambda d: "login" not in d.current_url)
            print("✅ ล็อกอินสำเร็จ!")
        except TimeoutException:
            print("❌ หมดเวลาล็อกอิน")
            sys.exit()

    def _wait_until_captcha_gone(self):
        print("\n🚨 ติด CAPTCHA! กรุณาแก้ในเบราว์เซอร์...")
        alert_beep(5)
        while True:
            is_captcha = False
            for xpath in SELECTORS["captcha"]:
                try:
                    if self.driver.find_element(By.XPATH, xpath).is_displayed():
                        is_captcha = True
                        break
                except Exception: pass
            if not is_captcha:
                print("✅ CAPTCHA หายไปแล้ว ทำงานต่อ...")
                break
            time.sleep(1)

    def _click_smart(self, xpaths, label):
        for xpath in xpaths:
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                if el.is_enabled():
                    try: el.click()
                    except: self.driver.execute_script("arguments[0].click();", el)
                    print(f"✅ คลิก {label} สำเร็จ")
                    return True
            except Exception: continue
        return False

    def _select_variants(self):
        for v in self.variants:
            xpath = [x.replace("{text}", v) for x in SELECTORS["variant"]]
            self._click_smart(xpath, f"ตัวเลือก: {v}")

    def start_sale_process(self):
        print(f"\n🚀 Step 2: หน้าสินค้า: {self.url}")
        self.driver.get(self.url)
        
        if self.fs_time:
            target_dt = datetime.combine(datetime.today(), datetime.strptime(self.fs_time, "%H:%M:%S").time())
            if target_dt < datetime.now(): target_dt += timedelta(days=1)
            
            print(f"🕒 รอเวลา Flash Sale: {self.fs_time}...")
            while (target_dt - datetime.now()).total_seconds() > 5:
                time.sleep(1)
            
            # เลือก Variant ก่อนเริ่มรัว (ป้องกัน Toggle Off)
            print("\n🎨 กำลังเลือกตัวเลือกสินค้าล่วงหน้า...")
            self._select_variants()
            
            print("🔥 เข้าสู่ช่วงรัวปุ่ม (Precision Polling)...")
            while datetime.now() < target_dt:
                time.sleep(0.001)

            start_time = time.time()
            while time.time() - start_time < 20: # เพิ่มเป็น 20 วิ
                # เช็ค Captcha และหยุดรอถ้าเจอ
                for xpath in SELECTORS["captcha"]:
                    try:
                        if self.driver.find_element(By.XPATH, xpath).is_displayed():
                            self._wait_until_captcha_gone()
                    except Exception: pass

                if self._click_smart(SELECTORS["buy_now"], "Buy Now"):
                    return True
                time.sleep(0.01)
        else:
            self._select_variants()
            return self._click_smart(SELECTORS["buy_now"], "Buy Now")
        return False

    def finish(self):
        print("\n💳 Step 3: หน้า Checkout")
        try:
            WebDriverWait(self.driver, 15).until(EC.url_contains("checkout"))
            alert_beep(3)
            print("🎉 มาถึงหน้าชำระเงินแล้ว! กรุณากดสั่งซื้อด้วยตัวเอง")
        except Exception:
            print("⚠️ ไม่เข้าหน้า Checkout อัตโนมัติ กรุณาตรวจสอบ")

    def run(self):
        try:
            self.login()
            if self.start_sale_process():
                self.finish()
            else:
                print("❌ กดซื้อไม่สำเร็จ")
        except KeyboardInterrupt:
            print("\n🛑 หยุดโดยผู้ใช้")
        finally:
            print("\nโปรแกรมเสร็จสิ้น...")

if __name__ == "__main__":
    print("✨ Shopee Flash Sale Bot - v3 Final ✨")
    p_url = input("🔗 ลิงก์สินค้า: ").strip()
    v_str = input("🎨 ตัวเลือก (เช่น สีดำ,256GB) ถ้าไม่มีให้ Enter: ").strip()
    p_variants = [v.strip() for v in v_str.split(",")] if v_str else []
    p_time = input("⏰ เวลา Flash Sale (HH:MM:SS): ").strip()

    bot = ShopeeFinalBot(p_url, p_variants, p_time)
    bot.run()
