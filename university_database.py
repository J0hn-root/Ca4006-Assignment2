from datetime import date
from request_status import RequestStatus

class ResearchAccount(object):
    budget: int
    leading_researcher: str
    users: list
    transactions: dict
    number_of_transactions: int
    end_date: date

    def __init__(self, budget: int, researcher: str, end_date: date) -> None:
        self.budget = budget
        self.leading_researcher = researcher
        self.users = []
        self.transactions = {}
        self.number_of_transactions = 1
        self.end_date = end_date

class UniversityDatabase(object):

    accounts: dict              #account informations (key: research account name)
    lead_researchers: dict      #mapping researchers-research_account (name)

    def __init__(self) -> None:
        self.accounts = {}
        self.lead_researchers = {}

    def create_research_account(self, project_title: str, researcher: str, budget: int, end_date: date) -> None:
        account = ResearchAccount(budget, researcher, end_date)
        self.accounts[project_title] = account
        self.lead_researchers[researcher] = project_title

    def add_researcher(self, lead_researcher: str, researcher: str) -> None:
        if(lead_researcher not in self.lead_researchers.keys()):
            print(f"{lead_researcher} is not a Lead Researcher")
            return
        
        account_name: str = self.lead_researchers[lead_researcher]
        account: ResearchAccount = self.accounts[account_name]

        account.users.append(researcher)

    def remove_researcher(self, lead_researcher: str, researcher: str) -> None:
        if(lead_researcher not in self.lead_researchers.keys()):
            print(f"{lead_researcher} is not a Lead Researcher")
            return
        
        account_name: str = self.lead_researchers[lead_researcher]
        account: ResearchAccount = self.accounts[account_name]

        if researcher in account.users:
            account.users.remove(researcher)

    def access_details(self, lead_researcher: str) -> None:
        """
            Returns remaining budget, end date, users
        """
        if(lead_researcher not in self.lead_researchers.keys()):
            print(f"{lead_researcher} is not a Lead Researcher")
            return
        
        account_name: str = self.lead_researchers[lead_researcher]
        account: ResearchAccount = self.accounts[account_name]

        print(f"""\
        ------------------------------------------------------\n\
            LEAD RESEARCHER:    {account.leading_researcher}\n\
            BUDGET(REMAINING):  {account.budget}\n\
            USERS:              {account.users}\n\
            END DATE:           {account.end_date}\n\
        ------------------------------------------------------\
        """)

    def list_transactions(self, lead_researcher: str) -> None:
        if(lead_researcher not in self.lead_researchers.keys()):
            print(f"{lead_researcher} is not a Lead Researcher")
            return
        
        account_name: str = self.lead_researchers[lead_researcher]
        account: ResearchAccount = self.accounts[account_name]

        print(f"""\
            ------------------------------------------------------\n\
            {account_name} TRANSACTIONS\n\n {'ID':4} | {'RESEARCHER':15} | {'AMOUNT':6} | {'DATE':10} | {'STATUS':8} | {'BUDGET':6}\
        """)

        for id, transaction in account.transactions.items():
            print(f""" {id: 4} | {transaction['researcher']:15} | {transaction['amount']:6} | {transaction['date'].strftime('%d-%m-%Y'):10} \
                  | {transaction['status']:8} | {transaction['budget']:6}\
            """)

        print("------------------------------------------------------")

    def withdraw_funds(self, account: str, researcher: str, amount: int) -> RequestStatus:
        account: ResearchAccount = self.accounts[account]

        #get transaction id 
        transaction_id: int = account.number_of_transactions     
        
        #register transaction
        if account.budget >= amount:
            account.budget -= amount
            status = RequestStatus.APPROVED
        else:
            status = RequestStatus.REJECTED
        
        transaction = {
            "researcher": researcher,
            "date": date.today(),
            "amount": amount,
            "status": status,
            "budget": account.budget    #after the transaction
        }

        #register transaction
        account.transactions[transaction_id] = transaction

        #increase number of transactions
        account.number_of_transactions += 1 

        return status
