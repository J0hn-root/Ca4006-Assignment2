#!/usr/bin/env python
from pika import BlockingConnection, ConnectionParameters
from pika.spec import Basic, BasicProperties, PERSISTENT_DELIVERY_MODE
from pika.adapters.blocking_connection import BlockingChannel
import pickle
import json
from request_status import RequestStatus
from funding_agency_database import FundingAgencyDatabase
from research_proposal_request import ResearchProposalRequest
from datetime import date
from dateutil.relativedelta import relativedelta
from actions import Actions
import uuid
from timer import Timer
from concurrent.futures import ThreadPoolExecutor

class FundingAgency(object):

    DATA_FILE: str = "funding_agency.pickle"
    database: FundingAgencyDatabase
    response: dict
    correlation_id: uuid
    timer: Timer = Timer("funding agency")

    def __init__(self) -> None:
        try:
            #read funds and history from file
            with open(self.DATA_FILE, 'rb') as f:
                self.database = pickle.load(f)
        except FileNotFoundError:
            # initialize funds and history
            self.database = FundingAgencyDatabase()

        # two threads
        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(self.timer.start)
            executor.submit(self.start)
    
    def start(self) -> None:
        #Connect to RabbitMQ
        connection = BlockingConnection(ConnectionParameters(host='localhost'))
        channel = connection.channel()

        #Create queue for research proposal RPC
        channel.queue_declare(queue='submit_research_proposal')

        #Fair dispatch, no more than one message to a worker at a time
        #To avoid race condition
        channel.basic_qos(prefetch_count=1)

        #Defining queue where callback function should receive messages from
        channel.basic_consume(queue='submit_research_proposal', on_message_callback=self.process_research_proposal)

        print(" [F] Awaiting Research Proposals requests")

        #await research proposals
        channel.start_consuming()

    def process_research_proposal(self, ch: BlockingChannel, method: Basic.Deliver, props: BasicProperties, body: bytes) -> None:    
        request: ResearchProposalRequest = ResearchProposalRequest.from_json_data(body)

        #adjust timer if needed
        self.timer.adjust_timer(request.timestamp.strftime("%d-%m-%Y"))
        
        if request.amount > self.database.funds:
            response = RequestStatus.REJECTED.value
            print(f" [F] Research Proposals rejected: not enough funds (Request: {request.amount}, Funds: {self.database.funds})")
        elif request.amount >= 200000 and request.amount <= 500000:
            response = RequestStatus.APPROVED.value
            self.database.allocate_funds(request.amount)
            print(" [F] Research Proposals accepted")
        else:
            response = RequestStatus.REJECTED.value
            print(" [F] Research Proposals rejected")

        history_record = {
            'request_type': Actions.CREATE_ACCOUNT.value,
            'status': response, 
            'budget': request.amount,
            'title': request.title,
            'researcher': request.id,
            'end_date': (date.today() + relativedelta(months=1)).strftime('%d-%m-%Y'), # end date 1 month after allocating budget
            'timestamp': self.timer.get_time_str()
        }

        self.database.record_history(history_record)
        
        # save database to file
        with open(self.DATA_FILE, 'wb') as f:
            pickle.dump(self.database, f)

        # send response to researcher
        ch.basic_publish(exchange='',
            routing_key=props.reply_to,
            properties=BasicProperties(
                correlation_id = props.correlation_id,
                content_type="application/json"
                ),
            body=json.dumps({
                "status": response, 
                "account": request.title,
                "timestamp": self.timer.get_time_str()
            })
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

        print(" [F] Response sent")
        if(response == RequestStatus.APPROVED.value):
            self.notify_university(history_record)

    def notify_university(self, message: dict):
        #Connect to RabbitMQ
        self.connection = BlockingConnection(ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()

        #Create an anonymous exclusive callback queue
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)
        
        #Initialize the response to NULL and create a new request ID
        self.response = None
        self.correlation_id = str(uuid.uuid4())

        print(" [F] Sending Create Account Request")
        # Send Request To Funding Agency
        self.channel.basic_publish(
            exchange='',
            routing_key='university_requests_queue',
            properties=BasicProperties(
                reply_to=self.callback_queue,   # Anonymous exclusive researcher callback queue
                correlation_id=self.correlation_id,    # Request ID
                content_type="application/json"
            ),
            body=json.dumps(message)
        )
        
        self.connection.process_data_events(time_limit=None)

    def on_response(self, ch: BlockingChannel, method: Basic.Deliver, props: BasicProperties, body: bytes) -> None:
        print(" [F] Received Create Account Response")
        if self.correlation_id == props.correlation_id:
            self.response = json.loads(body)

            #adjust timer if needed
            self.timer.adjust_timer(self.response["timestamp"])

if __name__ == '__main__':
    funding_agency = FundingAgency()