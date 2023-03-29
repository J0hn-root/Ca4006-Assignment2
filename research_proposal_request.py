import json
from datetime import date, datetime

class ResearchProposalRequest(object):
    
    id: str
    title: str
    description: str
    amount: int
    timestamp: date

    def __init__(self, id: str, title: str, description: str, amount: int, timestamp: date) -> None:
        self.id = id
        self.title = title
        self.description = description
        self.amount = amount
        self.timestamp = timestamp

    @classmethod
    def from_json_data(self, json_data: str) -> None:
        data = json.loads(json_data)

        self.id = data["id"]
        self.title = data["title"]
        self.description = data["description"]
        self.amount = data["amount"]
        self.timestamp = datetime.strptime(data["timestamp"], '%d-%m-%Y').date()

        return self

    def to_json(self) -> str:
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "amount": self.amount,
            "timestamp": self.timestamp.strftime("%d-%m-%Y")
        }

        return json.dumps(data)