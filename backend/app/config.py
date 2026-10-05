from dotenv import load_dotenv
import os
load_dotenv()
from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_COOKIE_SECURE = True  # Set to True in production
    JWT_COOKIE_SAMESITE = "Lax"  # Adjust based on your needs