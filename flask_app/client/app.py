from application import create_app

app = create_app()
app.app_context().push()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13000)

# PYTHONUNBUFFERED=1;SQLALCHEMY_DATABASE_URI=sqlite:///monolithic.db?check_same_thread=False;SQLALCHEMY_TRACK_MODIFICATIONS=False
