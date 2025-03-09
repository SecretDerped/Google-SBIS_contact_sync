import os
import logging
import time
import traceback

import Google_connector
from SBIS_parser import WebdriverProfile, reload
from utilits import read_contacts_xlsx, read_employee_xlsx

def main_job():
    browser = WebdriverProfile()
    try:
        google = Google_connector.GoogleManager(["https://www.googleapis.com/auth/contacts"])
        clients_file_path = '/home/user/Autorun/SBIS_contacts/Клиенты_CRM.xlsx'
        employees_file_path = 'Сотрудники.xlsx'
        if os.path.exists(clients_file_path):
            os.remove(clients_file_path)
            pass
        if browser.get_sbis_contacts_xlsx():
            google_contacts = google.get_contacts_dict()
            sbis_contacts = read_contacts_xlsx(clients_file_path)
            sbis_employees = read_employee_xlsx(employees_file_path)
            sbis_contacts.update(sbis_employees)
            for phone, name in sbis_contacts.items():

                if phone in google_contacts.keys():
                    continue

                if phone in sbis_employees.keys():
                    google.create_contact(name, phone)
                    continue

                full_name = browser.sbis_contact_search(phone)
                browser = reload(browser)
                if full_name is None or full_name is False:
                    full_name = name
                google.create_contact(full_name, phone)

            excess_contacts = set(google_contacts) - set(sbis_contacts)
            for phone in excess_contacts:
                contact = google.search_contact(phone)
                contact_resource = contact['resourceName']
                google.delete_contact(contact_resource)
                time.sleep(1)
            logging.info('Process done.')

    except Exception:
        logging.critical(f'{traceback.format_exc()}')

    finally:
        browser.close()