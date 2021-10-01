import requests

base_url = "http://localhost:13000/"


# Piece API #########################################################################################################

def piece_finished(order_id):
    url = str(base_url + "piece_finished/{}".format(order_id))
    requests.post(url, None)
