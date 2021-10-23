from os import environ
from dotenv import load_dotenv

# Only needed for developing, on production Docker .env file is used
load_dotenv()


class Config:
    """Set Flask configuration vars from .env file."""
    # Database
    SQLALCHEMY_DATABASE_URI = environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = environ.get("SQLALCHEMY_TRACK_MODIFICATIONS")

    DELIVERY_IP = environ.get("DELIVERY_IP")
    MACHINE_IP = environ.get("MACHINE_IP")
    PAYMENT_IP = environ.get("PAYMENT_IP")
    RABBITMQ_IP = environ.get("RABBITMQ_IP")

    GUNICORN_PORT = environ.get("GUNICORN_PORT")
    RABBITMQ_PORT = environ.get("RABBITMQ_PORT")
    # print(SQLALCHEMY_DATABASE_URI)
