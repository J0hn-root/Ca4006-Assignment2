class FundingAgencyDatabase(object):

    funds: int
    # k = correlation_id, v = request metadata
    transaction_history: dict
    # k = int, v = correlation_id
    requests_history: dict
    transaction_number: int

    def __init__(self) -> None:
        self.funds = 1000000
        self.transaction_number = 1
        self.transaction_history = {}
        self.requests_history = {}

    def allocate_funds(self, amount: int) -> None:
        self.funds -= amount

    def record_history(self, history_record: dict) -> None:
        history_record['transaction'] = self.transaction_number

        #keep track of the last 10 requests
        self.requests_history[self.transaction_number % 10] = history_record["correlation_id"]
        self.transaction_number += 1

        #save request transaction - logs
        self.transaction_history[history_record["correlation_id"]] = history_record

    def is_request_new(self, correlation_id: str) -> bool:
        """
            Return false if the transaction has been already processed.
            Return false if this is a new request.
        """
        for k, v in self.requests_history.items():
            if v == correlation_id:
                return False
            
        return True
    
    def get_request_metadata(self, correlation_id: str) -> dict:
        return self.transaction_history[correlation_id]
    