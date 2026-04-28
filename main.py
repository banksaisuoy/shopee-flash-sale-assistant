import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

class ShopeeFlashSaleAssistant:
    def __init__(self, product_url, variants=None, flash_sale_time=None):
        self.product_url = product_url
        self.variants = variants if variants else []
        self.flash_sale_time = flash_sale_time
        
        # ตั้งค่า Chrome Options
        chrome_options = Options()
        # chrome_options.add_argument("--headless") # เปิดเพื่อไม่ให้แสดงหน้าต่างเบราว์เซอร์
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # กำหนดพาธของ ChromeDriver (ต้องมีติดตั้งในเครื่อง)
        # service = Service('/path/to/chromedriver') 
        # self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # สำหรับ Manus Environment จะใช้ ChromeDriver ที่ติดตั้งอยู่แล้ว
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def login_manually(self):
        """ให้ผู้ใช้ล็อกอินด้วยตัวเอง"""
        print("กรุณาล็อกอินเข้า Shopee ในหน้าต่างเบราว์เซอร์ที่เปิดขึ้นมา...")
        self.driver.get("https://shopee.co.th/buyer/login")
        # รอจนกว่าจะล็อกอินสำเร็จ (ตรวจสอบจากคุกกี้หรือ URL ที่เปลี่ยนไป)
        while "login" in self.driver.current_url:
            time.sleep(1)
        print("ล็อกอินสำเร็จแล้ว!")

    def wait_for_flash_sale(self):
        """รอจนกว่าจะถึงเวลา Flash Sale"""
        if not self.flash_sale_time:
            return
        
        target_time = datetime.strptime(self.flash_sale_time, "%H:%M:%S").time()
        print(f"กำลังรอเวลา Flash Sale: {self.flash_sale_time}...")
        
        while True:
            now = datetime.now().time()
            if now >= target_time:
                print("ถึงเวลา Flash Sale แล้ว! เริ่มการทำงาน...")
                break
            time.sleep(0.1) # ตรวจสอบทุก 0.1 วินาที

    def buy_product(self):
        """ขั้นตอนการกดซื้อสินค้า"""
        self.driver.get(self.product_url)
        
        try:
            # 1. เลือกตัวเลือกสินค้า (ถ้ามี)
            for variant in self.variants:
                print(f"กำลังเลือกตัวเลือก: {variant}...")
                variant_element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{variant}')]"))
                )
                variant_element.click()
            
            # 2. กดปุ่ม "ซื้อสินค้า" (Buy Now)
            print("กำลังกดปุ่ม 'ซื้อสินค้า'...")
            # Shopee มักจะใช้ปุ่มที่มีคลาสเฉพาะ หรือข้อความ "ซื้อสินค้า" หรือ "Buy Now"
            buy_button_xpath = "//button[contains(@class, 'btn-solid-primary') and (contains(text(), 'ซื้อสินค้า') or contains(text(), 'Buy Now'))]"
            buy_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, buy_button_xpath))
            )
            buy_button.click()
            
            # 3. ไปที่หน้าชำระเงิน (Checkout)
            print("กำลังนำทางไปยังหน้าชำระเงิน...")
            # หลังจากกด "ซื้อสินค้า" มักจะนำทางไปยังหน้าชำระเงินโดยอัตโนมัติ
            # หรืออาจต้องกดปุ่ม "ชำระเงิน" ในหน้าตะกร้า
            
            # ตรวจสอบว่าอยู่ในหน้า Checkout หรือยัง
            WebDriverWait(self.driver, 20).until(
                EC.url_contains("checkout")
            )
            print("มาถึงหน้าชำระเงินแล้ว! กรุณาตรวจสอบและกดยืนยันการสั่งซื้อด้วยตัวเองครับ")
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")

    def run(self):
        self.login_manually()
        self.wait_for_flash_sale()
        self.buy_product()
        # ปล่อยเบราว์เซอร์ไว้เพื่อให้ผู้ใช้ดำเนินการต่อ
        print("โปรแกรมทำงานเสร็จสิ้น (ขั้นตอนอัตโนมัติ) กรุณาดำเนินการต่อในเบราว์เซอร์...")
        # self.driver.quit() # ไม่ปิดเบราว์เซอร์เพื่อให้ผู้ใช้กดชำระเงินเอง

if __name__ == "__main__":
    # ตัวอย่างการใช้งาน
    # ลิงก์สินค้า: https://shopee.co.th/product-i.123456.7891011
    # ตัวเลือก: ['สีดำ', '256GB']
    # เวลา Flash Sale: '12:00:00'
    
    print("=== Shopee Flash Sale Assistant ===")
    url = input("กรุณาใส่ลิงก์สินค้า Shopee: ")
    variants_str = input("กรุณาใส่ตัวเลือกสินค้า (แยกด้วยคอมม่า เช่น สีดำ,256GB) ถ้าไม่มีให้เว้นว่าง: ")
    variants = [v.strip() for v in variants_str.split(",")] if variants_str else []
    fs_time = input("กรุณาใส่เวลา Flash Sale (รูปแบบ HH:MM:SS เช่น 12:00:00) ถ้าไม่มีให้เว้นว่าง: ")
    
    assistant = ShopeeFlashSaleAssistant(url, variants, fs_time)
    assistant.run()
