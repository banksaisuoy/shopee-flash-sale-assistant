"""
Shopee Flash Sale Assistant - ULTIMATE EDITION (v3.0)
======================================================
รวมฟีเจอร์ที่ดีที่สุดจากทุกเวอร์ชัน:
  - Stealth Mode: ซ่อนการตรวจจับบอทด้วย selenium-stealth
  - Multi-OS Alert: เสียงเตือนรองรับ Windows, macOS, Linux
  - Precision Polling: วนลูปกดปุ่มรัวๆ ในระดับมิลลิวินาที (เร็วกว่า Refresh)
  - Auto-Dependency: ตรวจสอบและติดตั้ง Library ที่จำเป็นให้อัตโนมัติ
  - Smart Variant: ระบบเลือกตัวเลือกสินค้าที่เสถียรและแม่นยำ

Requirements:
    pip install selenium webdriver-manager selenium-stealth
"""

import time
import sys
import platform
import subprocess
from datetime import datetime, timedelta

# --- Auto Dependency Check ---
def install_dependencies():
    required = ["selenium", "webdriver-manager", "selenium-stealth"]
    for lib in required:
        try:
            __import__(lib.replace("-", "_"))
        except ImportError:
            print(f"📦 กำลังติดตั้ง {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

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
    ],
    "checkout": [
        "//button[contains(.,'ชำระเงิน') or contains(.,'Checkout')]",
        "//div[contains(@class,'cart-page-footer__checkout')]//button",
    ]
}

# ============================================================
#  Universal Sound Alert
# ============================================================
def alert_beep(times: int = 3):
    os_name = platform.system()
    try:
        if os_name == "Windows":
            import winsound
            for _ in range(times):
                winsound.Beep(1200, 300)
                time.sleep(0.1)
        elif os_name == "Darwin":
            for _ in range(times):
                subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], capture_output=True)
        else:
            print("\a" * times)
    except:
        print("\n🚨 ALERT! (Check Browser)")

# ============================================================
#  Main Bot Class
# ============================================================
class ShopeeUltimateBot:
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
        print("\n🔑 Step 1: กรุณาล็อกอิน Shopee ให้เรียบร้อย (มีเวลา 5 นาที)")
        self.driver.get("https://shopee.co.th/buyer/login")
        wait = WebDriverWait(self.driver, 300)
        wait.until(lambda d: "login" not in d.current_url)
        print("✅ ล็อกอินสำเร็จ!")

    def _check_captcha(self):
        for xpath in SELECTORS["captcha"]:
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                if el.is_displayed():
                    print("\n🚨 ติด CAPTCHA! รีบแก้ด่วน!")
                    alert_beep(5)
                    return True
            except: pass
        return False

    def _click_smart(self, xpaths, label):
        for xpath in xpaths:
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                if el.is_enabled():
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    try: el.click()
                    except: self.driver.execute_script("arguments[0].click();", el)
                    print(f"✅ คลิก {label} สำเร็จ")
                    return True
            except: continue
        return False

    def start_sale_process(self):
        print(f"\n🚀 Step 2: ไปยังหน้าสินค้า: {self.url}")
        self.driver.get(self.url)
        
        if self.fs_time:
            target_dt = datetime.combine(datetime.today(), datetime.strptime(self.fs_time, "%H:%M:%S").time())
            if target_dt < datetime.now(): target_dt += timedelta(days=1)
            
            print(f"🕒 รอเวลา Flash Sale: {self.fs_time}...")
            
            # Phase 1: Waiting
            while (target_dt - datetime.now()).total_seconds() > 10:
                print(f"⏳ เหลือเวลา {(target_dt - datetime.now()).total_seconds():.0f} วินาที...", end="\r")
                time.sleep(1)
            
            # Phase 2: Polling (รัวปุ่ม)
            print("\n🔥 เข้าสู่ช่วงรัวปุ่ม (Precision Polling)...")
            
            # เลือก Variant ล่วงหน้า (ถ้าปุ่มโชว์แล้ว)
            self._select_variants()
            
            # รอจนถึงวินาทีที่ 0.05 ก่อนเริ่มรัว (เพื่อความแม่นยำ)
            while datetime.now() < target_dt - timedelta(milliseconds=50):
                time.sleep(0.001)

            # รัวจนกว่าจะสำเร็จ (Max 15 วิ)
            start_time = time.time()
            while time.time() - start_time < 15:
                self._check_captcha()
                if self._click_smart(SELECTORS["buy_now"], "Buy Now"):
                    break
                # ถ้ายังเลือก variant ไม่ครบ ให้ลองเลือกซ้ำ (กรณีหน้าโหลดไม่ทัน)
                self._select_variants()
                time.sleep(0.01) # กันเครื่องค้าง
        else:
            self._select_variants()
            self._click_smart(SELECTORS["buy_now"], "Buy Now")

    def _select_variants(self):
        for v in self.variants:
            xpath = [x.replace("{text}", v) for x in SELECTORS["variant"]]
            self._click_smart(xpath, f"ตัวเลือก: {v}")

    def finish(self):
        print("\n💳 Step 3: ตรวจสอบหน้า Checkout")
        try:
            WebDriverWait(self.driver, 15).until(EC.url_contains("checkout"))
            alert_beep(3)
            print("="*50)
            print("🎉 มาถึงหน้าชำระเงินแล้ว! กรุณาตรวจสอบและกดสั่งซื้อด้วยตัวเอง")
            print("="*50)
        except:
            print("⚠️ ไม่เข้าหน้า Checkout อัตโนมัติ กรุณาตรวจสอบหน้าจอ")

    def run(self):
        try:
            self.login()
            self.start_sale_process()
            self.finish()
        except KeyboardInterrupt:
            print("\n🛑 หยุดทำงานโดยผู้ใช้")
        finally:
            print("\nโปรแกรมเสร็จสิ้น ปล่อยเบราว์เซอร์ไว้ให้คุณดำเนินการต่อ...")

if __name__ == "__main__":
    print("✨ Shopee Flash Sale Bot - Ultimate Edition ✨")
    p_url = input("🔗 ลิงก์สินค้า: ").strip()
    v_str = input("🎨 ตัวเลือก (เช่น สีดำ,256GB) ถ้าไม่มีให้ Enter: ").strip()
    p_variants = [v.strip() for v in v_str.split(",")] if v_str else []
    p_time = input("⏰ เวลา Flash Sale (HH:MM:SS): ").strip()

    bot = ShopeeUltimateBot(p_url, p_variants, p_time)
    bot.run()
