from datetime import date
from request_status import RequestStatus
from request_response import RequestResponse

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

    def create_research_account(self, project_title: str, researcher: str, budget: int, end_date: date) -> RequestResponse:
        account = ResearchAccount(budget, researcher, end_date)
        self.accounts[project_title] = account
        self.lead_researchers[researcher] = project_title

        return RequestResponse(
            RequestStatus.SUCCEEDED.value, 
            f"Account '{project_title}' has been created"
        )

    def add_researcher(self, lead_researcher: str, researcher: str) -> RequestResponse:
        if(lead_researcher not in self.lead_researchers.keys()):
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{lead_researcher} is not a Lead Researcher"
            )
        
        if(researcher in self.lead_researchers.keys()):
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{researcher} is leading another research"
            )
        
        account_name: str = self.lead_researchers[lead_researcher]
        account: ResearchAccount = self.accounts[account_name]

        if researcher in account.users:
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{researcher} has already access to account '{account_name}'"
            )
        else:
            account.users.append(researcher)

            return RequestResponse(
                RequestStatus.SUCCEEDED.value, 
                f"{researcher} has been added to account '{account_name}'",
                account_name
            )

    def remove_researcher(self, lead_researcher: str, researcher: str) -> RequestResponse:
        if(lead_researcher not in self.lead_researchers.keys()):
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{lead_researcher} is not a Lead Researcher"
            )
        
        account_name: str = self.lead_researchers[lead_researcher]
        account: ResearchAccount = self.accounts[account_name]

        if researcher in account.users:
            account.users.remove(researcher)
            return RequestResponse(
                RequestStatus.SUCCEEDED.value, 
                f"{researcher} has been removed from account '{account_name}'",
                account_name
            )
        else:
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{researcher} does not have access to account '{account_name}'"
            )

    def access_details(self, lead_researcher: str) -> RequestResponse:
        """
            Returns remaining budget, end date, users
        """
        if(lead_researcher not in self.lead_researchers.keys()):
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{lead_researcher} is not a Lead Researcher"
            )
        
        account_name: str = self.lead_researchers[lead_researcher]
        account: ResearchAccount = self.accounts[account_name]

        message = (f"""\t\t------------------------------------------------------\n\
        \t  LEAD RESEARCHER:    {account.leading_researcher}\n\
        \t  BUDGET(REMAINING):  {account.budget} £\n\
        \t  USERS:              {account.users}\n\
        \t  END DATE:           {account.end_date}\n\
        \t------------------------------------------------------""")

        return RequestResponse(
            RequestStatus.SUCCEEDED.value,
            message
        )

    def list_transactions(self, lead_researcher: str) -> RequestResponse:
        if(lead_researcher not in self.lead_researchers.keys()):
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{lead_researcher} is not a Lead Researcher"
            )
        
        account_name: str = self.lead_researchers[lead_researcher]
        account: ResearchAccount = self.accounts[account_name]
        
        message_list = []
        message_list.append(f"""\t\t------------------------------------------------------\n\
        \t{account_name} TRANSACTIONS\n\n\
        \t{'ID':4} | {'RESEARCHER':15} | {'AMOUNT':6} | {'DATE':10} | {'STATUS':8} | {'BUDGET':6}\n""")

        for id, transaction in account.transactions.items():
            message_list.append(f"""\t{id: 4} | {transaction['researcher']:15} | {transaction['amount']:6} | {transaction['date'].strftime('%d-%m-%Y'):10} \
                  | {transaction['status']:8} | {transaction['budget']:6}\n""")

        message_list.append("\t\t------------------------------------------------------")

        return RequestResponse(
            RequestStatus.SUCCEEDED.value,
            "".join(message_list)
        )

    def withdraw_funds(self, account_name: str, researcher: str, amount: int) -> RequestResponse:
        if account_name == None:
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{researcher} has not access to any accounts"
            )
        
        account: ResearchAccount = self.accounts[account_name]

        if researcher not in account.users:
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{researcher} has not access to account '{account_name}'"
            )

        #get transaction id 
        transaction_id: int = account.number_of_transactions     
        
        #register transaction
        if account.budget >= int(amount):
            account.budget -= int(amount)
        else:
            return RequestResponse(
                RequestStatus.FAILED.value,
                f"Not enough budegt left in account '{account_name}'"
            )
        
        transaction = {
            "researcher": researcher,
            "date": date.today(),
            "amount": amount,
            "status": RequestStatus.SUCCEEDED.value,
            "budget": account.budget    #after the transaction
        }

        #register transaction
        account.transactions[transaction_id] = transaction

        #increase number of transactions
        account.number_of_transactions += 1 

        return RequestResponse(
            RequestStatus.SUCCEEDED.value,
            f"{amount} £ has been withdrawn from account '{account_name}'"
        )
