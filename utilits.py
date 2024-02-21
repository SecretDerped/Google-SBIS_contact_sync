import logging
import openpyxl
import time
import re

console_out = logging.StreamHandler()
file_log = logging.FileHandler("application.log", mode="w")
logging.basicConfig(handlers=(file_log, console_out), level=logging.INFO,
                    format='[%(asctime)s | %(levelname)s]: %(message)s')


def log_print(func):
    def _wrapper(*args, **kwargs):
        logging.info(f'Call - {func.__name__}{args} {kwargs}')
        start_time = time.time()
        result = func(*args, **kwargs)
        exec_time = time.time() - start_time
        logging.info(f'Result ({exec_time:.3f} sec.) - {func.__name__}{args} {kwargs}: {result}')
        return result
    return _wrapper


def find_phone_numbers(text):
    pattern = r'\b\d{4,15}\b'
    return re.findall(pattern, text)


def normalize_phone(number):
    number = re.sub("[(|)|\-| ]", "", number)
    if number.startswith('+7'):
        number = '8' + number[2:]
    return number

@log_print
def read_contacts_xlsx(file_path: str):
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active  # Выбор активного листа
    phone_book = {}
    for row in sheet.iter_rows(min_row=2, values_only=True):  # Начинаем со второй строки, если есть заголовок
        client_name = row[0]  # Название или ФИО из первого столбца
        for cell in row[4:8]:  # Номера расположены с 4-й по 8-й столбец
            if cell is not None:
                numbers = cell.split(';')
                for number in numbers:
                    found_numbers = find_phone_numbers(number)  # Очистка и поиск номеров телефонов
                    for found_number in found_numbers:
                        phone_book[found_number] = client_name
    return phone_book


if __name__ == '__main__':
    file_path = '/home/user/Autorun/SBIS_contacts/Клиенты_CRM.xlsx'
    sbis_contacts = read_contacts_xlsx(file_path)
    for phone, name in sbis_contacts.items():
        print(f"{phone}: {name}")
