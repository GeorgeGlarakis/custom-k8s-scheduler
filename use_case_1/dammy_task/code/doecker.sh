docker run --hostname redis --name redis -p 6379:6379 -d redis:7.4-alpine redis-server --save 60 1 --loglevel warning

docker login
docker push