from application import create_app
from application.subscriber_machine import ThreadedConsumer
from application.auth import RsaSingleton

app = create_app()

ThreadedConsumer('event_exchange', 'order.payed', ThreadedConsumer.start_producing)

# request jwt public key
RsaSingleton.request_public_key()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13002)
