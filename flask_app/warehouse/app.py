from application import create_app
from application.subscriber_warehouse import ThreadedConsumer
from application.auth import RsaSingleton
from application import log

app = create_app()

ThreadedConsumer('sagas_commands', 'order.paid', ThreadedConsumer.start_producing)

ThreadedConsumer('event_exchange', 'machine.piece_finished', ThreadedConsumer.piece_finished)

ThreadedConsumer('event_exchange', 'delivery.delivered', ThreadedConsumer.pieces_delivered)

ThreadedConsumer('sagas_commands', 'order.cancel', ThreadedConsumer.cancel_order)


# request jwt public key
RsaSingleton.request_public_key()

app.app_context().push()

log.create_log('Application initialized', 'info')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13004)
