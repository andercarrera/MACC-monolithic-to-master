# Stop any containers still running. Don't wait for them to finish :-)
docker-compose down -t0

docker-compose up -d consul
sleep 10s
docker-compose up -d haproxy
sleep 10s
docker-compose up -d rabbitmq
sleep 10s
docker-compose up -d client
sleep 5s
docker-compose up