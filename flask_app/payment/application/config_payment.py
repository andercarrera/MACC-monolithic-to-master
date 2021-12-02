from os import environ

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
    PAYMENT_IP = environ.get("PAYMENT_IP")
    CLIENT_IP = environ.get("CLIENT_IP")

    GUNICORN_PORT = environ.get("GUNICORN_PORT")
    # print(SQLALCHEMY_DATABASE_URI)

    """ Set RabbitMQ env vars """

    RABBITMQ_IP = environ.get("RABBITMQ_IP")
    RABBITMQ_USER = environ.get("RABBITMQ_USER")
    RABBITMQ_PASS = environ.get("RABBITMQ_PASS")

    CA_CERTS = environ.get("RABBITMQ_CA_CERT")
    KEY_FILE = environ.get("RABBITMQ_CLIENT_KEY")
    CERT_FILE = environ.get("RABBITMQ_CLIENT_CERT")

    # Consul
    CONSUL_IP = environ.get("CONSUL_IP", "192.168.17.16")
    SERVICE_NAME = environ.get("SERVICE_NAME", "payment")
    SERVICE_ID = environ.get("SERVICE_ID", "payment")
    IP = None
    PORT = int(environ.get("GUNICORN_PORT", '8000'))

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
            self.get_ip()
            Config.__instance = self

    def get_ip(self):
        ifaces = ni.interfaces()
        if "br-ca1e5a751726" in ifaces:  # this is for my specific iface for debugging.
            self.IP = Config.get_ip_iface("br-ca1e5a751726")
        elif "eth0" in ifaces:  # this is the default interface in docker
            self.IP = Config.get_ip_iface("eth0")
        else:
            self.IP = "127.0.0.1"

    @staticmethod
    def get_ip_iface(iface):
        return ni.ifaddresses(iface)[ni.AF_INET][0]['addr']
