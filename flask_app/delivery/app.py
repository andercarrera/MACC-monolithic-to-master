from application import create_app
from application.subscriber_delivery import ThreadedConsumer
from application.auth import RsaSingleton
from application import log

app = create_app()

ThreadedConsumer('event_exchange', 'order.created', ThreadedConsumer.create_delivery)
ThreadedConsumer('event_exchange', 'order.finished', ThreadedConsumer.start_producing)

# request jwt public key
RsaSingleton.request_public_key()

log.create_log('Application initialized', 'info')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13001)
