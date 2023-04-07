#!/usr/bin/env python
from pika import BlockingConnection, ConnectionParameters
from pika.spec import Basic, BasicProperties, PERSISTENT_DELIVERY_MODE
from pika.adapters.blocking_connection import BlockingChannel
import uuid
from research_proposal_request import ResearchProposalRequest
import json
import random
from actions import Actions
from datetime import date, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from timer import Timer
from request_status import RequestStatus
from threading import Condition
import sys

class Researcher(object):

    fa_correlation_id: uuid
    uni_correlation_id: uuid
    id: str
    current_date: date
    timer: Timer
    command: dict = None
    command_lock: Condition = Condition()
    command_channel: BlockingChannel
    command_connection: BlockingConnection
    run: bool

    def __init__(self, id: int) -> None:
        self.current_date = date.today()
        self.id = f"Researcher-{id}"
        self.timer = Timer(self.id)
        self.run = True
        self.delivery_tag = None


    def start(self) -> None:
        # two threads
        with ThreadPoolExecutor(max_workers=3) as executor:
            executor.submit(self.timer.start)
            executor.submit(self.command_listener)

            while self.run:
                # listen to commands     
                with self.command_lock:
                    if self.command == None:
                        self.command_lock.wait()
                    if self.command['command'] == "exit":
                        print("exit")
                        self.run = False
                        break
                    executor.submit(self.perform_command, self.command)
                    self.command_channel.basic_ack(delivery_tag = self.delivery_tag)
                    self.command = None

            self.timer.stop()
            self.command_connection.close()
            sys.exit(0)

    def command_listener(self) -> str:
        try:
            self.command_connection = BlockingConnection(ConnectionParameters(host='localhost'))
            self.command_channel = self.command_connection.channel()

            self.command_channel.exchange_declare(exchange='send_researchers_command', exchange_type='direct')

            result = self.command_channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue

            self.command_channel.queue_bind(exchange='send_researchers_command', queue=queue_name, routing_key=self.id)

            print(f" [{self.id}] Waiting commands")
            #Fair dispatch, no more than one message to a worker at a time
            #To avoid race condition
            self.command_channel.basic_qos(prefetch_count=1)

            self.command_channel.basic_consume(queue=queue_name, on_message_callback=self.command_callback, auto_ack=False)

            self.command_channel.start_consuming()
        except Exception as e:
            print(e)

    def command_callback(self, ch: BlockingChannel, method: Basic.Deliver, props: BasicProperties, body: bytes) -> None:
        message = json.loads(body)

        with self.command_lock:
            self.command = message
            self.command_lock.notify()
            self.delivery_tag = method.delivery_tag

    def perform_command(self, command: dict) -> None:
        try:
            if command["command"] == Actions.RESEARCH_PROPOSAL.value:
                request_proposal = ResearchProposalRequest(
                    command['project_id'], 
                    command['title'], 
                    command['description'],  
                    int(command['amount']), 
                    self.timer.get_time(), 
                    self.id
                )

                print(f" [{self.id}] Submitting research proposal")
                self.submit_research_proposal(request_proposal)
                print(f" [{self.id}] Research proposal has been {self.funding_agency_response['status']}. Amount: {request_proposal.amount}")
            elif command["command"] == "time":
                # print time of researcher
                print(f" [{self.id}] {self.timer.get_time_str()}")
            elif command["command"] == Actions.ADD_RESEARCH_ACCOUNT.value:
                # notify researcher that has been added to the research account
                print(f" [{self.id}] added to account '{command['account']}'")
            elif command["command"] == Actions.REMOVE_RESEARCH_ACCOUNT.value:
                # notify researcher that has been removed from the research account
                print(f" [{self.id}] removed from account '{command['account']}'")
            elif command["command"] not in [comm.value for comm in Actions]:
                print(f" [{self.id}] command {command['command']} does not exist")
            else:
                execute_command_connection = BlockingConnection(ConnectionParameters(host='localhost'))

                execute_command_channel = execute_command_connection.channel()

                result = execute_command_channel.queue_declare(queue='', exclusive=True)
                self.uni_callback_queue = result.method.queue

                execute_command_channel.basic_consume(
                    queue=self.uni_callback_queue,
                    on_message_callback=self.command_response,
                    auto_ack=True
                )
                
                #Initialize the response to NULL and create a new request ID
                self.university_response = None
                self.uni_correlation_id = str(uuid.uuid4())

                # Execute University RPC
                execute_command_channel.basic_publish(
                    exchange='',
                    routing_key='university_requests_queue',
                    properties=BasicProperties(
                        reply_to=self.uni_callback_queue,           # Anonymous exclusive researcher callback queue
                        correlation_id=self.uni_correlation_id,    # Request ID
                        content_type="application/json",
                        delivery_mode = PERSISTENT_DELIVERY_MODE
                    ),
                    body=json.dumps({
                        "correlation_id": self.uni_correlation_id,
                        "request_type": command['command'],
                        "amount": command['amount'] if "amount" in command.keys() else None,
                        "researcher": self.id,
                        "target_researcher": command['researcher'] if "researcher" in command.keys() else None,
                        "timestamp": self.timer.get_time_str()
                    })
                )

        
                execute_command_connection.process_data_events(time_limit=None)
            
                print(f" {self.university_response['status']}:[{self.id}] Command {command['command']}:\n{self.university_response['message']}\n")

        except Exception as e:
            print(e)
            raise e

    # response of the university rpc
    def command_response(self, ch: BlockingChannel, method: Basic.Deliver, props: BasicProperties, body: bytes) -> None:
        if self.uni_correlation_id == props.correlation_id:
            self.university_response = json.loads(body)

            #adjust timer if needed
            self.timer.adjust_timer(self.university_response["timestamp"])

    def submit_research_proposal(self, request: ResearchProposalRequest) -> None:
        try:
            #Connect to RabbitMQ
            connection = BlockingConnection(ConnectionParameters(host='localhost'))
            channel = connection.channel()

            #Create an anonymous exclusive callback queue
            result = channel.queue_declare(queue='', exclusive=True)
            callback_queue = result.method.queue

            channel.basic_consume(
                queue=callback_queue,
                on_message_callback=self.on_response,
                auto_ack=True)

            self.funding_agency_response = None
            self.fa_correlation_id = None

            #Initialize the response to NULL and create a new request ID
            self.funding_agency_response = None
            self.fa_correlation_id = str(uuid.uuid4())

            # Send Request To Funding Agency
            channel.basic_publish(
                exchange='',
                routing_key='submit_research_proposal',
                properties=BasicProperties(
                    reply_to=callback_queue,   # Anonymous exclusive researcher callback queue
                    correlation_id=self.fa_correlation_id,    # Request ID
                    content_type="application/json",
                    delivery_mode = PERSISTENT_DELIVERY_MODE
                ),
                body=request.to_json()
            )

            connection.process_data_events(time_limit=None)
        except Exception as e:
            print(e)
            raise e
        
    # response to the research proposal by the funding agency
    def on_response(self, ch: BlockingChannel, method: Basic.Deliver, props: BasicProperties, body: bytes) -> None:
        if self.fa_correlation_id == props.correlation_id:
            self.funding_agency_response = json.loads(body)

            #adjust timer if needed
            self.timer.adjust_timer(self.funding_agency_response["timestamp"])
    
if __name__ == '__main__':
    id = sys.argv[1]
    researcher = Researcher(id)
    researcher.start()