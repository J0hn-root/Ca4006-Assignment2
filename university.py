#!/usr/bin/env python
from pika import BlockingConnection, ConnectionParameters
from pika.spec import Basic, BasicProperties
from pika.adapters.blocking_connection import BlockingChannel
import json
import pickle
from university_database import UniversityDatabase
from datetime import datetime

class University(object):

    DATA_FILE: str = "university.pickle"
    database: UniversityDatabase

    def __init__(self) -> None:
        try:
            #read data from file
            with open(self.DATA_FILE, 'rb') as f:
                self.database = pickle.load(f)
        except FileNotFoundError:
            # initialize funds and history
            self.database = UniversityDatabase()

        #Connect to RabbitMQ
        connection = BlockingConnection(ConnectionParameters(host='localhost'))
        channel = connection.channel()

        #durable = True -> queue won't be lost on restarts
        channel.queue_declare(queue='create_project_account', durable=True)
        print(' [*] Waiting for messages. To exit press CTRL+C')

        #Fair dispatch, no more than one message to a worker at a time
        #To avoid race condition
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='create_project_account', on_message_callback=self.callback)

        channel.start_consuming()

    def callback(self, ch: BlockingChannel, method: Basic.Deliver, props: BasicProperties, body: bytes) -> None:
        print(" [x] Received Create Project Account Request")
        request = json.loads(body)

        self.database.create_research_account(request['title'], request['researcher'], request['budget'],  datetime.strptime(request['end_date'], '%d-%m-%Y').date())

        # save database to file
        with open(self.DATA_FILE, 'wb') as f:
            pickle.dump(self.database, f)

        self.database.access_details(request['researcher'])

        print(" [x] Done")
        # notify that the account has been created
        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    university = University()