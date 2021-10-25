import bcrypt
from flask import abort
from werkzeug.exceptions import BadRequest

from application import create_app, Session
from application.model_client import Client, Role


def initDB():
    session = Session()
    clients = session.query(Client).all()
    if not clients:
        print("First execution: creating a default admin", flush=True)
        try:
            new_role = Role(name="admin")
            session.add(new_role)
            session.commit()

            new_admin = Client(
                email="admin@mondragon.edu",
                status=Client.STATUS_CREATED,
                username="admin",
                password=bcrypt.hashpw("admin".encode(), bcrypt.gensalt()).decode('utf-8'),
            )
            new_admin.roles.append(new_role)
            session.add(new_admin)
            session.commit()
        except KeyError:
            session.rollback()
            session.close()
            abort(BadRequest.code)
    session.close()


app = create_app()
initDB()
app.app_context().push()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13000)

# PYTHONUNBUFFERED=1;SQLALCHEMY_DATABASE_URI=sqlite:///monolithic.db?check_same_thread=False;SQLALCHEMY_TRACK_MODIFICATIONS=False
