import requests
from .config_machine import Config

base_url_order = "http://{}:{}/".format(Config.ORDER_IP, Config.GUNICORN_PORT)


# Piece API #########################################################################################################

def piece_finished(order_id):
    url = str(base_url_order + "piece_finished/{}".format(order_id))
    requests.post(url, None)
