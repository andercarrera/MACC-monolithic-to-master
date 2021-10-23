from os import environ
from dotenv import load_dotenv

# Only needed for developing, on production Docker .env file is used
load_dotenv()


class Config:
    """Set Flask configuration vars from .env file."""
    # Database
    SQLALCHEMY_DATABASE_URI = environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = environ.get("SQLALCHEMY_TRACK_MODIFICATIONS")

    ORDER_IP = environ.get("ORDER_IP")

    CLIENT_IP = environ.get("CLIENT_IP")
    GUNICORN_PORT = environ.get("GUNICORN_PORT")

    """ Set RabbitMQ env vars """

    RABBITMQ_IP = environ.get("RABBITMQ_IP")
    RABBITMQ_USER = environ.get("RABBITMQ_USER")
    RABBITMQ_PASS = environ.get("RABBITMQ_PASS")

    CA_CERTS = environ.get("RABBITMQ_CA_CERT")
    KEY_FILE = environ.get("RABBITMQ_CLIENT_KEY")
    CERT_FILE = environ.get("RABBITMQ_CLIENT_CERT")

