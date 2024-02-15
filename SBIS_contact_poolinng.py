import re
import time
from datetime import datetime

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

SBIS_LOGIN = 'leartest'
SBIS_PASSWORD = 'Leartest2007!'

options = ChromeOptions()
options.add_argument('--allow-profiles-outside-user-dir')
options.add_argument('--enable-profile-shortcut-manager')
options.add_argument(r'user-data-dir=.\User')
options.add_argument('--profile-directory=Profile 1')
options.add_argument("--window-size=1600,900")

driver = Chrome(options=options)
driver.implicitly_wait(10)
title = driver.title


wait = WebDriverWait(driver, 20)
field_universal_name = "ws-input_" + datetime.now().strftime('%Y-%m-%d')

def move_and_click(element):
    ActionChains(driver).move_to_element(element).click().perform()


def global_xpath_find(xpath: str):
    result = driver.find_element(by=By.XPATH, value=xpath)
    return result


def global_xpath_find_all(xpath: str):
    result = driver.find_elements(by=By.XPATH, value=xpath)
    return result


def close_window():
    close_button = global_xpath_find("//i[@class='controls-Button__icon controls-BaseButton__icon controls-icon_size-m controls-icon_style-label controls-icon icon-Close']")
    move_and_click(close_button)


def sbis_login():
    time.sleep(2)
    login_box = driver.find_element(By.NAME, field_universal_name)
    login_box.send_keys(SBIS_LOGIN)

    submit_button = global_xpath_find("//span[@class='controls-BaseButton controls-Button_filled controls-Button_radius-filled controls-Button_hoverIcon controls-Button_clickable controls-Button_filled_style-primary controls-Button_bg-contrast controls-Button_circle_height-4xl controls-fontsize-m controls-Button_button__wrapper-fontsize-m controls-Button_filled_shadow-big controls-notFocusOnEnter auth-AdaptiveLoginForm__loginButton controls-margin_left-m ws-flex-shrink-0 controls-inlineheight-4xl controls-Button-inlineheight-4xl controls-Button_filled_4xl']")
    move_and_click(submit_button)
    time.sleep(1)

    password_box = driver.find_elements(By.NAME, field_universal_name)[1]
    move_and_click(password_box)
    password_box.send_keys(SBIS_PASSWORD)

    submit_button = global_xpath_find("//span[@class='controls-BaseButton controls-Button_filled controls-Button_radius-filled controls-Button_hoverIcon controls-Button_clickable controls-Button_filled_style-primary controls-Button_bg-contrast controls-Button_circle_height-4xl controls-fontsize-m controls-Button_button__wrapper-fontsize-m controls-Button_filled_shadow-big controls-notFocusOnEnter auth-AdaptiveLoginForm__loginButton controls-margin_left-m ws-flex-shrink-0 controls-inlineheight-4xl controls-Button-inlineheight-4xl controls-Button_filled_4xl']")
    move_and_click(submit_button)


def sbis_contact_search(number: str):
    number = re.sub("[(|)|\-| ]","", number)
    if number.startswith('+7'):
        number = '8' + number[2:]
    try:
        # Если при загрузке найден элемент со страницы авторизации, выполняет скрипт авторизации и обновляет страницу
        driver.get('https://online.sbis.ru/page/crm-clients')
        if len(global_xpath_find_all("//div[@class='auth-AuthTemplate__browserWarning']")) > 0:
            sbis_login()

        # Находит поле поиска, ищет через него компанию по номеру и ждёт, пока прогрузится
        contact_search_field = driver.find_element(By.NAME, field_universal_name)
        contact_search_field.send_keys(number)
        time.sleep(3)

        # Кликает на первую позицию в поиске и ждёт загрузки
        clients = global_xpath_find_all("//div[@class='crm_ClientMain__item crm_ClientMain__item ws-ellipsis ws-flexbox ws-flex-column']")
        #wait.until(EC.element_to_be_clickable(clients[0]))
        move_and_click(clients[0])
        time.sleep(5)

        # Сохраняет имя компании
        company_name = global_xpath_find('//div[@class="controls-Tabs__item_overflow"]').text
        print(company_name)

        # Нажимает кнопки раскрытия контакта, если они есть
        if len(expand_buttons := global_xpath_find_all("//span[@class='controls-fontsize-m cd-ItemTemplate__showMoreContacts controls-margin_left-2xl controls-padding_left-3xs']")) > 0:
            for button in expand_buttons:
                move_and_click(button)
                time.sleep(0.5)

        """# Ищет имена контактов и номера
        user_name_xpath = f"//div[contains(div, '{number}')]/../div[3]"
        user_name_element = driver.find_element(By.XPATH, user_name_xpath)
        print(user_name_element.text)"""

        contacts = global_xpath_find_all("//div[@class='controls-ListView__itemV-relative controls-ListView__itemV js-controls-ListView__editingTarget  controls-ListView__itemV_cursor-default  controls-ListView__item_default controls-ListView__item_showActions js-controls-ListView__measurableContainer controls-ListView__item__unmarked_default controls-ListView__item_roundBorder_topLeft_l controls-ListView__item_roundBorder_topRight_l controls-ListView__item_roundBorder_bottomLeft_l controls-ListView__item_roundBorder_bottomRight_l controls-Tree__item  controls-ListView__item-leftPadding_null cd-ContactsView__itemTemplate cd-ContactsTreeView__item cd-ContactsTreeView__root-item undefined controls-margin_bottom-3xs']")
        for contact in contacts:
            #TODO: Добаботать поиск по странице компании
            try:
                contact_name = contact.find_element(by=By.XPATH, value=".//span[@data-qa='cd-ItemTemplate__assigneeName']").text
            except NoSuchElementException:
                contact_name = 'Безымянный'
            print(contact_name)
            phone_numbers = contact.find_elements(by=By.XPATH, value='.//span[@data-qa="cd-ItemTemplate__contactValue"]')
            # Записывает номера по порядку, пропускает почтовые ящики
            for number in phone_numbers:
                if '@' in number.text:
                    continue
                else:
                    contact_phone = re.sub("[(|)|\-| ]","", number.text)
                    print(contact_phone)
                    if contact_phone == number:
                        return f'{company_name} | {contact_name}'

            close_window()

    except NoSuchElementException as e:
        print("Нет элемента", e)
        driver.quit()
        return None


if __name__ == '__main__':
    sbis_contact_search('8 (34922) 5-11-81')
    driver.quit()
