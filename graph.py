
import re

from langchain_core.messages import HumanMessage, AIMessage

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import CustomerState


# =====================================================
# HELPER FUNCTION
# GET LATEST USER MESSAGE
# =====================================================

def get_latest_user_message(state):

    for message in reversed(state.get("messages", [])):

        if isinstance(message, HumanMessage):
            return message.content

    return ""


# =====================================================
# NODE 1 - COLLECT CUSTOMER INFORMATION
# =====================================================

def collect_info(state: CustomerState):

    user_message = get_latest_user_message(state)

    name = state.get("customer_name", "")
    email = state.get("email", "")
    phone = state.get("phone", "")

    # Extract email

    email_match = re.search(
        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
        user_message
    )

    if email_match:
        email = email_match.group(0)

    # Extract Pakistani mobile number

    phone_match = re.search(
        r'(?<!\d)(?:\+92|0)3\d{9}(?!\d)',
        user_message
    )

    if phone_match:
        phone = phone_match.group(0)

    # Extract customer name

    name_patterns = [
        r"\b(?:my name is|name is|i am|i'm)\s+([A-Za-z][A-Za-z'-]*(?:\s+[A-Za-z][A-Za-z'-]*){0,2}?)(?=\s+(?:and\b|email\b|phone\b)|[,!.?;\n]|$)"
    ]

    for pattern in name_patterns:

        match = re.search(
            pattern,
            user_message,
            re.IGNORECASE
        )

        if match:
            name = match.group(1).strip()
            break

    return {
        "customer_name": name,
        "email": email,
        "phone": phone
    }


# =====================================================
# NODE 2 - VALIDATE CUSTOMER INFORMATION
# =====================================================

def validate_info(state: CustomerState):

    name = state.get("customer_name", "").strip()
    email = state.get("email", "").strip()
    phone = state.get("phone", "").strip()

    missing = []
    invalid = []

    # Check name

    if not name:
        missing.append("name")

    # Validate email

    if not email:
        missing.append("email")

    elif not re.fullmatch(
        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
        email
    ):
        invalid.append("email")

    # Validate Pakistani phone number

    if not phone:
        missing.append("phone")

    elif not re.fullmatch(
        r'(?:\+92|0)3\d{9}',
        phone
    ):
        invalid.append("phone")

    # Generate validation response

    if missing or invalid:

        status = "invalid"

        parts = []

        if missing:
            parts.append(
                "I still need the following information: "
                + ", ".join(missing)
                + "."
            )

        if invalid:
            parts.append(
                "Please provide a valid "
                + ", ".join(invalid)
                + "."
            )

        message = " ".join(parts)

    else:

        status = "valid"

        message = (
            "Great! Your customer information "
            "has been validated successfully."
        )

    return {
        "validation_status": status,
        "messages": [
            AIMessage(content=message)
        ]
    }


# =====================================================
# NODE 3 - VERIFY CUSTOMER
# =====================================================

def verify_customer(state: CustomerState):

    name = state.get("customer_name", "")
    email = state.get("email", "")
    phone = state.get("phone", "")

    if name and email and phone:

        message = (
            f"Customer verification completed for {name}. "
            "The provided information looks valid."
        )

        return {
            "verification_status": "verified",
            "messages": [
                AIMessage(content=message)
            ]
        }

    return {
        "verification_status": "failed",
        "messages": [
            AIMessage(
                content="Customer verification could not be completed."
            )
        ]
    }


# =====================================================
# NODE 4 - RISK ASSESSMENT
# =====================================================

def risk_check(state: CustomerState):

    risk = "LOW"

    message = (
        "Risk assessment completed. "
        f"Customer risk level: {risk}."
    )

    return {
        "risk_level": risk,
        "messages": [
            AIMessage(content=message)
        ]
    }


# =====================================================
# NODE 5 - CREATE CUSTOMER ACCOUNT
# =====================================================

def create_account(state: CustomerState):

    message = (
        "Your customer account has been created successfully."
    )

    return {
        "account_status": "created",
        "messages": [
            AIMessage(content=message)
        ]
    }


# =====================================================
# NODE 6 - WELCOME CUSTOMER
# =====================================================

def welcome_customer(state: CustomerState):

    name = state.get("customer_name", "Customer")

    message = (
        f"🎉 Welcome {name}! "
        "Your onboarding process is complete. "
        "Your account is ready to use."
    )

    return {
        "messages": [
            AIMessage(content=message)
        ]
    }


# =====================================================
# CONDITIONAL ROUTING
# =====================================================

def validation_router(state: CustomerState):

    if state.get("validation_status") == "valid":
        return "verify"

    return "end"


# =====================================================
# BUILD LANGGRAPH
# =====================================================

builder = StateGraph(CustomerState)

builder.add_node("collect", collect_info)
builder.add_node("validate", validate_info)
builder.add_node("verify", verify_customer)
builder.add_node("risk", risk_check)
builder.add_node("create_account", create_account)
builder.add_node("welcome", welcome_customer)


# Define workflow

builder.add_edge(START, "collect")
builder.add_edge("collect", "validate")

builder.add_conditional_edges(
    "validate",
    validation_router,
    {
        "verify": "verify",
        "end": END
    }
)

builder.add_edge("verify", "risk")
builder.add_edge("risk", "create_account")
builder.add_edge("create_account", "welcome")
builder.add_edge("welcome", END)


# =====================================================
# CHECKPOINT / MEMORY
# =====================================================

memory = MemorySaver()


# =====================================================
# COMPILE GRAPH
# =====================================================

graph = builder.compile(
    checkpointer=memory
)
