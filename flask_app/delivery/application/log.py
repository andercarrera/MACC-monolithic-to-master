from .publisher_delivery import publish_log


def create_log(message, log_type):
    log = {
        'microservice': 'delivery',
        'message': message,
        'type': log_type
    }
    publish_log(log)
