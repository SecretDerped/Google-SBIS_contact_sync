from fastapi import FastAPI
from Google_connector import GoogleManager


app = FastAPI()
google = GoogleManager(["https://www.googleapis.com/auth/contacts"])


@app.get("/contact/list")
async def get_contacts():
    return google.get_contacts_info()


@app.get("/contact/add")
async def create_contact(phone):
    return google.create_contact(phone)
