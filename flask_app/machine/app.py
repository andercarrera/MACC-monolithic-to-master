from application import create_app
from application.subscriber_machine import ThreadedConsumer
from application.auth import RsaSingleton
from application import log

app = create_app()

ThreadedConsumer('event_exchange', 'machine.produce_piece', ThreadedConsumer.produce_piece)
ThreadedConsumer('event_exchange', 'order.deleted', ThreadedConsumer.delete_pieces)

# request jwt public key
RsaSingleton.request_public_key()

log.create_log('Application initialized', 'info')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13002)
