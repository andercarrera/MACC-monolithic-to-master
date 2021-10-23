from application import create_app
from application.subscriber_payment import ThreadedConsumer

app = create_app()

ThreadedConsumer('event_exchange', 'order.created', ThreadedConsumer.check_balance)

app.app_context().push()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13004)