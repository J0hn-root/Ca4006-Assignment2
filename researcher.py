#!/usr/bin/env python
from pika import BlockingConnection, ConnectionParameters
from pika.spec import Basic, BasicProperties
from pika.adapters.blocking_connection import BlockingChannel
import uuid
from research_proposal_request import ResearchProposalRequest
import json
import random

class Researcher(object):

    response: ResearchProposalRequest
    correlation_id: uuid
    id: str

    def __init__(self, id: int) -> None:
        self.id = f"Researcher-{id}"
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

    def on_response(self, ch: BlockingChannel, method: Basic.Deliver, props: BasicProperties, body: bytes) -> None:
        if self.correlation_id == props.correlation_id:
            self.response = json.loads(body)

    def submit_research_proposal(self, request: ResearchProposalRequest):
        #Initialize the response to NULL and create a new request ID
        self.response = None
        self.correlation_id = str(uuid.uuid4())

        # Send Request To Funding Agency
        self.channel.basic_publish(
            exchange='',
            routing_key='submit_research_proposal',
            properties=BasicProperties(
                reply_to=self.callback_queue,   # Anonymous exclusive researcher callback queue
                correlation_id=self.correlation_id,    # Request ID
                content_type="application/json"
            ),
            body=request.to_json()
        )
        
        self.connection.process_data_events(time_limit=None)
        return self.response
    
if __name__ == '__main__':
    researcher = Researcher(1)

    print(" [x] Submitting research proposal")

    amount = random.randint(1, 1000000)

    request_proposal = ResearchProposalRequest(
        researcher.id, "Distributed Systems", "This is assignment 2",  amount
    )

    response = researcher.submit_research_proposal(request_proposal)
    print(f" [{researcher.id}] Research proposal has been {response}")