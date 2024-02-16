import re
import os
import time

import requests

log_file_path = 'C:/Users/User/AppData/Local/MicroSIP/microsip_log.txt'
state_file_path = 'log_read_state.txt'
found_numbers_file_path = 'found_phone_numbers.txt'


# Функция для извлечения номеров телефонов
def find_phone_numbers(start_pos, known_numbers):
    phone_number_pattern = re.compile(r'\[CALLING\] To: <sip:([+]?[0-9]+)(?:@|>)')
    new_numbers = set()

    with open(log_file_path, 'r', encoding='utf-8') as file:
        file.seek(start_pos)
        content = file.read()
        matches = phone_number_pattern.findall(content)
        for number in matches:
            if number not in known_numbers:
                new_numbers.add(number)
                known_numbers.add(number)
        return new_numbers, file.tell()


# Функции для сохранения и загрузки состояния и найденных номеров
def save_state(state):
    with open(state_file_path, 'w') as file:
        file.write(str(state))


def load_state():
    if os.path.exists(state_file_path):
        with open(state_file_path, 'r') as file:
            return int(file.read())
    return 0


def save_found_numbers(numbers):
    with open(found_numbers_file_path, 'w') as file:
        for number in numbers:
            file.write(f"{number}\n")


def load_found_numbers():
    if os.path.exists(found_numbers_file_path):
        with open(found_numbers_file_path, 'r') as file:
            return set(line.strip() for line in file)
    return set()


# Основная логика
if __name__ == '__main__':
    while True:
        start_pos = load_state()
        known_numbers = load_found_numbers()
        new_numbers, new_pos = find_phone_numbers(start_pos, known_numbers)
        save_state(new_pos)
        for number in new_numbers:
            print(number + ' has in job...')
            #TODO: починить get
            requests.get(f'192.168.1.64:8000/contact/add?phone={number}')
        save_found_numbers(known_numbers)
        time.sleep(10)

