#!/bin/bash

DB_PATH="$(pwd)/data"

function start() {
    mkdir -p $DB_PATH
    docker-compose up -d
}

function stop() {
    docker-compose down
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
