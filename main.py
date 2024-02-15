from fastapi import FastAPI
from Google.Google_connector import GoogleManager


app = FastAPI()
google = GoogleManager(["https://www.googleapis.com/auth/contacts"])


@app.get("/contacts")
async def get_contacts():
    return google.get_contacts_info()


@app.post("/contacts")
async def create_contact(name, phone):
    return google.create_contact(name, phone)
