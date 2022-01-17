FROM python:3.6-slim
ADD requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
# EXPOSE 8000
# ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
ENTRYPOINT gunicorn --certfile=certs/gunicorn.crt --keyfile=certs/gunicorn.key --bind 0.0.0.0:443 app:app
