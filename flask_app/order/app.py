from application import create_app
from application.subscriber_order import ThreadedConsumer
from application.auth import RsaSingleton

app = create_app()

ThreadedConsumer('event_exchange', 'payment.status', ThreadedConsumer.check_status)

# request jwt public key
RsaSingleton.request_public_key()

app.app_context().push()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13003)
