#!/usr/bin/env python
from pika import BlockingConnection, ConnectionParameters
from pika.spec import Basic, BasicProperties
from pika.adapters.blocking_connection import BlockingChannel
import sys
from researcher import Researcher
from funding_agency import FundingAgency
from university import University
from research_proposal_request import ResearchProposalRequest
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json
from actions import Actions

def get_commands() -> list:
    """
        Parse commands given in input with the following format:

            'routing_key:command:(amount|researcher)'

        Commands can be concatenated using th epipe character:

            '1:proposal:DS:Distributed systems:CASE4 module:200000 | 1:add:3 | 2:details | 4:transactions' 

        'routing_key' defines the queue belonging to the target of the command (which is the id of the researcher)
        'command' is the name of the command can be:
            - proposal
            - withdraw
            - add
            - remove
            - transactions
            - details
            - time

        the third parameter can be amount (only for withdraw/proposal) or researcher (only for add/remove) 
    """
    
    input_line = input(" [Main] Type command:\n")
    list_commands = []

    requests = input_line.split("|")
    for request in requests:
        command = request.split(":")[1].strip()
        if command == "proposal":
            routing_key, command, project_id, title, description, amount =  request.split(":")
            list_commands.append({
                "routing_key": f"Researcher-{routing_key.strip()}", 
                "command": Actions.RESEARCH_PROPOSAL.value, 
                "project_id": project_id.strip(),
                "title": title.strip(),
                "description": description.strip(),
                "amount": amount.strip()})
        elif command == "withdraw":
            routing_key, command, amount =  request.split(":")
            list_commands.append({"routing_key": f"Researcher-{routing_key.strip()}", "command": Actions.WITHDRAW.value, "amount": amount.strip()})
        elif command == "add":
            routing_key, command, researcher =  request.split(":")
            list_commands.append({"routing_key": f"Researcher-{routing_key.strip()}", "command": Actions.ADD_RESEARCHER.value, "researcher": f"Researcher-{researcher.strip()}"})
        elif command == "remove":
            routing_key, command, researcher =  request.split(":")
            list_commands.append({"routing_key": f"Researcher-{routing_key.strip()}", "command": Actions.REMOVE_RESEARCHER.value, "researcher": f"Researcher-{researcher.strip()}"})
        elif command == "transactions":
            routing_key, command =  request.split(":")
            list_commands.append({"routing_key": f"Researcher-{routing_key.strip()}", "command": Actions.LIST_TRANSACTIONS.value})
        elif command == "details":
            routing_key, command =  request.split(":")
            list_commands.append({"routing_key": f"Researcher-{routing_key.strip()}", "command": Actions.GET_DETAILS.value})
        else:
            routing_key, command =  request.split(":")
            list_commands.append({"routing_key": f"Researcher-{routing_key.strip()}", "command": command.strip()})


    return list_commands

def send_command(routing_key: str, request: dict) -> None:
    connection = BlockingConnection(ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    channel.exchange_declare(exchange='send_researchers_command', exchange_type='direct')

    channel.basic_publish(
        exchange='send_researchers_command', 
        routing_key=routing_key,
        body=json.dumps(request)
    )
                    
    print(" [Main] Sent %r:%r" % (routing_key, request))

    connection.close()
    
if __name__ == '__main__':

    requests: list = get_commands()
    with ThreadPoolExecutor(max_workers=len(requests)) as executor:
        while True:
            future_commands = {executor.submit(send_command, request['routing_key'], request): request for request in requests}
            
            requests: list = get_commands()