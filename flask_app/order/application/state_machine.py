import json

from .publisher_order import publish_msg


class Coordinator(object):
    def __init__(self):
        self.order_state_list = list()

    def process_create_order(self, message):
        order_state = self.__get_order_from_list(message['order_id'])
        if message['type'] == 'PAYMENT':
            order_state.process_payment(message)
            if order_state.state.get_state() == 'Pending delivery':
                publish_msg("sagas_commands", "delivery.create", json.dumps(message))
            if order_state.state.get_state() == 'CANCELLED PAYMENT':
                publish_msg("sagas_commands", "order.cancel", json.dumps(message))
        if message['type'] == 'DELIVERY':
            order_state.process_delivery(message)
            if order_state.state.get_state() == 'ACCEPTED DELIVERY':
                publish_msg("sagas_commands", "payment.accepted", json.dumps(message))
                publish_msg("sagas_commands", "order.paid", json.dumps(message))
            else:
                publish_msg("sagas_commands", "payment.reserved.denied", json.dumps(message))
            self.order_state_list.remove(order_state)

    def __get_order_from_list(self, order_id):
        for order_state in self.order_state_list:
            if order_state.order_id == order_id:
                return order_state
        return None


coordinator = Coordinator()


def get_coordinator():
    return coordinator
