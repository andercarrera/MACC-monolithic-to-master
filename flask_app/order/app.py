from application import create_app
from application import log
from application.auth import RsaSingleton
from application.subscriber_order import ThreadedConsumer

app = create_app()

ThreadedConsumer('event_exchange', 'machine.piece_finished', ThreadedConsumer.piece_finished)
ThreadedConsumer('sagas_commands', 'sagas.payment', ThreadedConsumer.payment_response)
ThreadedConsumer('sagas_commands', 'sagas.delivery', ThreadedConsumer.delivery_response)

# request jwt public key
RsaSingleton.request_public_key()

app.app_context().push()

log.create_log('Application initialized', 'info')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13003)
