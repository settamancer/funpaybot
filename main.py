from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
from config import BRAVE_PATH

TRADE_URL = "https://funpay.com/lots/81/trade"
LOGOUT_BUTTON_SELECTOR = "a.menu-item-logout[href*='logout']"
RAISE_BUTTON_SELECTOR = "button.js-lot-raise"
TIMEOUT = 30  # Увеличил таймаут для надёжности

class FunPayAutoRaiser:
    def __init__(self):
        self.driver = self.setup_driver()
        self.wait = WebDriverWait(self.driver, TIMEOUT)

    def setup_driver(self):
        if not os.path.exists(BRAVE_PATH):
            raise FileNotFoundError(f"Brave не найден по пути: {BRAVE_PATH}")
        options = Options()
        options.binary_location = BRAVE_PATH
        options.add_argument("--start-maximized")
        service = Service(ChromeDriverManager(driver_version="136.0.7103.94").install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def manual_login(self):
        """Ждёт ручной авторизации по кнопке 'Выйти'"""
        print("🔐 Открываем FunPay для ручного входа...")
        self.driver.get("https://funpay.com/en/account/login")
        
        try:
            print("⏳ Ожидаем ручной авторизации (ищем кнопку 'Выйти')...")
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, LOGOUT_BUTTON_SELECTOR))
            )
            print("✅ Авторизация успешна (кнопка 'Выйти' найдена)!")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.driver.quit()
            raise

    def raise_lot(self):
        """Нажимает кнопку 'Поднять предложения'"""
        print("🌐 Переходим на страницу торговли...")
        self.driver.get(TRADE_URL)
        
        try:
            print("🔎 Ищем кнопку поднятия...")
            raise_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, RAISE_BUTTON_SELECTOR)))
            
            # Плавный скролл и клик
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                raise_button)
            time.sleep(1)
            raise_button.click()
            print("✅ Лот успешно поднят!")
        except Exception as e:
            print(f"❌ Ошибка при поднятии лота: {e}")
            self.driver.save_screenshot("error.png")
            raise

    def run(self, interval_hours=4):
        """Основной цикл с заданным интервалом"""
        try:
            self.manual_login()
            while True:
                self.raise_lot()
                print(f"⏳ Следующее обновление через {interval_hours} часа...")
                time.sleep(interval_hours * 3600)  
        except KeyboardInterrupt:
            print("\n🛑 Скрипт остановлен пользователем")
        finally:
            self.driver.quit()

if __name__ == "__main__":
    bot = FunPayAutoRaiser()
    bot.run()  