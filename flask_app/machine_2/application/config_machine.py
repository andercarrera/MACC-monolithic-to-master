import json
from os import environ

import boto3 as boto3
import netifaces as ni
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

    client = boto3.client('secretsmanager')

    if environ.get("RABBITMQ_USER") is not None:
        RABBITMQ_USER = environ.get("RABBITMQ_USER")
    else:
        rabbitmq_user_secret = client.get_secret_value(SecretId='rabbitmq_user')
        RABBITMQ_USER = json.loads(rabbitmq_user_secret['SecretString'])['rabbitmq_user']

    if environ.get("RABBITMQ_PASS") is not None:
        RABBITMQ_PASS = environ.get("RABBITMQ_PASS")
    else:
        rabbitmq_user_secret = client.get_secret_value(SecretId='rabbitmq_password')
        RABBITMQ_PASS = json.loads(rabbitmq_user_secret['SecretString'])['rabbitmq_password']

    CA_CERTS = environ.get("RABBITMQ_CA_CERT")
    KEY_FILE = environ.get("RABBITMQ_CLIENT_KEY")
    CERT_FILE = environ.get("RABBITMQ_CLIENT_CERT")

    # Consul
    CONSUL_IP = environ.get("CONSUL_IP", "192.168.17.16")
    SERVICE_NAME = environ.get("SERVICE_NAME", "machine2")
    SERVICE_ID = environ.get("SERVICE_ID", "machine2")
    IP = environ.get("FLASK_IP")
    PORT = int(environ.get("MACHINE_2_PORT", '8000'))

    __instance = None

    @staticmethod
    def get_instance():
        if Config.__instance is None:
            Config()
        return Config.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if Config.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Config.__instance = self

    @staticmethod
    def get_ip_iface(iface):
        return ni.ifaddresses(iface)[ni.AF_INET][0]['addr']
