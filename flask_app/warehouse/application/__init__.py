from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .BLConsul import BLConsul
from .config_warehouse import Config

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
        from . import routes_warehouse
        from . import model_warehouse
        consul = BLConsul.get_instance()
        consul.init_and_register(app)
        model_warehouse.Base.metadata.create_all(engine)
        return app
