import requests

base_url_order = "http://localhost:13003/"


# Piece API #########################################################################################################

def piece_finished(order_id):
    url = str(base_url_order + "piece_finished/{}".format(order_id))
    requests.post(url, None)
