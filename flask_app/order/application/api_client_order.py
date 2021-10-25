import requests
from .config_order import Config

base_url_machine = "http://{}:{}/".format(Config.MACHINE_IP, Config.GUNICORN_PORT)


# Order API #########################################################################################################

def delete_pieces(order):
    delete_url = str(base_url_machine + "delete_pieces")
    delete_data = {"order_id": order.id}
    requests.post(delete_url, json=delete_data)
