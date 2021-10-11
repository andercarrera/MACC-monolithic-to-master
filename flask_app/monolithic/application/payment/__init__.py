from flask import Flask
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from flask_app.monolithic.application.delivery.config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=True,
                bind=engine)
        )


def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)

    with app.app_context():
        from flask_app.monolithic.application.payment import routes_payment
        from flask_app.monolithic.application.payment import api_client_payment
        from flask_app.monolithic.application.payment import model_payment
        model_payment.Base.metadata.create_all(engine)

        return app
