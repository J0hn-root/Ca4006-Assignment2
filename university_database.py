from datetime import date
from request_status import RequestStatus
from request_response import RequestResponse
from timer import Timer

class ResearchAccount(object):
    budget: int
    leading_researcher: str
    users: list
    transactions: dict
    number_of_transactions: int
    title: str
    description: str
    project_id: str
    end_date: date

    def __init__(self, title: str, description: str, project_id: str, budget: int, leading_researcher: str, end_date: date) -> None:
        self.budget = budget
        self.leading_researcher = leading_researcher
        self.users = []
        self.transactions = {}
        self.number_of_transactions = 1
        self.end_date = end_date
        self.title = title
        self.description = description
        self.project_id = project_id

class UniversityDatabase(object):

    accounts: dict              #account informations (key: research account name)
    researchers: dict           #mapping researcher-research_account (name)

    def __init__(self) -> None:
        self.accounts = {}
        self.researchers = {}

    def create_research_account(self, request: dict, end_date: date, timer: Timer) -> RequestResponse:
        # checking if researcher is member of another account or if another project with the same id exists is done in self.check_researcher_proposal()

        account = ResearchAccount(
            request["title"],
            request["description"],
            request["project_id"],
            request["budget"], 
            request["researcher"], 
            end_date
        )
        self.accounts[request["project_id"]] = account
        self.researchers[request["researcher"]] = request["project_id"]

        return RequestResponse(
            RequestStatus.SUCCEEDED.value, 
            f"Account '{request['project_id']}' has been created",
            timer.get_time()
        )

    def add_researcher(self, lead_researcher: str, researcher: str, timer: Timer) -> RequestResponse:
        #check if the requesting user is a lead resercher of member of an account
        if lead_researcher not in self.researchers.keys() or self.researchers[lead_researcher] == None:
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{lead_researcher} is not a Lead Researcher",
                timer.get_time()
            )
        
        # check if researcher is already registered with another account
        if researcher in self.researchers.keys() and self.researchers[researcher] != None :
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{researcher} has already access to account '{self.researchers[researcher]}'",
                timer.get_time()
            )
        
        #retrieve account name given lead researcher
        account_name: str = self.researchers[lead_researcher]
        #retrieve account given project name
        account: ResearchAccount = self.accounts[account_name]

        if researcher in account.users:
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{researcher} has already access to account '{account_name}'",
                timer.get_time()
            )
        else:
            #update list users
            account.users.append(researcher)
            #update researcher project
            self.researchers[researcher] = account.project_id

            return RequestResponse(
                RequestStatus.SUCCEEDED.value, 
                f"{researcher} has been added to account '{account_name}'",
                timer.get_time(),
                account_name
            )

    def remove_researcher(self, lead_researcher: str, researcher: str, timer: Timer) -> RequestResponse:        
        #check if the requesting user is a lead resercher of member of an account
        if lead_researcher not in self.researchers.keys() or self.researchers[lead_researcher] == None:
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{lead_researcher} is not a Lead Researcher",
                timer.get_time()
            )
        
        #retrieve account name given lead researcher
        account_name: str = self.researchers[lead_researcher]
        #retrieve account given project name
        account: ResearchAccount = self.accounts[account_name]

        if researcher in account.users:
            account.users.remove(researcher)
            self.researchers[researcher] = None
            
            return RequestResponse(
                RequestStatus.SUCCEEDED.value, 
                f"{researcher} has been removed from account '{account_name}'",
                timer.get_time(),
                account_name
            )
        else:
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{researcher} does not have access to account '{account_name}'",
                timer.get_time()
            )

    def access_details(self, lead_researcher: str, timer: Timer) -> RequestResponse:
        """
            Returns remaining budget, end date, users
        """
        #check if the requesting user is a lead resercher of an account
        if lead_researcher not in self.researchers.keys() or self.researchers[lead_researcher] == None:
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{lead_researcher} is not a Lead Researcher",
                timer.get_time()
            )
        
        #retrieve account name given lead researcher
        account_name: str = self.researchers[lead_researcher]
        #retrieve account given project name
        account: ResearchAccount = self.accounts[account_name]


        message = (f"""\t\t------------------------------------------------------\n\
        \t  PROJECT ID:         {account.project_id}\n\
        \t  TITLE:              {account.title}\n\
        \t  DESCRIPTION:        {account.description}\n\
        \t  LEAD RESEARCHER:    {account.leading_researcher}\n\
        \t  BUDGET(REMAINING):  {account.budget} £\n\
        \t  USERS:              {account.users}\n\
        \t  END DATE:           {account.end_date.strftime('%d-%m-%Y')}\n\
        \t------------------------------------------------------""")

        return RequestResponse(
            RequestStatus.SUCCEEDED.value,
            message,
            timer.get_time()
        )

    def list_transactions(self, lead_researcher: str, timer: Timer) -> RequestResponse:       
        #check if the requesting user is a lead resercher of member of an account
        if lead_researcher not in self.researchers.keys() or self.researchers[lead_researcher] == None:
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{lead_researcher} is not a Lead Researcher",
                timer.get_time()
            )
        
        #retrieve account name given lead researcher
        account_name: str = self.researchers[lead_researcher]
        #retrieve account given project name
        account: ResearchAccount = self.accounts[account_name]
        
        message_list = []
        message_list.append(f"""\t\t------------------------------------------------------\n\
        \t{account_name} TRANSACTIONS\n\n\
        \t{'ID':4} | {'RESEARCHER':15} | {'AMOUNT':6} | {'DATE':15} | {'STATUS':10} | {'BUDGET':10}\n""")

        for id, transaction in account.transactions.items():
            date_transaction = transaction['date'].strftime('%d-%m-%Y')
            message_list.append(f"""\t\t{id: 4} | {transaction['researcher']:15} | {transaction['amount']:6} | {date_transaction:15} | {transaction['status']:10} | {transaction['budget']:10}\n""")

        message_list.append("\t\t------------------------------------------------------")

        return RequestResponse(
            RequestStatus.SUCCEEDED.value,
            "".join(message_list),
            timer.get_time()
        )

    def withdraw_funds(self, researcher: str, amount: int, timer: Timer) -> RequestResponse:
        #check if researcher is registered with an account
        if researcher not in self.researchers.keys() or self.researchers[researcher] == None:
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{researcher} has not access to any accounts",
                timer.get_time()
            )
        
        #retrieve account name given lead researcher
        account_name: str = self.researchers[researcher]
        #retrieve account given project name
        account: ResearchAccount = self.accounts[account_name]

        # check that the user is either lead or member of the account
        if researcher not in account.users and researcher != account.leading_researcher:
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"{researcher} has not access to account '{account_name}'",
                timer.get_time()
            )
        
        #check that the end date did not expire
        if account.end_date < timer.get_time():
            return RequestResponse(
                RequestStatus.FAILED.value, 
                f"The end date for account '{account_name}' has passed!",
                timer.get_time()
            )

        #get transaction id 
        transaction_id: int = account.number_of_transactions     
        
        #register transaction
        if account.budget >= int(amount):
            account.budget -= int(amount)
        else:
            return RequestResponse(
                RequestStatus.FAILED.value,
                f"Not enough budegt left in account '{account_name}'",
                timer.get_time()
            )
        
        transaction = {
            "researcher": researcher,
            "date": timer.get_time_str(),
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
            f"{amount} £ has been withdrawn from account '{account_name}'",
            timer.get_time()
        )
    
    def check_researcher_proposal(self, request: dict, timer: Timer) -> RequestResponse:
        researcher = request['researcher']
        if request["project_id"] in self.accounts.keys():
            return RequestResponse(
                RequestStatus.REJECTED.value, 
                f"An account with id '{request['project_id']}' already exists",
                timer.get_time()
            )
        #check if the requesting user is a lead resercher of member of an account
        if researcher not in self.researchers.keys() or self.researchers[researcher] == None:
            return RequestResponse(
                RequestStatus.APPROVED.value, 
                f"{researcher} is not member of any accounts",
                timer.get_time(),
                action=request["request_type"]
            )
        else:
            return RequestResponse(
                RequestStatus.REJECTED.value, 
                f"{researcher} has already access to account '{self.researchers[researcher]}'",
                timer.get_time(),
                action=request["request_type"]
            )
