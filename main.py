import logging
import os

import Google_connector
from SBIS_contact_poolinng import get_sbis_contacts_xlsx
from utilits import read_contacts_xlsx

console_out = logging.StreamHandler()
file_log = logging.FileHandler("application.log", mode="w")
logging.basicConfig(handlers=(file_log, console_out), level=logging.INFO,
                    format='[%(asctime)s | %(levelname)s]: %(message)s')


if __name__ == "__main__":
    google = Google_connector.GoogleManager(["https://www.googleapis.com/auth/contacts"])
    file_path = '/home/user/Autorun/SBIS_contacts/Клиенты_CRM.xlsx'
    if os.path.exists(file_path):
        os.remove(file_path)
    if get_sbis_contacts_xlsx():
        google_contacts = google.get_contacts_dict()
        sbis_contacts = read_contacts_xlsx(file_path)
        for phone, name in sbis_contacts.items():
            if phone in google_contacts.keys():
                continue
            else:
                google.create_contact(name, phone)
