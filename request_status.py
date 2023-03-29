from enum import Enum

class RequestStatus(Enum):
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    APPROVED = "Approved"
    REJECTED = "Rejected"