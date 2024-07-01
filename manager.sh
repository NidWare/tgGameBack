#!/bin/bash

IMAGE_NAME="fastapi-app"
DB_PATH="$(pwd)/data"

function start() {
    mkdir -p $DB_PATH
    docker build -t $IMAGE_NAME .
    docker run -d --name $IMAGE_NAME -p 80:80 -v $DB_PATH:/data $IMAGE_NAME
}

function stop() {
    docker stop $IMAGE_NAME
    docker rm $IMAGE_NAME
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
        ;;
esac
