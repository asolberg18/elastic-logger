#!/bin/bash

# script to run elastic-logger in a Docker container

docker build --tag elastic_logger:1.0 .
docker run \
    -it --rm  \
    --env ELASTIC_USERID="${ELASTIC_USERID}" \
    --env ELASTIC_PASSWORD="${ELASTIC_PASSWORD}" \
    --env ELASTIC_INDEX="${ELASTIC_INDEX}" \
    --env KAFKA_CHANNEL="${KAFKA_CHANNEL}" \
    --env KAFKA_HOST="${KAFKA_HOST}" \
    --env KAFKA_GROUP="${KAFKA_GROUP}" \
    --name elastic_logger \
    elastic_logger:1.0
# docker logs --follow elastic_logger
