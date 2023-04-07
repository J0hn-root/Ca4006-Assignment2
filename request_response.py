import json
from datetime import date, datetime

class RequestResponse(object):
    
    status: str
    message: str
    account: str
    timestamp: date
    action: str

    def __init__(self, status: str, message: str, timestamp: date, account: str = None, action: str = None) -> None:
        self.status = status
        self.message = message
        self.timestamp = timestamp
        self.account = account
        self.action = action

    @classmethod
    def from_json_data(self, json_data: str) -> None:
        data = json.loads(json_data)

        self.status = data["status"]
        self.message = data["message"]
        self.account = data["account"]
        self.timestamp = datetime.strptime(data["timestamp"], '%d-%m-%Y').date()
        self.action = data["action"]

        return self

    def to_json(self) -> str:
        data = {
            "status": self.status,
            "message": self.message,
            "account": self.account,
            "timestamp": self.timestamp.strftime("%d-%m-%Y"),
            "action": self.action
        }

        return json.dumps(data)