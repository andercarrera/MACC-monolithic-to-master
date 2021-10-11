from flask_app.monolithic.application.machine import create_app

app = create_app()
app.app_context().push()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=13000)