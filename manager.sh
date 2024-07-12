#!/bin/bash

function start() {
    docker-compose up -d
}

function stop() {
    docker-compose down
}

function build() {
    docker-compose up -d --build
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    build)
        build
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
        ;;
esac
