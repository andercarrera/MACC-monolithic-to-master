from os import environ
from dotenv import load_dotenv

# Only needed for developing, on production Docker .env file is used
load_dotenv()


class Config:
    """Set Flask configuration vars from .env file."""
    # Database
    SQLALCHEMY_DATABASE_URI = environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = environ.get("SQLALCHEMY_TRACK_MODIFICATIONS")

    CLIENT_IP = environ.get("CLIENT_IP")
    GUNICORN_PORT = environ.get("GUNICORN_PORT")
