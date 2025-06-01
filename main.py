import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from config import BRAVE_PATH

COOKIES_FILE = "cookies.json"
TRADE_URL = "https://funpay.com/lots/81/trade"
LOGIN_URL = "https://funpay.com/en/account/login"
LOGOUT_BUTTON_SELECTOR = "a.menu-item-logout[href*='logout']"
RAISE_BUTTON_SELECTOR = "button.js-lot-raise"
RAISE_OFFERS_BUTTON_SELECTOR = "button.js-lot-raise-ex"
CHECKBOX_SELECTOR = "input[type='checkbox'][value='{value}']"
TRADE_URLS = {
    "82": {
        "url": "https://funpay.com/lots/82/trade",
        "checkbox_values": ["82", "502"]
    },
    "1106": {
        "url": "https://funpay.com/lots/1106/trade",
        "checkbox_values": ["1234", "5678"]  # <-- Заменить на актуальные
    }
}
TIMEOUT = 30

class FunPayAutoRaiser:
    def __init__(self):
        self.driver = None
        self.wait = None

    def setup_driver(self, headless=False):
        options = Options()
        options.binary_location = BRAVE_PATH
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        else:
            options.add_argument("--start-maximized")
        service = Service(ChromeDriverManager(driver_version="136.0.7103.94").install())
        driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(driver, TIMEOUT)
        return driver

    def save_cookies(self, driver):
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(driver.get_cookies(), f, indent=2)
        print("💾 Cookies сохранены.")

    def load_cookies(self, driver):
        if not os.path.exists(COOKIES_FILE):
            return False
        try:
            with open(COOKIES_FILE, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            driver.get("https://funpay.com")  # Нужно вызвать перед add_cookie
            for cookie in cookies:
                if "sameSite" in cookie and cookie["sameSite"] == "None":
                    cookie["sameSite"] = "Strict"
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"⚠️ Ошибка при добавлении cookie: {e}")
            print("✅ Cookies загружены.")
            return True
        except Exception as e:
            print(f"❌ Ошибка при загрузке cookies: {e}")
            return False

    def is_logged_in(self, driver):
        driver.get("https://funpay.com")
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, LOGOUT_BUTTON_SELECTOR)))
            return True
        except:
            return False

    def manual_login(self):
        print("🔐 Открываем браузер для авторизации...")
        self.driver = self.setup_driver(headless=False)
        self.driver.get(LOGIN_URL)

        try:
            print("⏳ Ждём кнопку 'Выйти' для подтверждения входа...")
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, LOGOUT_BUTTON_SELECTOR)))
            print("✅ Авторизация успешна!")
            self.save_cookies(self.driver)
        finally:
            self.driver.quit()
    def raise_lot(self):
        print("🌐 Запускаем браузер в headless-режиме...")
        self.driver = self.setup_driver(headless=True)
        self.load_cookies(self.driver)

        for lot_id, lot_info in TRADE_URLS.items():
            try:
                print(f"🔄 Обработка лота {lot_id}...")
                self.driver.get(lot_info["url"])

                # Первая кнопка "Поднять предложения"
                print("🟡 Нажимаем первую кнопку 'Поднять предложения'...")
                first_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, RAISE_BUTTON_SELECTOR)))
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", first_button)
                time.sleep(1)
                first_button.click()

                # Отметить чекбоксы
                print("☑️ Отмечаем нужные чекбоксы...")
                for checkbox_value in lot_info["checkbox_values"]:
                    selector = CHECKBOX_SELECTOR.format(value=checkbox_value)
                    checkbox = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if not checkbox.is_selected():
                        self.driver.execute_script("arguments[0].click();", checkbox)
                        print(f"  ☑️ Активирован чекбокс {checkbox_value}")
                    else:
                        print(f"  🔘 Чекбокс {checkbox_value} уже активен")

                # Вторая кнопка "Поднять предложения"
                print("🟢 Нажимаем вторую кнопку 'Поднять предложения'...")
                second_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, RAISE_OFFERS_BUTTON_SELECTOR)))
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", second_button)
                time.sleep(1)
                second_button.click()
                print(f"✅ Лот {lot_id} успешно обработан!")

            except Exception as e:
                print(f"❌ Ошибка при обработке лота {lot_id}: {e}")
                self.driver.save_screenshot(f"raise_error_{lot_id}.png")

        self.driver.quit()

    def run(self, interval_hours=4):
        # Если нет cookies — логин вручную
        if not os.path.exists(COOKIES_FILE):
            self.manual_login()

        # Проверка: cookies рабочие?
        print("🔍 Проверяем cookies...")
        test_driver = self.setup_driver(headless=True)
        if not self.load_cookies(test_driver) or not self.is_logged_in(test_driver):
            print("⚠️ Сессия не активна. Требуется повторная авторизация.")
            test_driver.quit()
            self.manual_login()
        else:
            print("✅ Авторизация через cookies прошла успешно.")
            test_driver.quit()

        # Основной цикл
        try:
            while True:
                self.raise_lot()
                print(f"⏳ Следующее поднятие через {interval_hours} ч...")
                time.sleep(interval_hours * 3600)
        except KeyboardInterrupt:
            print("\n🛑 Скрипт остановлен пользователем")
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    bot = FunPayAutoRaiser()
    bot.run()