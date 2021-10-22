from application import create_app
from application.auth import RsaSingleton

app = create_app()

# request jwt public key
RsaSingleton.request_public_key()
app.app_context().push()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13003)
