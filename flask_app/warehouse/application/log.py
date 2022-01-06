from .publisher_warehouse import publish_log


def create_log(message, log_type):
    log = {
        'microservice': 'warehouse',
        'message': message,
        'type': log_type
    }
    publish_log(log)
