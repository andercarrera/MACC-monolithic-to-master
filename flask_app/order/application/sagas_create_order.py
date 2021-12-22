import json

from .model_order import Saga
from .publisher_order import publish_msg


class CreateOrderState(object):
    def __init__(self, order_id, user_id, pieces):
        self.order_id = order_id
        self.user_id = user_id
        self.pieces = pieces
        self.state = pending_payment()
        content = {"order_id": self.order_id,
                   "state_machine": Saga.SAGAS_CREATE_ORDER,
                   "status": self.state.get_state(),
                   "description": "Order created"}
        publish_msg("sagas_commands", "sagas.persist", json.dumps(content))

    def process_payment(self, message):
        if message['status']:
            self.state = pending_delivery()

            content = {"order_id": self.order_id,
                       "state_machine": Saga.SAGAS_CREATE_ORDER,
                       "status": self.state.get_state(),
                       "description": "Credit reserved"}
            publish_msg("sagas_commands", "sagas.persist", json.dumps(content))
        else:
            self.state = cancelled_payment()

    def process_delivery(self, message):
        if message['status']:
            self.state = accepted_delivery()

            content = {"order_id": self.order_id,
                       "state_machine": Saga.SAGAS_CREATE_ORDER,
                       "status": "Order accepted",
                       "description": "Correct ZIP code"}
            publish_msg("sagas_commands", "sagas.persist", json.dumps(content))
        else:
            self.state = cancelled_delivery()

            content = {"order_id": self.order_id,
                       "state_machine": Saga.SAGAS_CREATE_ORDER,
                       "status": "Release reserved credit",
                       "description": "Invalid ZIP code"}
            publish_msg("sagas_commands", "sagas.persist", json.dumps(content))


class MachineState(object):
    def get_state(self):
        return "STATE"


class pending_payment(MachineState):
    def get_state(self):
        return "Pending Payment"


class cancelled_payment(MachineState):
    def get_state(self):
        return "CANCELLED PAYMENT"


class pending_delivery(MachineState):
    def get_state(self):
        return "Pending delivery"


class accepted_delivery(MachineState):
    def get_state(self):
        return "ACCEPTED DELIVERY"


class cancelled_delivery(MachineState):
    def get_state(self):
        return "CANCELLED DELIVERY"
