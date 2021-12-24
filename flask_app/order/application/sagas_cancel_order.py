import json

from .model_order import Saga
from .publisher_order import publish_msg


class CancelOrderState(object):
    def __init__(self, order_id):
        self.order_id = order_id
        self.state = CancelDelivery()
        content = {"order_id": self.order_id,
                   "state_machine": Saga.SAGAS_CANCEL_ORDER,
                   "status": self.state.get_state(),
                   "description": None}
        publish_msg("sagas_response_exchange", "sagas_persist.cancel_order", json.dumps(content))

    def process_cancel_delivery(self):
        self.state = CancelDelivery()

        content = {"order_id": self.order_id,
                   "state_machine": Saga.SAGAS_CANCEL_ORDER,
                   "status": self.state.get_state(),
                   "description": None}
        publish_msg("sagas_response_exchange", "sagas_persist.cancel_order", json.dumps(content))

    def process_cancel_payment(self):
        self.state = CancelPayment()

        content = {"order_id": self.order_id,
                   "state_machine": Saga.SAGAS_CANCEL_ORDER,
                   "status": self.state.get_state(),
                   "description": None}
        publish_msg("sagas_response_exchange", "sagas_persist.cancel_order", json.dumps(content))

    def process_cancel_order(self):
        self.state = CancelOrder()


class MachineState(object):
    def get_state(self):
        return "STATE"


class CancelDelivery(MachineState):
    def get_state(self):
        return "Delivery cancelled"


class CancelPayment(MachineState):
    def get_state(self):
        return "Payment cancelled"


class CancelOrder(MachineState):
    def get_state(self):
        return "Order cancelled"
