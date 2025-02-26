# app/config.py
import os
from dotenv import load_dotenv
import random, string

load_dotenv()  # Load environment variables from .env file

# SMTP configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("EMAIL_USERNAME")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")

# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    JWT_SECRET_KEY = ''.join(random.choices(string.ascii_letters + string.digits, k=32))