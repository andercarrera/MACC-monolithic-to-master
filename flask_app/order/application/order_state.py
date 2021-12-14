from .log import create_log

class OrderState(object):
    def __init__(self, order_id, user_id, pieces):
        self.order_id = order_id
        self.user_id = user_id
        self.pieces = pieces
        self.state = pending_payment()
        create_log('SAGAS: '+self.state.get_state(), 'info')
    
    def process_payment(self, message):
        if message['status']:
            self.state = pending_delivery()
        else:
            self.state = cancelled_payment()
        create_log('SAGAS: '+self.state.get_state(), 'info')

    def process_delivery(self, message):
        if message['status']:
            self.state = accepted_delivery()
        else:
            self.state = cancelled_delivery()
        create_log('SAGAS: '+self.state.get_state(), 'info')

class State(object):
    def get_state(self):
        return "STATE"

class pending_payment(State):
    def get_state(self):
        return "PENDING PAYMENT"

class cancelled_payment(State):
    def get_state(self):
        return "CANCELLED PAYMENT"

class pending_delivery(State):
    def get_state(self):
        return "PENDING DELIVERY"

class accepted_delivery(State):
    def get_state(self):
        return "ACCEPTED DELIVERY"

class cancelled_delivery(State):
    def get_state(self):
        return "CANCELLED DELIVERY"