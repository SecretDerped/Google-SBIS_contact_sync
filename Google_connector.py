import logging
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

console_out = logging.StreamHandler()
file_log = logging.FileHandler("application.log", mode="w")
logging.basicConfig(handlers=(file_log, console_out), level=logging.INFO,
                    format='[%(asctime)s | %(levelname)s]: %(message)s')


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
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", self.scopes)
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
            except HttpError as err:
                logging.warning(err)
        return _wrapper


    @on_service
    def get_contacts_dict(self):
        next_page_token = None
        contacts = {}

        while True:
            results = self.service.people().connections().list(
                resourceName="people/me",
                pageSize=2000,
                pageToken=next_page_token,
                personFields="names,phoneNumbers",
            ).execute()

            connections = results.get("connections", [])

            for person in connections:
                print(person)
                name = person.get("names", [])[0].get("displayName")
                phone_number = person.get('phoneNumbers', [])
                for info in phone_number:
                    phone_number = info.get('value')
                    contacts[phone_number] = name

            next_page_token = results.get('nextPageToken')
            if not next_page_token:
                break
        return contacts


    @on_service
    def search_contact(self, contact_phone: str = ''):
        contacts = self.get_contacts_dict()
        for contact in contacts:
            if contact['number'] == contact_phone:
                return f'{contact["name"]}: {contact["number"]}'
        return None


    @on_service
    def create_contact(self, name: str, phone: str):
        contact_body = {
            "names": [{"unstructuredName": name}],
            "phoneNumbers": [{'value': phone, 'type': 'mobile'}]
        }
        contact_result = self.service.people().createContact(body=contact_body).execute()
        logging.info(f"Create contact: {name}, {phone}")
        return contact_result


if __name__ == "__main__":
    google = GoogleManager(["https://www.googleapis.com/auth/contacts"])
    contacts = google.get_contacts_dict()
    for phone, name in contacts.items():
        print(phone, name)
    #print(json.dumps((google.get_contacts_info()), indent=4, ensure_ascii=False, sort_keys=True))
