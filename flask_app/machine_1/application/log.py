from .publisher_machine import publish_log


def create_log(message, log_type):
    log = {
        'microservice': 'machine_1',
        'message': message,
        'type': log_type
    }
    publish_log(log)
