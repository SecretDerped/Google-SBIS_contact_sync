import logging
import os
import sys
import time
import traceback
from datetime import datetime
from functools import wraps

from selenium.common import InvalidSelectorException, InvalidSessionIdException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement

from utilits import normalize_phone, log_print

SBIS_LOGIN = 'leartest'
SBIS_PASSWORD = 'Leartest2007!'
input_today_name = "ws-input_" + datetime.now().strftime('%Y-%m-%d')


def log_webdriver_action(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        # Предполагаем, что первый аргумент после self - это либо экземпляр WebDriver, либо WebElement
        element_or_driver = args[1]
        description = "WebDriver" if not isinstance(element_or_driver, WebElement) else "WebElement"
        # Дополнительно логгируем тип элемента и его атрибуты, если это WebElement
        if description == "WebElement":
            try:
                text = element_or_driver.text
                element_description = f"{element_or_driver.tag_name} element"
                if text:
                    element_description += f" with text:\n'{text}'"
            except:
                element_description = "unknown element"
            logging.info(f"CALL {func.__name__} on {element_description}...")
        else:
            logging.info(f"CALL {func.__name__} on {description}...")

        start_time = time.time()
        result = func(*args, **kwargs)
        exec_time = time.time() - start_time
        logging.info(f"RESULT {func.__name__} is completed for {exec_time:.3f} sec.")
        return result
    return _wrapper

class WebdriverProfile:
    def __init__(self):
        self.download_directory = "/home/user/Autorun/SBIS_contacts"
        self.options = ChromeOptions()
        self.options.add_argument('--allow-profiles-outside-user-dir')
        self.options.add_argument('--enable-profile-shortcut-manager')
        self.options.add_argument('--profile-directory=Profile 1')
        self.options.add_argument(r'user-data-dir=.\User')
        #self.options.add_argument("--headless")  # Выполнение в фоновом режиме без открытия браузера
        self.options.add_argument("--window-size=1600,900")
        self.options.add_experimental_option("prefs", {
            "download.default_directory": self.download_directory,
            "download.prompt_for_download": False,  # Отключение всплывающее окно загрузки
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        self.driver = Chrome(options=self.options)
        self.driver.implicitly_wait(5)

    @log_print
    def close(self):
        try:
            self.driver.quit()
            return True
        except Exception:
            return False

    @log_webdriver_action
    def click(self, element):
        """Imitate moving cursor and clicking the web element"""
        ActionChains(self.driver).move_to_element(element).click().perform()
        return True

    def find(self, xpath: str):
        """Search for one web element by Xpath"""
        result = self.driver.find_element(By.XPATH, xpath)
        return result

    def find_all(self, xpath: str):
        """Searching for all web elements by Xpath"""
        result = self.driver.find_elements(By.XPATH, xpath)
        return result

    @log_print
    def sbis_login(self):
        find = self.find
        click = self.click
        driver = self.driver

        time.sleep(2)
        login_box = driver.find_element(By.NAME, input_today_name)
        login_box.send_keys(SBIS_LOGIN)
        time.sleep(2)

        submit_button_xpath = "//div[@class='auth-AdaptiveLoginForm__loginButtonImage controls-BaseButton__icon controls-icon controls-icon_size-m controls-icon_style-contrast']"
        submit_button = find(submit_button_xpath)
        click(submit_button)
        time.sleep(2)

        password_box = driver.find_elements(By.NAME, input_today_name)[1]
        click(password_box)
        password_box.send_keys(SBIS_PASSWORD)

        submit_button = find(submit_button_xpath)  # ДА, ТАК НАДО
        click(submit_button)
        return True


    @log_print
    def sbis_contact_search(self, contact_phone_number: str):
        find = self.find
        finds = self.find_all
        click = self.click
        driver = self.driver

        phone = normalize_phone(contact_phone_number)
        try:  # Если при загрузке найден элемент со страницы авторизации, выполняет скрипт авторизации
            driver.get('https://online.sbis.ru/page/crm-clients')
            if len(finds("//div[@class='auth-AuthTemplate__browserWarning']")) > 0:
                self.sbis_login()

            contact_search_field = driver.find_element(By.NAME, input_today_name)
            contact_search_field.send_keys(phone)  # Находит поле поиска, ищет через него компанию по номеру и ждёт, пока поиск прогрузится
            time.sleep(2.5)

            clients = finds("//div[@class='crm_ClientMain__item crm_ClientMain__item ws-ellipsis ws-flexbox ws-flex-column']")
            if clients is []:   # Кликает на первую позицию в поиске и ждёт, когда откроется
                return None
            if type(clients) is list:
                click(clients[0])
            else:
                click(clients)
            time.sleep(4)

            try:  # Нажимает кнопку "Еще ..." в списке контактов, если она есть. Обычно появляется, если контактов больше 7
                more_button = finds(
                    "//span[@class='controls-BaseButton__text controls-text-listMore controls-Button_text-listMore controls-Button__text-listMore_viewMode-link controls-Button__text_viewMode-link'")
                click(more_button)
            except InvalidSelectorException:
                pass

            if len(expand_buttons := finds(
                    "//span[@class='controls-fontsize-m cd-ItemTemplate__showMoreContacts controls-margin_left-2xl controls-padding_left-3xs']")) > 0:
                for button in expand_buttons:  # Нажимает кнопки раскрытия контакта, если они есть
                    click(button)
                    time.sleep(0.4)
            try:
                company_name = find('//div[@class="controls-Tabs__item_overflow"]').text
            except NoSuchElementException:
                client_name = find('//div[@data-qa="crm_IndividualCard__nameInput"]').text
                return f'{client_name}'
            contacts = finds(
                "//div[@class='controls-ListView__itemV-relative controls-ListView__itemV js-controls-ListView__editingTarget  controls-ListView__itemV_cursor-default  controls-ListView__item_default controls-ListView__item_showActions js-controls-ListView__measurableContainer controls-ListView__item__unmarked_default controls-ListView__item_roundBorder_topLeft_l controls-ListView__item_roundBorder_topRight_l controls-ListView__item_roundBorder_bottomLeft_l controls-ListView__item_roundBorder_bottomRight_l controls-Tree__item  controls-ListView__item-leftPadding_null cd-ContactsView__itemTemplate cd-ContactsTreeView__item cd-ContactsTreeView__root-item undefined controls-margin_bottom-3xs']")
            for contact in contacts:   # Сохраняет имя компании, ищет контакты и возвращает имя владельца номера
                contact_info = contact.text.split('\n')
                for field in contact_info:
                    if field[0].isdigit():
                        if phone == normalize_phone(field):  # Если телефон совпадает, собирает имя и должность, фильтруя поля, содержащие цифры, "@" или "."
                            filtered_words = [word for word in contact_info if all(char.isdigit() is False and char not in {'@', '.'} for char in word)]
                            contact_name = ', '.join(filtered_words)
                            return f'{contact_name} ({company_name})' if contact_name else f'{company_name}'

        except InvalidSessionIdException:
            logging.critical(f'{traceback.format_exc()}')
            sys.exit(1)

        except Exception:
            logging.warning(f'{traceback.format_exc()}')
            if '--headless' in self.options.arguments:
                return False
            time.sleep(36000)
            return None

    @log_print
    def get_sbis_contacts_xlsx(self):
        find = self.find
        finds = self.find_all
        click = self.click
        driver = self.driver

        try:  # Если при загрузке найден элемент со страницы авторизации, выполняет скрипт авторизации
            driver.get('https://online.sbis.ru/page/crm-clients')
            if len(finds("//div[@class='auth-AuthTemplate__browserWarning']")) > 0:
                self.sbis_login()

            time.sleep(2)

            toggle_operations_button = find('//div[@data-qa="toggleOperationsPanel"]')
            click(toggle_operations_button)  # Кнопка "Отметить"
            time.sleep(2)

            fill_all_radiobutton = find('//div[@data-qa="controls-CheckboxMarker"]')
            click(fill_all_radiobutton)  # Круглая кнопка "Отметить все"

            unload_button = find('//i[@class="controls-BaseButton__icon controls-icon_size-s controls-icon icon-UnloadNew"]')
            click(unload_button)  # Кнопка "Выгрузить" вверху

            download_button = find('//div[@title="Номера телефонов"]')
            click(download_button)  # Пункт "Номера телефонов"

            while True:  # Проверка, что файл полностью загружен
                if os.path.exists(self.download_directory + '/Клиенты_CRM.xlsx'):
                    logging.info(f"File downloaded successfully: {self.download_directory}/Клиенты_CRM.xlsx")
                    return True
                else:
                    time.sleep(1)

        except Exception:
            logging.warning(f'{traceback.format_exc()}')
            if '--headless' in self.options.arguments:
                return None
            time.sleep(36000)
            return False


def reload(webdriver: WebdriverProfile):
    webdriver.driver.quit()
    logging.debug('Driver was reloaded.')
    return WebdriverProfile()


if __name__ == '__main__':
    browser = WebdriverProfile()
    #print(browser.sbis_contact_search('89183816878'))
    browser.close()
