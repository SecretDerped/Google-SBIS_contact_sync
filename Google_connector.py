import logging
import os.path
import traceback

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

from utilits import log_print

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

console_out = logging.StreamHandler()
file_log = logging.FileHandler("application.log", mode="w")
logging.basicConfig(handlers=(file_log, console_out), level=logging.INFO,
                    format='[%(asctime)s | %(levelname)s]: %(message)s')

SERVICE_ACCOUNT_FILE = "/home/user/PycharmProjects/Google-SBIS_contact_sync/credentials.json"

class GoogleManager:
    def __init__(self, scopes):
        self.scopes = scopes
        self.service = None

    def get_creds(self):
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(SERVICE_ACCOUNT_FILE, self.scopes)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return creds

    def on_service(func):
        def _wrapper(self, *args, **kwargs):
            try:
                if self.service is None:
                    self.service = build("people", "v1", credentials=self.get_creds())
                return func(self, *args, **kwargs)
            except HttpError:
                logging.warning(traceback.format_exc())
        return _wrapper

    @on_service
    def get_contacts(self):
        next_page_token = None
        contact_list = list()

        while True:
            results = self.service.people().connections().list(
                resourceName="people/me",
                pageSize=2000,
                pageToken=next_page_token,
                personFields="names,phoneNumbers",
            ).execute()
            connections = results.get("connections", [])
            for person in connections:
                contact_list.append(person)

            next_page_token = results.get('nextPageToken')
            if not next_page_token:
                return contact_list

    @log_print
    @on_service
    def create_contact(self, name: str = '-', phone: str = '-'):

        contact_body = {
            "names": [{"unstructuredName": name}],
            "phoneNumbers": [{'value': phone, 'type': 'mobile'}]
        }
        contact_result = self.service.people().createContact(body=contact_body).execute()
        return contact_result

    @on_service
    def delete_contact(self, contact_resource: str):
        self.service.people().deleteContact(resourceName=contact_resource).execute()
        logging.info(f"Contact was deleted: {contact_resource}")

    def get_contacts_dict(self):
        contacts = {}
        contacts_book = self.get_contacts()
        for person in contacts_book:
            name = person.get("names", [])
            if name:
                name = name[0].get("displayName")
            phone_numbers = person.get('phoneNumbers', [])
            for number_info in phone_numbers:
                phone_numbers = number_info.get('value')
                contacts[phone_numbers] = name
        return contacts

    def search_contact(self, phone):
        contacts_book = self.get_contacts()
        for person in contacts_book:
            phone_numbers = person.get('phoneNumbers', [])
            for number_info in phone_numbers:
                if number_info.get('value') == phone:
                    return person
        return None


if __name__ == "__main__":
    google = GoogleManager(["https://www.googleapis.com/auth/contacts"])
    print(google.search_contact('88619368001'))
