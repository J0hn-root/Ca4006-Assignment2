class FundingAgencyDatabase(object):

    funds: int
    history: list
    transaction_number: int

    def __init__(self) -> None:
        self.funds = 1000000
        self.transaction_number = 1
        self.history = []

    def allocate_funds(self, amount: int) -> None:
        self.funds -= amount

    def record_history(self, history_record) -> None:
        history_record['transaction'] = self.transaction_number
        self.transaction_number += 1
        self.history.append(history_record)