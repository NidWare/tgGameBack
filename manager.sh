#!/bin/bash

function start() {
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
