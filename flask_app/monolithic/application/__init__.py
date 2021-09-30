from flask import Flask
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from .config import Config

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
        from .machine import routes_machine
        from .machine import api_client_machine
        from .machine import model_machine
        from .order import routes_order
        from .order import api_client_order
        from .order import model_order
        from .delivery import model_delivery
        from .delivery import api_client_delivery
        from .delivery import routes_delivery

        model_machine.Base.metadata.create_all(engine)
        model_order.Base.metadata.create_all(engine)
        model_delivery.Base.metadata.create_all(engine)
        return app
