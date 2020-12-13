import time
import argparse
import json
import sys
import os
import asyncio
from queue import Queue, Empty
from threading import Thread
from kafka import KafkaConsumer

from .task_engine import TaskEngine
from .log_event import LogEvent
from .es_logger import ElasticLogger

# Set up the command line parser
parser = argparse.ArgumentParser(description="Command description.")
# the program takes only one argument:
# karka: run the Kafka->ElasticSearch logger
# init: Initialize the ElasticSearch index and schema
# query: Run the specified query (from stdin)
# delete: Delete the ElasticSearch index
# show: Show the ElasticSearch index metadata and schema
parser.add_argument("command", choices=[
                    "kafka", "init", "query", "delete", "show"])


def main(args):

    # Parse the command line options
    args = parser.parse_args(args)

    # Read the Kafka and ES parameters from env vars
    kafka_channel = os.getenv("KAFKA_CHANNEL")
    kafka_host = os.getenv("KAFKA_HOST")
    kafka_group = os.getenv("KAFKA_GROUP")
    elastic_index = os.getenv("ELASTIC_INDEX")

    # Reads data from the Kafka topic
    # and pushes the events onto a Queue
    # This function is intended to run on a background thread
    # The passed in Queue object is thread-safe
    def KafkaReader(q):
        print("\033[1K\rStarted Kafka Reader")
        consumer = KafkaConsumer(bootstrap_servers=kafka_host,
                                 group_id=kafka_group, auto_offset_reset='latest')
        consumer.subscribe([kafka_channel])
        # currently this never returns (I could change this to have
        # a terminating condition).
        while True:
            for message in consumer:
                # This blocks if the queue is at full capacity
                # (derault 1000 items)
                # This is desired behavior as this is on
                # a background thread
                q.put(message, block=True)
            # Sleep briefly when there are no pending messages
            time.sleep(0.01)

    # Main message processing loop.
    # parameters:
    # engine: The async TaskEngine manager
    async def elastic_kafka(engine):
        print("\033[1K\rSourcing Kafka channel {} to ElasticSearch index {}".format(
            kafka_channel, elastic_index))
        # The queu used to pass messages from the background thread
        q = Queue(maxsize=1000)
        # Run the Kafka Reader on a background thread
        Thread(target=KafkaReader, args=(q, )).start()
        # Run indefinitely - perhaps add a terminating condition later
        while True:
            try:
                # Fetch a record from the queue
                # if none is available, this will not block
                # rather, it will throw an Empty exception
                event = q.get(block=False)
            except Empty:
                # If no records are available, briefly sleep
                # and continue polling
                await asyncio.sleep(0.01)
                continue
            # Create a LogEvent object using the from_kafka factory
            event = LogEvent.from_kafka(json.loads(event.value))
            # Start an async task to log the event to ElasticSearch
            await engine.start_task(event.log, engine.logger)

    # Initialize the ElasticSearch schema
    async def init_logger(engine):
        await engine.start_task(engine.logger.init_schema)

    # Run the specified query against the ES index
    async def query_logger(engine):
        # The query json is read from standard in
        # This can be piped into the command line
        query = json.load(sys.stdin)
        await engine.start_task(engine.logger.query, query)

    # Delete the ES index
    # Careful! No confirmation!
    async def delete_index(engine):
        await engine.start_task(engine.logger.delete_index)

    # Display metadata/schema of the ES index
    async def show_index(engine):
        await engine.start_task(engine.logger.get_schema)

    # Create an instance of the TaskEngine
    # with 100 maximum concurrent non-blocking (async) tasks
    engine = TaskEngine(monitor=True, logger=ElasticLogger(
        LogEvent.schema), max_tasks=100)

    # process based on the specified CLI command
    if args.command == 'kafka':

        # Run the main Kafka->ES flow
        engine.run(elastic_kafka)
        print("{} events transferred".format(LogEvent.logged))

    elif args.command == 'init':

        # Initialize Schema
        engine.run(init_logger)
        print("Schema generated")

    elif args.command == 'query':

        # Run a query
        engine.run(query_logger)
        print("Query finished")

    elif args.command == 'delete':

        # Delete the index
        engine.run(delete_index)
        print("Index deleted")

    elif args.command == 'show':

        # Show metadata/schema
        engine.run(show_index)
