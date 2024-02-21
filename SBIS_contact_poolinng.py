import logging
import os
import time
from datetime import datetime
from selenium.common import NoSuchElementException, InvalidSelectorException
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains

from utilits import normalize_phone, log_print

download_directory = "/home/user/Autorun/SBIS_contacts"
options = ChromeOptions()
options.add_argument('--allow-profiles-outside-user-dir')
options.add_argument('--enable-profile-shortcut-manager')
options.add_argument('--profile-directory=Profile 1')
options.add_argument(r'user-data-dir=.\User')
options.add_argument("--headless")  # Выполнение в фоновом режиме без открытия браузера
options.add_argument("--window-size=1600,900")
options.add_experimental_option("prefs", {
    "download.default_directory": download_directory,
    "download.prompt_for_download": False,  # Отключение всплывающее окно загрузки
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})
driver = Chrome(options=options)
driver.implicitly_wait(5)
title = 'SBIS contact parser'  # По умолчанию было: driver.title
version = driver.capabilities['browserVersion']
driver_version = driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]
logging.debug(f"Chrome Version: {version}")
logging.debug(f"ChromeDriver Version: {driver_version}")

SBIS_LOGIN = 'leartest'
SBIS_PASSWORD = 'Leartest2007!'

input_today_name = "ws-input_" + datetime.now().strftime('%Y-%m-%d')

@log_print
def move_and_click(element):
    ActionChains(driver).move_to_element(element).click().perform()
    return True


def xpath_find(xpath: str):
    result = driver.find_element(By.XPATH, xpath)
    return result


def xpath_finds(xpath: str):
    result = driver.find_elements(By.XPATH, xpath)
    return result

@log_print
def sbis_login():
    time.sleep(2)
    login_box = driver.find_element(By.NAME, input_today_name)
    login_box.send_keys(SBIS_LOGIN)

    submit_button_xpath = "//span[@class='controls-BaseButton controls-Button_filled controls-Button_radius-filled controls-Button_hoverIcon controls-Button_clickable controls-Button_filled_style-primary controls-Button_bg-contrast controls-Button_circle_height-4xl controls-fontsize-m controls-Button_button__wrapper-fontsize-m controls-Button_filled_shadow-big controls-notFocusOnEnter auth-AdaptiveLoginForm__loginButton controls-margin_left-m ws-flex-shrink-0 controls-inlineheight-4xl controls-Button-inlineheight-4xl controls-Button_filled_4xl']"
    submit_button = xpath_find(submit_button_xpath)
    move_and_click(submit_button)
    time.sleep(1)

    password_box = driver.find_elements(By.NAME, input_today_name)[1]
    move_and_click(password_box)
    password_box.send_keys(SBIS_PASSWORD)

    submit_button = xpath_find(submit_button_xpath)  # ДА, ТАК НАДО
    move_and_click(submit_button)
    return True


def sbis_contact_search(contact_phone_number: str):
    phone = normalize_phone(contact_phone_number)
    try:  # Если при загрузке найден элемент со страницы авторизации, выполняет скрипт авторизации
        driver.get('https://online.sbis.ru/page/crm-clients')
        if len(xpath_finds("//div[@class='auth-AuthTemplate__browserWarning']")) > 0:
            sbis_login()

        contact_search_field = driver.find_element(By.NAME, input_today_name)
        contact_search_field.send_keys(phone)  # Находит поле поиска, ищет через него компанию по номеру и ждёт, пока поиск прогрузится
        time.sleep(1.5)

        clients = xpath_finds(
            "//div[@class='crm_ClientMain__item crm_ClientMain__item ws-ellipsis ws-flexbox ws-flex-column']")
        if clients is []:   # Кликает на первую позицию в поиске и ждёт, когда откроется
            return None
        if type(clients) is list:
            move_and_click(clients[0])
        else:
            move_and_click(clients)
        time.sleep(1.5)

        try:  # Нажимает кнопку "Еще ..." в списке контактов, если она есть. Обычно появляется, если контактов больше 7
            more_button = xpath_finds(
                "//span[@class='controls-BaseButton__text controls-text-listMore controls-Button_text-listMore controls-Button__text-listMore_viewMode-link controls-Button__text_viewMode-link'")
            move_and_click(more_button)
        except InvalidSelectorException:
            pass

        if len(expand_buttons := xpath_finds(
                "//span[@class='controls-fontsize-m cd-ItemTemplate__showMoreContacts controls-margin_left-2xl controls-padding_left-3xs']")) > 0:
            for button in expand_buttons:  # Нажимает кнопки раскрытия контакта, если они есть
                move_and_click(button)
                time.sleep(0.4)

        company_name = xpath_find('//div[@class="controls-Tabs__item_overflow"]').text
        contacts = xpath_finds(
            "//div[@class='controls-ListView__itemV-relative controls-ListView__itemV js-controls-ListView__editingTarget  controls-ListView__itemV_cursor-default  controls-ListView__item_default controls-ListView__item_showActions js-controls-ListView__measurableContainer controls-ListView__item__unmarked_default controls-ListView__item_roundBorder_topLeft_l controls-ListView__item_roundBorder_topRight_l controls-ListView__item_roundBorder_bottomLeft_l controls-ListView__item_roundBorder_bottomRight_l controls-Tree__item  controls-ListView__item-leftPadding_null cd-ContactsView__itemTemplate cd-ContactsTreeView__item cd-ContactsTreeView__root-item undefined controls-margin_bottom-3xs']")
        for contact in contacts:   # Сохраняет имя компании, ищет контакты и возвращает имя владельца номера
            contact_name = None
            contact_info = contact.text.split('\n')
            for field in contact_info:
                if field[0].isalpha():
                    contact_name = field
                if field[0].isdigit():
                    if phone == normalize_phone(field):
                        return f'{company_name} | {contact_name}' if contact_name else f'{company_name}'

    except NoSuchElementException as e:
        logging.info(e)
        return None

@log_print
def get_sbis_contacts_xlsx():
    try:  # Если при загрузке найден элемент со страницы авторизации, выполняет скрипт авторизации
        driver.get('https://online.sbis.ru/page/crm-clients')
        if len(xpath_finds("//div[@class='auth-AuthTemplate__browserWarning']")) > 0:
            sbis_login()

        toggle_operations_button = xpath_find('//i[@class="controls-Button__icon controls-BaseButton__icon controls-icon_size-m controls-icon_style-secondary controls-icon icon-Check2"]')
        move_and_click(toggle_operations_button)  # Кнопка "Отметить"
        time.sleep(1.5)

        fill_all_radiobutton = xpath_find('//div[@data-qa="controls-CheckboxMarker"]')
        move_and_click(fill_all_radiobutton)  # Круглая кнопка "Отметить все"

        unload_button = xpath_find('//i[@class="controls-Button__icon controls-BaseButton__icon controls-icon_size-s controls-icon_style-secondary controls-icon icon-Save"]')
        move_and_click(unload_button)  # Кнопка "Выгрузить" вверху

        download_button = xpath_find('//div[@title="Номера телефонов"]')
        move_and_click(download_button)  # Пункт "Номера телефонов"

        while True:  # Проверка, что файл полностью загружен
            if os.path.exists(download_directory + '/Клиенты_CRM.xlsx'):
                logging.info(f"File downloaded successfully: {download_directory}/Клиенты_CRM.xlsx")
                return True
            else:
                time.sleep(1)

    except NoSuchElementException as e:
        logging.warning("ERROR, NO SUCH ELEMENT:", e)
        return None

    finally:
        driver.quit()


if __name__ == '__main__':
    get_sbis_contacts_xlsx()
