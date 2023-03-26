import json

class ResearchProposalRequest(object):
    
    id: str
    title: str
    description: str
    amount: int

    def __init__(self, id: str, title: str, description: str, amount: int) -> None:
        self.id = id
        self.title = title
        self.description = description
        self.amount = amount

    @classmethod
    def from_json_data(self, json_data: str) -> None:
        data = json.loads(json_data)

        self.id = data["id"]
        self.title = data["title"]
        self.description = data["description"]
        self.amount = data["amount"]

        return self

    def to_json(self) -> str:
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "amount": self.amount
        }

        return json.dumps(data)