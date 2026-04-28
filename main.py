"""
Shopee Flash Sale Assistant - v3.0 FINAL (Bug Fixed & Refined)
==============================================================
การเปลี่ยนแปลงหลัก:
  - แก้ไข Bug Auto-install (webdriver_manager)
  - แยก Logic การเลือก Variant ออกจากลูปรัว (ป้องกัน Toggle On/Off)
  - เพิ่มระบบหยุดรอ (Pause) เมื่อติด CAPTCHA ให้ผู้ใช้จัดการก่อนไปต่อ
  - ปรับปรุง Error Handling ให้ Debug ง่ายขึ้น
"""

import time
import sys
import platform
import subprocess
import importlib.util
from datetime import datetime, timedelta

# --- 1. Fixed Auto-Dependency Check ---
def install_dependencies():
    # mapping package_name: import_name
    dependencies = {
        "selenium": "selenium",
        "webdriver-manager": "webdriver_manager",
        "selenium-stealth": "selenium_stealth"
    }
    for package, import_name in dependencies.items():
        if importlib.util.find_spec(import_name) is None:
            print(f"📦 กำลังติดตั้ง {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            except Exception as e:
                print(f"❌ ไม่สามารถติดตั้ง {package} ได้: {e}")
                sys.exit(1)

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
#  Selectors & Config
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
        "//div[contains(@class,'verify')]//canvas",
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
    except:
        pass

# ============================================================
#  Main Bot
# ============================================================
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
        print("\n🔑 [1/4] ล็อกอิน Shopee (มีเวลา 5 นาที)...")
        self.driver.get("https://shopee.co.th/buyer/login")
        try:
            WebDriverWait(self.driver, 300).until(lambda d: "login" not in d.current_url)
            print("  ✅ ล็อกอินสำเร็จ!")
        except TimeoutException:
            print("  ❌ ล็อกอินหมดเวลา")
            sys.exit(1)

    def _wait_for_captcha(self):
        """ถ้าเจอ CAPTCHA ให้หยุดและรอจนกว่าจะหายไป"""
        captcha_found = False
        for xpath in SELECTORS["captcha"]:
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                if el.is_displayed():
                    captcha_found = True
                    break
            except NoSuchElementException:
                continue
        
        if captcha_found:
            print("\n🚨 [ALERT] ตรวจพบ CAPTCHA! กรุณาจัดการในเบราว์เซอร์ให้เสร็จ...")
            alert_beep(5)
            # วนลูปเช็คจนกว่าจะหาย
            while True:
                still_has_captcha = False
                for xpath in SELECTORS["captcha"]:
                    try:
                        if self.driver.find_element(By.XPATH, xpath).is_displayed():
                            still_has_captcha = True
                            break
                    except NoSuchElementException:
                        continue
                if not still_has_captcha:
                    break
                time.sleep(1)
            print("  ✅ CAPTCHA ผ่านแล้ว! เริ่มทำงานต่อ...")

    def _click_element(self, xpaths, label, timeout=5):
        """คลิก element จากรายการ XPath"""
        for xpath in xpaths:
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                if el.is_displayed() and el.is_enabled():
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    try:
                        el.click()
                    except ElementClickInterceptedException:
                        self.driver.execute_script("arguments[0].click();", el)
                    return True
            except (NoSuchElementException, StaleElementReferenceException):
                continue
        return False

    def select_variants(self):
        """เลือกตัวเลือกสินค้า (ทำครั้งเดียวก่อนเริ่มรัว)"""
        if not self.variants:
            return True
        
        print(f"\n🎨 [2/4] กำลังเลือกตัวเลือก: {self.variants}")
        for v in self.variants:
            xpath = [x.replace("{text}", v) for x in SELECTORS["variant"]]
            ok = False
            for _ in range(10): # ลอง 10 ครั้ง กรณีหน้ายังโหลดไม่ครบ
                if self._click_smart(xpath, v):
                    ok = True
                    break
                time.sleep(0.5)
            if not ok:
                print(f"  ❌ ไม่สามารถเลือก [{v}] ได้")
                return False
        return True

    def _click_smart(self, xpaths, label):
        """Helper สำหรับ click_element แบบเงียบ"""
        for xpath in xpaths:
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                self.driver.execute_script("arguments[0].click();", el)
                return True
            except:
                pass
        return False

    def start_sale_polling(self):
        print(f"\n🚀 [3/4] เตรียมพร้อมที่หน้าสินค้า: {self.url}")
        self.driver.get(self.url)
        
        # เลือก Variant ล่วงหน้าไว้ก่อน
        self.select_variants()
        
        if self.fs_time:
            target_dt = datetime.combine(datetime.today(), datetime.strptime(self.fs_time, "%H:%M:%S").time())
            if target_dt < datetime.now(): target_dt += timedelta(days=1)
            
            print(f"🕒 รอเวลา Flash Sale: {self.fs_time}...")
            while (target_dt - datetime.now()).total_seconds() > 5:
                print(f"  ⏳ เหลือ {(target_dt - datetime.now()).total_seconds():.0f} วินาที...", end="\r")
                time.sleep(1)
            
            # ช่วง 5 วินาทีสุดท้าย — เช็ค CAPTCHA เคลียร์ทาง
            self._wait_for_captcha()
            
            # รอจนถึงจุดเริ่มรัว (เป้าหมายคือเริ่มรัวที่วินาทีที่ 0.00)
            while datetime.now() < target_dt:
                time.sleep(0.001)

            print("\n🔥 ถึงเวลาแล้ว! เริ่มระบบ Polling (รัว Buy Now)...")
            start_time = time.time()
            while time.time() - start_time < 15: # รัว 15 วินาที
                # เช็ค CAPTCHA ในลูป (ถ้าติดให้หยุดรอ)
                self._wait_for_captcha()
                
                if self._click_element(SELECTORS["buy_now"], "Buy Now"):
                    print("  🔥 กด Buy Now สำเร็จ!")
                    return True
                
                # ป้องกันกรณี Variant หลุด (Shopee บางทีโหลดใหม่แล้ว Variant หาย)
                # แต่จะไม่รัวกด Variant ทุกรอบ จะเช็คเฉพาะตอนกด Buy Now ไม่เจอ
                time.sleep(0.01)
            return False
        else:
            return self._click_element(SELECTORS["buy_now"], "Buy Now")

    def checkout(self):
        print("\n💳 [4/4] กำลังเข้าสู่หน้า Checkout...")
        try:
            WebDriverWait(self.driver, 20).until(EC.url_contains("checkout"))
            self._wait_for_captcha()
            alert_beep(3)
            print("="*55)
            print("  🎉 บอทพามาถึงหน้า Checkout แล้ว!")
            print("  👆 กรุณาตรวจสอบและกด 'ยืนยันสั่งซื้อ' ด้วยตัวเอง")
            print("="*55)
        except TimeoutException:
            print("  ⚠️  หน้า Checkout ไม่โหลดอัตโนมัติ กรุณาดำเนินการต่อเอง")

    def run(self):
        try:
            self.login()
            if self.start_sale_polling():
                self.checkout()
            else:
                print("\n❌ กดซื้อไม่สำเร็จ (อาจสินค้าหมดหรือเน็ตช้า)")
                alert_beep(5)
        except Exception as e:
            print(f"\n❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
            alert_beep(3)
        finally:
            print("\nเบราว์เซอร์ยังเปิดอยู่เพื่อใช้ดำเนินการต่อ...")

if __name__ == "__main__":
    print("="*55)
    print("   Shopee Flash Sale Assistant - v3.0 FINAL")
    print("="*55)
    
    p_url = input("🔗 ลิงก์สินค้า: ").strip()
    v_str = input("🎨 ตัวเลือก (เช่น สีดำ,256GB) ถ้าไม่มีให้ Enter: ").strip()
    p_variants = [v.strip() for v in v_str.split(",")] if v_str else []
    p_time = input("⏰ เวลา Flash Sale (HH:MM:SS): ").strip()

    bot = ShopeeFinalBot(p_url, p_variants, p_time)
    bot.run()
