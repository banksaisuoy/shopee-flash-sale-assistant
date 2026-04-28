import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta

class ShopeeFlashSaleAssistant:
    def __init__(self, product_url, variants=None, flash_sale_time=None):
        self.product_url = product_url
        self.variants = variants if variants else []
        self.flash_sale_time = flash_sale_time # รูปแบบ "YYYY-MM-DD HH:MM:SS"
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def login_manually(self):
        """ให้ผู้ใช้ล็อกอินด้วยตัวเอง พร้อมระบบ Timeout"""
        print("กรุณาล็อกอินเข้า Shopee ในหน้าต่างเบราว์เซอร์ที่เปิดขึ้นมา...")
        self.driver.get("https://shopee.co.th/buyer/login")
        
        timeout = 300  # 5 นาที
        start_time = time.time()
        while "login" in self.driver.current_url:
            if time.time() - start_time > timeout:
                print("❌ หมดเวลาล็อกอิน กรุณารันโปรแกรมใหม่อีกครั้ง")
                self.driver.quit()
                sys.exit()
            time.sleep(1)
        print("✅ ล็อกอินสำเร็จแล้ว!")

    def wait_for_flash_sale(self):
        """รอจนกว่าจะถึงเวลา Flash Sale พร้อมระบบ Pre-load"""
        if not self.flash_sale_time:
            self.driver.get(self.product_url)
            return
        
        # โหลดหน้าสินค้าล่วงหน้า
        print("📦 กำลังโหลดหน้าสินค้าล่วงหน้า...")
        self.driver.get(self.product_url)
        
        try:
            target_datetime = datetime.strptime(self.flash_sale_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # กรณีใส่แค่เวลา ให้ใช้เป็นวันที่ปัจจุบัน
            today = datetime.now().strftime("%Y-%m-%d")
            try:
                target_datetime = datetime.strptime(f"{today} {self.flash_sale_time}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print("❌ รูปแบบเวลาไม่ถูกต้อง กรุณาใช้ HH:MM:SS หรือ YYYY-MM-DD HH:MM:SS")
                return

        print(f"🕒 กำลังรอเวลา Flash Sale: {target_datetime}...")
        
        # รอจนเหลือ 5 วินาที
        while datetime.now() < target_datetime - timedelta(seconds=5):
            time.sleep(1)
            
        # Precision loop ช่วงสุดท้าย
        print("🚀 เข้าสู่ช่วงนับถอยหลังวินาทีสุดท้าย...")
        while datetime.now() < target_datetime:
            time.sleep(0.01)
        
        print("🔥 ถึงเวลาแล้ว! กำลัง Refresh หน้าสินค้า...")
        self.driver.refresh()

    def click_with_retry(self, xpath, name, retries=5):
        """พยายามคลิกปุ่มด้วยระบบ Retry"""
        for i in range(retries):
            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                element.click()
                print(f"✅ คลิก {name} สำเร็จ")
                return True
            except Exception as e:
                print(f"⚠️ พยายามคลิก {name} ครั้งที่ {i+1}/{retries}...")
                time.sleep(0.1)
        return False

    def buy_product(self):
        """ขั้นตอนการกดซื้อสินค้าเวอร์ชันปรับปรุง"""
        try:
            # 1. เลือกตัวเลือกสินค้า (ถ้ามี)
            for variant in self.variants:
                variant_xpath = f"//*[contains(@class,'product-variation') and contains(text(), '{variant}')]"
                if not self.click_with_retry(variant_xpath, f"ตัวเลือก: {variant}"):
                    print(f"❌ ไม่สามารถเลือกตัวเลือก {variant} ได้")
            
            # 2. กดปุ่ม "ซื้อสินค้า" (Buy Now)
            buy_button_xpath = "//button[@type='button' and (contains(., 'ซื้อสินค้า') or contains(., 'Buy Now'))]"
            if self.click_with_retry(buy_button_xpath, "ปุ่มซื้อสินค้า"):
                # 3. นำทางไปยังหน้า Checkout
                print("💳 กำลังนำทางไปยังหน้าชำระเงิน...")
                WebDriverWait(self.driver, 20).until(
                    EC.url_contains("checkout")
                )
                print("🏁 มาถึงหน้าชำระเงินแล้ว! กรุณาตรวจสอบและกดยืนยันการสั่งซื้อด้วยตัวเอง")
            else:
                print("❌ ไม่พบปุ่มซื้อสินค้า หรือปุ่มยังไม่เปิดให้กด")
                
        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")

    def run(self):
        self.login_manually()
        self.wait_for_flash_sale()
        self.buy_product()
        print("\n=== สิ้นสุดการทำงานอัตโนมัติ ===")

if __name__ == "__main__":
    print("=== Shopee Flash Sale Assistant (v2.0) ===")
    url = input("🔗 กรุณาใส่ลิงก์สินค้า Shopee: ")
    variants_str = input("🎨 ตัวเลือกสินค้า (แยกด้วยคอมม่า เช่น สีดำ,256GB) ถ้าไม่มีให้เว้นว่าง: ")
    variants = [v.strip() for v in variants_str.split(",")] if variants_str else []
    
    print("\nรูปแบบเวลา: YYYY-MM-DD HH:MM:SS (เช่น 2026-12-12 12:00:00)")
    print("หรือใส่แค่เวลา: HH:MM:SS (เช่น 12:00:00) ระบบจะใช้วันนี้")
    fs_time = input("⏰ เวลา Flash Sale: ")
    
    assistant = ShopeeFlashSaleAssistant(url, variants, fs_time)
    assistant.run()
