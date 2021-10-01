import requests

base_url = "http://localhost:13000/"


def create_delivery(new_order):
    delivery_url = str(base_url + "delivery")
    delivery_data = {"order_id": new_order.id}
    requests.post(delivery_url, json=delivery_data)


def send_pieces(new_order):
    pieces_url = str(base_url + "pieces")
    pieces_data = {"number_of_pieces": new_order.number_of_pieces,
                   "order_id": new_order.id}
    requests.post(pieces_url, json=pieces_data)


def delete_order(order):
    delete_url = str(base_url + "delete_pieces")
    delete_data = {"order_id": order.id}
    requests.post(delete_url, json=delete_data)

