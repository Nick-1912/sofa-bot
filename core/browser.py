from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from undetected_chromedriver import ChromeOptions
from seleniumwire.undetected_chromedriver import Chrome
from core.config_parser import UndetectedSeleniumConfig
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import time
import random


class Browser:
    CONFIG = UndetectedSeleniumConfig()
    MAIN_PAGE = 'https://www.sofascore.com'

    def __init__(self,
                 fullscreen: Optional[bool] = None,
                 window_height: Optional[int] = None,
                 window_width: Optional[int] = None,
                 use_proxy: Optional[bool] = None):
        self.fullscreen = fullscreen if fullscreen else self.CONFIG['fullscreen']
        self.window_height = window_height if window_height else self.CONFIG['window height']
        self.window_width = window_width if window_width else self.CONFIG['window width']
        self.use_proxy = use_proxy if use_proxy else self.CONFIG['use proxy']
        self.driver = self.create_browser()
        self.open_page('https://google.com/')

    def create_browser(self):
        options = ChromeOptions()
        proxy_options = None

        options.add_argument('--user-data-dir=' + os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                               self.CONFIG['browser folder']))
        if self.fullscreen:
            options.add_argument('--kiosk')
        if self.use_proxy:
            proxy_options = {'proxy': {
                'http': f'http://{self.CONFIG["proxy username"]}:{self.CONFIG["proxy password"]}@'
                        f'{self.CONFIG["proxy ip"]}:{self.CONFIG["proxy port"]}',
                'https': f'http://{self.CONFIG["proxy username"]}:{self.CONFIG["proxy password"]}@'
                         f'{self.CONFIG["proxy ip"]}:{self.CONFIG["proxy port"]}'}}
        driver = Chrome(options=options, seleniumwire_options=proxy_options)
        if not self.fullscreen:
            driver.set_window_size(self.window_width, self.window_height)
        return driver

    def close_browser(self):
        self.driver.quit()

    def open_page(self, url: str):
        self.driver.get(url)

    def open_main_page(self):
        self.open_page(self.MAIN_PAGE)

    @staticmethod
    def random_sleep(left: int = 10, right: int = 20):
        time.sleep(random.randint(left, right))

    def wait(self, delay: int, wait_for_by: By, wait_for_element: str, poll_frequency: float = 0.5):
        try:
            WebDriverWait(self.driver, delay, poll_frequency).until(
                EC.presence_of_element_located((wait_for_by, wait_for_element)))
            return True
        except TimeoutException:
            return False

    def check_web_element_availability(self, by: By, by_what: str):
        try:
            self.driver.find_element(by, by_what)
            return True
        except NoSuchElementException:
            return False

    def check_text_availability(self, text: str):
        return True if text in self.driver.page_source else False

    def change_zoom(self, zoom: int = 25):
        self.driver.execute_script(f"""document.body.style.zoom='{zoom}%'""")

    def scroll_to_web_element(self, web_element: WebElement):
        self.driver.execute_script("return arguments[0].scrollIntoView();", web_element)


if __name__ == '__main__':
    temp_browser = Browser()
    temp_browser.open_page('https://google.com/')
    temp_browser.close_browser()
