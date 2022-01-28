from application import create_app
from application import log
from application.auth import RsaSingleton

app = create_app()

RsaSingleton.request_public_key()
log.create_log('Application initialized', 'info')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13000)

# PYTHONUNBUFFERED=1;SQLALCHEMY_DATABASE_URI=sqlite:///monolithic.db?check_same_thread=False;SQLALCHEMY_TRACK_MODIFICATIONS=False
