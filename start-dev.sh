# Stop any containers still running. Don't wait for them to finish :-)
docker-compose down -t0

docker-compose up -d rabbitmq
sleep 10s
docker-compose up