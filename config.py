import os
from dotenv import load_dotenv

load_dotenv('.env', override=True)

class Config:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    MONGODB_URI = os.getenv("MONGODB_URI")
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USERNAME = os.getenv("EMAIL_USERNAME")
    SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")
    KROGER_CLIENT_ID = os.getenv("KROGER_CLIENT_ID")
    KROGER_CLIENT_SECRET = os.getenv("KROGER_CLIENT_SECRET")
    SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")