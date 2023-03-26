from researcher import Researcher
from research_proposal_request import ResearchProposalRequest
from concurrent.futures import ThreadPoolExecutor
import random

def run_workers(id: int) -> None:
    researcher = Researcher(id)

    print(" [x] Submitting research proposal")

    amount = random.randint(1, 500000)

    request_proposal = ResearchProposalRequest(
        researcher.id, "Distributed Systems", "This is assignment 2",  amount
    )

    response = researcher.submit_research_proposal(request_proposal)
    print(f" [{researcher.id}] Research proposal has been {response}")

if __name__ == '__main__':
    researches_number = 4
    with ThreadPoolExecutor(max_workers=researches_number) as executor:
        future = {executor.submit(run_workers, worker_id): worker_id for worker_id in range(0, researches_number)}