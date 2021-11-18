from application import create_app
from application.subscriber_order import ThreadedConsumer
from application.auth import RsaSingleton

app = create_app()

ThreadedConsumer('event_exchange', 'payment.Accepted', ThreadedConsumer.status_accepted)
ThreadedConsumer('event_exchange', 'payment.Denied', ThreadedConsumer.status_denied)
ThreadedConsumer('event_exchange', 'machine.piece_finished', ThreadedConsumer.piece_finished)
ThreadedConsumer('event_exchange', 'delivery.delivered', ThreadedConsumer.order_delivered)

# request jwt public key
RsaSingleton.request_public_key()

app.app_context().push()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13003)
