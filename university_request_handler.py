#!/usr/bin/env python
from __future__ import annotations
from pika import BlockingConnection, ConnectionParameters
from pika.spec import Basic, BasicProperties
from pika.adapters.blocking_connection import BlockingChannel
from actions import Actions
from datetime import datetime
from university_database import UniversityDatabase
from abc import ABC, abstractmethod
from request_response import RequestResponse
from request_status import RequestStatus
from timer import Timer
import json

class IHandler(ABC):
    @abstractmethod
    def send_notification(self, routing_key: str, request: dict) -> None:
        pass

    @abstractmethod
    def set_next_handler(self, handler: IHandler) -> IHandler:
        pass
    
    @abstractmethod
    def execute_request(self, message: str, database: UniversityDatabase, timer: Timer) -> None:
        pass

class UniversityRequestHandler(IHandler):
    _next_handler: IHandler = None

    def send_notification(self, routing_key: str, request: dict) -> None:
        """
            Notify researcher that has been added or removed from the research account
        """
        connection = BlockingConnection(ConnectionParameters(host='localhost'))
        channel = connection.channel()
        
        channel.exchange_declare(exchange='send_researchers_command', exchange_type='direct')

        channel.basic_publish(
            exchange='send_researchers_command', 
            routing_key=routing_key,
            body=json.dumps(request)
        )
                        
        print(" [U] Sent %r:%r" % (routing_key, request))

        connection.close()
    
    def set_next_handler(self, handler: IHandler) -> IHandler:
        self._next_handler = handler
        return handler
    
    def execute_request(self, message: str, database: UniversityDatabase, timer: Timer) -> RequestResponse:
        if self._next_handler is not None:
            return self._next_handler.execute_request(message, database, timer)
        return None

class CreateAccountHandler(UniversityRequestHandler):
    def execute_request(self, request: dict, database: UniversityDatabase, timer: Timer) -> RequestResponse:
        if request['request_type'] == Actions.CREATE_ACCOUNT.value:
            result = database.create_research_account(request,  datetime.strptime(request['end_date'], '%d-%m-%Y').date(), timer)
            database.record_request_result(request["correlation_id"], result, request['request_type'])
            return result
        else:
            return super().execute_request(request, database, timer)

class WithdrawHandler(UniversityRequestHandler):
    def execute_request(self, request: dict, database: UniversityDatabase, timer: Timer) -> RequestResponse:
        if request['request_type'] == Actions.WITHDRAW.value:
            result = database.withdraw_funds(request['researcher'], request['amount'], timer)
            database.record_request_result(request["correlation_id"], result, request['request_type'])
            return result
        else:
            return super().execute_request(request, database, timer)

class AddResearcherHandler(UniversityRequestHandler):
    def execute_request(self, request: dict, database: UniversityDatabase, timer: Timer) -> RequestResponse:
        if request['request_type'] == Actions.ADD_RESEARCHER.value:
            result = database.add_researcher(request['researcher'], request['target_researcher'], timer)
            if result.status == RequestStatus.SUCCEEDED.value:
                self.send_notification(request['target_researcher'], {"command": Actions.ADD_RESEARCH_ACCOUNT.value, "account": result.account})
            database.record_request_result(request["correlation_id"], result, request['request_type'])
            return result
        else:
            return super().execute_request(request, database, timer)
    
class RemoveResearcherHandler(UniversityRequestHandler):
    def execute_request(self, request: dict, database: UniversityDatabase, timer: Timer) -> RequestResponse:
        if request['request_type'] == Actions.REMOVE_RESEARCHER.value:
            result = database.remove_researcher(request['researcher'], request['target_researcher'], timer)
            if result.status == RequestStatus.SUCCEEDED.value:
                self.send_notification(request['target_researcher'], {"command": Actions.REMOVE_RESEARCH_ACCOUNT.value, "account": result.account})
            database.record_request_result(request["correlation_id"], result, request['request_type'])
            return result
        else:
            return super().execute_request(request, database, timer)
    
class GetDetailsHandler(UniversityRequestHandler):
    def execute_request(self, request: dict, database: UniversityDatabase, timer: Timer) -> RequestResponse:
        if request['request_type'] == Actions.GET_DETAILS.value:
            result = database.access_details(request['researcher'], timer)
            database.record_request_result(request["correlation_id"], result, request['request_type'])
            return result
        else:
            return super().execute_request(request, database, timer)
    
class ListTransactionsHandler(UniversityRequestHandler):
    def execute_request(self, request: dict, database: UniversityDatabase, timer: Timer) -> RequestResponse:
        if request['request_type'] == Actions.LIST_TRANSACTIONS.value:
            result = database.list_transactions(request['researcher'], timer)
            database.record_request_result(request["correlation_id"], result, request['request_type'])
            return result
        else:
            return super().execute_request(request, database, timer)
        
class ResearcherProposalHandler(UniversityRequestHandler):
    def execute_request(self, request: dict, database: UniversityDatabase, timer: Timer) -> RequestResponse:
        if request['request_type'] == Actions.NOTIFY_RESEARCHER_PROPOSAL.value:
            result = database.check_researcher_proposal(request, timer)
            database.record_request_result(request["correlation_id"], result, request['request_type'])
            return result
        else:
            return super().execute_request(request, database, timer)
