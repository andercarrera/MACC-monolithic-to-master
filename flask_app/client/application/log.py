from .publisher_client import publish_log


def create_log(message, log_type):
    log = {
        'microservice': 'client',
        'message': message,
        'type': log_type
    }
    publish_log(log)
