from application import create_app
from application.subscriber_payment import ThreadedConsumer
from application.auth import RsaSingleton
from application import log

app = create_app()

ThreadedConsumer('sagas_commands', 'payment.reserved', ThreadedConsumer.payment_reserved_accepted)
ThreadedConsumer('sagas_commands', 'payment.reserved.denied', ThreadedConsumer.payment_reserve_cancelled)

# request jwt public key
RsaSingleton.request_public_key()

app.app_context().push()

log.create_log('Application initialized', 'info')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13004)
