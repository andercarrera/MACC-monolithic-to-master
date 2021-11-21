from .publisher_order import publish_log


def create_log(message, log_type):
    log = {
        'microservice': 'order',
        'message': message,
        'type': log_type
    }
    publish_log(log)
