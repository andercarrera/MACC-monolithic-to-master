from application import create_app
from application.subscriber_logs import ThreadedConsumer

app = create_app()

ThreadedConsumer('event_exchange', '#', ThreadedConsumer.get_logs)

app.app_context().push()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13005)
