import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta

# พยายามนำเข้า selenium_stealth และ winsound
try:
    from selenium_stealth import stealth
except ImportError:
    print("⚠️ กำลังติดตั้ง selenium-stealth...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium-stealth"])
    from selenium_stealth import stealth

try:
    import winsound
except ImportError:
    # สำหรับระบบที่ไม่ใช่ Windows ให้ใช้การพิมพ์ข้อความเตือนแทน
    winsound = None

class ShopeeFlashSalePro:
    def __init__(self, product_url, variants=None, flash_sale_time=None):
        self.product_url = product_url
        self.variants = variants if variants else []
        self.flash_sale_time = flash_sale_time
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # ใช้ Selenium Stealth เพื่อพรางตัว
        stealth(self.driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

    def alert_user(self, message):
        """ส่งเสียงเตือนและพิมพ์ข้อความเมื่อต้องการความช่วยเหลือจากมนุษย์"""
        print(f"\n🚨 {message}")
        if winsound:
            for _ in range(5):
                winsound.Beep(1000, 500)
        else:
            print("\a") # เสียงกระดิ่งระบบทั่วไป

    def login_manually(self):
        print("🔑 กรุณาล็อกอินเข้า Shopee ในเบราว์เซอร์...")
        self.driver.get("https://shopee.co.th/buyer/login")
        
        start_time = time.time()
        while "login" in self.driver.current_url:
            if time.time() - start_time > 300:
                print("❌ หมดเวลาล็อกอิน")
                sys.exit()
            time.sleep(1)
        print("✅ ล็อกอินสำเร็จ!")

    def check_captcha(self):
        """ตรวจสอบว่าติดหน้า CAPTCHA หรือไม่"""
        captcha_indicators = ["verify", "captcha", "robot"]
        if any(ind in self.driver.page_source.lower() for ind in captcha_indicators):
            self.alert_user("ติดหน้า CAPTCHA! กรุณารีบจัดการด่วน!")
            return True
        return False

    def wait_for_flash_sale(self):
        if not self.flash_sale_time:
            self.driver.get(self.product_url)
            return

        self.driver.get(self.product_url)
        try:
            target_dt = datetime.strptime(self.flash_sale_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            today = datetime.now().strftime("%Y-%m-%d")
            target_dt = datetime.strptime(f"{today} {self.flash_sale_time}", "%Y-%m-%d %H:%M:%S")

        print(f"🕒 รอเวลา Flash Sale: {target_dt}...")
        
        # รอจนเกือบถึงเวลา
        while datetime.now() < target_dt - timedelta(seconds=2):
            time.sleep(0.5)
            
        print("🚀 เริ่มระบบ Polling (เฝ้าสังเกตปุ่มซื้อ)...")
        # แทนที่จะ Refresh ทั้งหน้า เราจะวนลูปหาปุ่มจนกว่าจะกดได้
        buy_button_xpath = "//button[@type='button' and (contains(., 'ซื้อสินค้า') or contains(., 'Buy Now'))]"
        
        while datetime.now() < target_dt:
            pass # รอจนถึงวินาทีที่ 0
            
        # วนลูปกดปุ่มรัวๆ จนกว่าจะสำเร็จหรือหมดเวลา
        start_attempt = time.time()
        while time.time() - start_attempt < 10: # พยายาม 10 วินาที
            try:
                # ตรวจ CAPTCHA ระหว่างทาง
                self.check_captcha()
                
                # พยายามคลิกปุ่ม
                buy_btn = self.driver.find_element(By.XPATH, buy_button_xpath)
                if buy_btn.is_enabled():
                    buy_btn.click()
                    print("🔥 กดปุ่มซื้อสำเร็จ!")
                    return True
            except:
                pass
            time.sleep(0.05) # พักสั้นๆ เพื่อไม่ให้ CPU ทำงานหนักเกินไป
        return False

    def checkout_process(self):
        """จัดการหน้าชำระเงิน"""
        print("💳 กำลังเข้าสู่หน้า Checkout...")
        try:
            WebDriverWait(self.driver, 10).until(EC.url_contains("checkout"))
            self.check_captcha()
            
            # พยายามเลือกวิธีชำระเงิน (ตัวอย่าง: เลือกตัวเลือกแรกที่พบ)
            # ในสถานการณ์จริง คุณควรตั้งค่า 'วิธีชำระเงินเริ่มต้น' ใน Shopee ไว้แล้ว
            print("🏁 มาถึงหน้าสั่งซื้อแล้ว! กรุณาตรวจสอบและกดยืนยันด้วยตัวเองเพื่อความปลอดภัย")
            self.alert_user("พร้อมสั่งซื้อแล้ว! กรุณากดปุ่ม 'สั่งซื้อ' (Place Order) ด้วยตัวเอง")
            
        except Exception as e:
            print(f"⚠️ เกิดปัญหาในหน้า Checkout: {e}")
            self.alert_user("เกิดปัญหา! กรุณาตรวจสอบหน้าจอเบราว์เซอร์")

    def run(self):
        self.login_manually()
        if self.wait_for_flash_sale():
            self.checkout_process()
        else:
            self.alert_user("กดซื้อไม่สำเร็จภายในเวลาที่กำหนด")

if __name__ == "__main__":
    print("=== Shopee Flash Sale Pro (v3.0 Stealth) ===")
    url = input("🔗 ลิงก์สินค้า: ")
    fs_time = input("⏰ เวลา Flash Sale (HH:MM:SS): ")
    
    bot = ShopeeFlashSalePro(url, flash_sale_time=fs_time)
    bot.run()
