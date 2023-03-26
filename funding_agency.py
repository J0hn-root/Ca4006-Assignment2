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

class FundingAgency(object):

    DATA_FILE: str = "funding_agency.pickle"
    database: FundingAgencyDatabase

    def __init__(self) -> None:
        try:
            #read funds and history from file
            with open(self.DATA_FILE, 'rb') as f:
                self.database = pickle.load(f)
        except FileNotFoundError:
            # initialize funds and history
            self.database = FundingAgencyDatabase()
                
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

        print(" [x] Awaiting Research Proposals requests")

        #await research proposals
        channel.start_consuming()

    def process_research_proposal(self, ch: BlockingChannel, method: Basic.Deliver, props: BasicProperties, body: bytes) -> None:    
        request: ResearchProposalRequest = ResearchProposalRequest.from_json_data(body)
        
        if request.amount > self.database.funds:
            response = RequestStatus.REJECTED.value
            print(f" [x] Research Proposals rejected: not enough funds (Request: {request.amount}, Funds: {self.database.funds})")
        elif request.amount >= 200000 and request.amount <= 500000:
            response = RequestStatus.APPROVED.value
            self.database.allocate_funds(request.amount)
            print(" [x] Research Proposals accepted")
        else:
            response = RequestStatus.REJECTED.value
            print(" [x] Research Proposals rejected")

        history_record = {
            'status': response, 
            'budget': request.amount,
            'title': request.title,
            'researcher': request.id,
            'end_date': (date.today() + relativedelta(months=1)).strftime('%d-%m-%Y') # end date 1 month after allocating budget
        }

        self.database.record_history(history_record)
        
        # save database to file
        with open(self.DATA_FILE, 'wb') as f:
            pickle.dump(self.database, f)

        ch.basic_publish(exchange='',
                        routing_key=props.reply_to,
                        properties=BasicProperties(
                            correlation_id = props.correlation_id,
                            content_type="application/json"
                            ),
                        body=json.dumps(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

        print(" [x] Response sent")
        if(response == RequestStatus.APPROVED.value):
            self.notify_university(history_record)

    def notify_university(self, message: dict) -> None:
        #Connect to RabbitMQ
        connection = BlockingConnection(ConnectionParameters(host='localhost'))
        channel = connection.channel()

        channel.queue_declare(queue='create_project_account', durable=True)

        channel.basic_publish(
            exchange='',
            routing_key='create_project_account',
            body=json.dumps(message),
            properties=BasicProperties(
                delivery_mode=PERSISTENT_DELIVERY_MODE, #queue won't be lost even on restarts
                content_type="application/json"
            ))
        print(" [x] Sent %r" % message)
        connection.close()

if __name__ == '__main__':
    funding_agency = FundingAgency()