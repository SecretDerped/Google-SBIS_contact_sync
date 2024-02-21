import logging

import pygetwindow as gw
import time
import re
from selenium.webdriver import Chrome, ChromeOptions
from bs4 import BeautifulSoup

console_out = logging.StreamHandler()
file_log = logging.FileHandler("../application.log", mode="w")
logging.basicConfig(handlers=(file_log, console_out), level=logging.INFO,
                    format='[%(asctime)s | %(levelname)s]: %(message)s')

# Подключаемся к уже открытому Chrome
options = ChromeOptions()
prefs = {"download.default_directory": "C:\\Your\\Download\\Directory"}
options.add_experimental_option("prefs", prefs)
driver = Chrome(options=options)


def log_print(func):
    def _wrapper(*args, **kwargs):
        logging.info(f'Call - {func.__name__}{args} {kwargs}')
        result = func(*args, **kwargs)
        logging.info(f'Result - {func.__name__}{args} {kwargs}: {result}')
        return result
    return _wrapper


@log_print
def is_window_open(window_name):
    return True if len(gw.getWindowsWithTitle(window_name)) > 0 else False


@log_print
def find_phone_numbers(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return re.findall(r'\+?\d[\d\s-]{10,}', soup.get_text())


if __name__ == '__main__':
    while is_window_open(window_name):
        driver.get('https://online.sbis.ru/phone')
        # lurk lurk lurk...
        phones = find_phone_numbers(driver)
        print(phones)
        time.sleep(10)
    print('Всё')
    driver.quit()
