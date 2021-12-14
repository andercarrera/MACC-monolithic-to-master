from application import create_app
from application import log
from application.auth import RsaSingleton
from application.subscriber_delivery import ThreadedConsumer

app = create_app()

ThreadedConsumer('sagas_commands', 'delivery.create', ThreadedConsumer.create_delivery)
ThreadedConsumer('sagas_commands', 'delivery.cancel', ThreadedConsumer.cancel_delivery)
ThreadedConsumer('sagas_commands', 'delivery.update', ThreadedConsumer.update_delivery)

# request jwt public key
RsaSingleton.request_public_key()

log.create_log('Application initialized', 'info')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13001)
