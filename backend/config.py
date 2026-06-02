import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SESSION_TYPE = os.getenv('SESSION_TYPE', 'filesystem')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')
    
    @staticmethod
    def validate_config():
        """Validate that required environment variables are set"""
        if not Config.SQLALCHEMY_DATABASE_URI:
            raise ValueError("DATABASE_URL environment variable is required but not set")
