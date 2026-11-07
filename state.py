
from typing import TypedDict, Annotated

from langgraph.graph.message import add_messages


class CustomerState(TypedDict):

    messages: Annotated[list, add_messages]

    customer_name: str
    email: str
    phone: str

    validation_status: str
    verification_status: str

    risk_level: str
    account_status: str
