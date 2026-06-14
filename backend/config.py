import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SESSION_TYPE = os.getenv('SESSION_TYPE', 'filesystem')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')

    # Flask-Mail (Gmail SMTP)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_USERNAME')

    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

    @staticmethod
    def validate_config():
        if not Config.SQLALCHEMY_DATABASE_URI:
            raise ValueError("DATABASE_URL environment variable is required but not set")
