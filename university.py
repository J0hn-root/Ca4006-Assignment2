#!/usr/bin/env python
from pika import BlockingConnection, ConnectionParameters
from pika.spec import Basic, BasicProperties
from pika.adapters.blocking_connection import BlockingChannel
import json
import pickle
from university_database import UniversityDatabase
from university_request_handler import ResearcherProposalHandler, UniversityRequestHandler, CreateAccountHandler, WithdrawHandler, AddResearcherHandler, RemoveResearcherHandler, GetDetailsHandler, ListTransactionsHandler
from timer import Timer
from request_status import RequestStatus
from request_response import RequestResponse
from concurrent.futures import ThreadPoolExecutor

class University(object):

    DATA_FILE: str = "university.pickle"
    database: UniversityDatabase
    request_handler: UniversityRequestHandler
    timer: Timer = Timer("university")

    def __init__(self) -> None:
        try:
            #read data from file
            with open(self.DATA_FILE, 'rb') as f:
                self.database = pickle.load(f)
        except FileNotFoundError:
            # initialize database
            self.database = UniversityDatabase()

        # initialize responisbility chain
        self.request_handler = CreateAccountHandler()

        (self.request_handler
            .set_next_handler(WithdrawHandler())
            .set_next_handler(AddResearcherHandler())
            .set_next_handler(RemoveResearcherHandler())
            .set_next_handler(GetDetailsHandler())
            .set_next_handler(ListTransactionsHandler())
            .set_next_handler(ResearcherProposalHandler())
        )

        # two threads
        with ThreadPoolExecutor(max_workers=3) as executor:
            executor.submit(self.start)
            executor.submit(self.timer.start)

    def start(self) -> None:        
        #Connect to RabbitMQ
        connection = BlockingConnection(ConnectionParameters(host='localhost'))
        channel = connection.channel()

        """
            RPC Researcher actions setup
        """

        #Create queue for research proposal RPC
        channel.queue_declare(queue='university_requests_queue')

        #Fair dispatch, no more than one message to a worker at a time
        #To avoid race condition
        channel.basic_qos(prefetch_count=1)

        #Defining queue where callback function should receive messages from
        channel.basic_consume(queue='university_requests_queue', on_message_callback=self.process_requests)

        print(' [U] Waiting for requests.')

        #await research proposals
        channel.start_consuming()

    def process_requests(self, ch: BlockingChannel, method: Basic.Deliver, props: BasicProperties, body: bytes) -> None:
        request = json.loads(body)
        print(f" [U] Received '{request['request_type']}' request")

        #adjust timer if needed
        self.timer.adjust_timer(request["timestamp"])

        result: RequestResponse = self.request_handler.execute_request(request, self.database, self.timer)

        if result.status == RequestStatus.SUCCEEDED.value:
            # save database to file
            with open(self.DATA_FILE, 'wb') as f:
                pickle.dump(self.database, f)

            print(" [U] Changes Saved")

        # notify response
        ch.basic_publish(exchange='',
            routing_key=props.reply_to,
            properties=BasicProperties(
                correlation_id = props.correlation_id,
                content_type="application/json"
                ),
            body=result.to_json()
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    university = University()
