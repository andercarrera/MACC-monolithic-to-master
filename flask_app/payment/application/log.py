from .publisher_payment import publish_log


def create_log(message, log_type):
    log = {
        'microservice': 'payment',
        'message': message,
        'type': log_type
    }
    publish_log(log)
