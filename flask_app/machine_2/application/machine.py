import json
from time import sleep

from . import publisher_machine

manufacturing_speed = 5
machine_id = 2


def produce_piece(order_id, piece_type):
    print("Manufacturing piece type {} in Machine {}".format(piece_type, machine_id), flush=True)
    sleep(manufacturing_speed)

    body = {"order_id": order_id,
            "type": piece_type,
            "machine": machine_id}

    publisher_machine.publish_msg("event_exchange", "machine.piece_finished", json.dumps(body))
