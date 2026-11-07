
import uuid
import streamlit as st

from langchain_core.messages import HumanMessage, AIMessage

from graph import graph


# ---------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------

st.set_page_config(
    page_title="Customer Onboarding Agent",
    page_icon="🤖",
    layout="centered"
)


# ---------------------------------------
# SESSION INITIALIZATION
# ---------------------------------------

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ---------------------------------------
# NEW CUSTOMER BUTTON
# ---------------------------------------

if st.button("➕ Start New Customer"):

    st.session_state.thread_id = str(uuid.uuid4())

    st.session_state.chat_history = []

    st.rerun()


# ---------------------------------------
# TITLE
# ---------------------------------------

st.title("🤖 Customer Onboarding Agent")

st.write(
    "LangGraph Stateful Workflow with Streamlit"
)


# ---------------------------------------
# DISPLAY PREVIOUS MESSAGES
# ---------------------------------------

for message in st.session_state.chat_history:

    with st.chat_message(message["role"]):
        st.write(message["content"])


# ---------------------------------------
# USER INPUT
# ---------------------------------------

user_input = st.chat_input(
    "Enter customer information..."
)


if user_input:

    # Display user message

    with st.chat_message("user"):
        st.write(user_input)

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": user_input
        }
    )


    # -----------------------------------
    # LANGGRAPH CONFIGURATION
    # -----------------------------------

    config = {
        "configurable": {
            "thread_id": st.session_state.thread_id
        }
    }


    # -----------------------------------
    # GET PREVIOUS GRAPH STATE
    # -----------------------------------

    previous_state = graph.get_state(config)

    previous_message_count = len(
        previous_state.values.get("messages", [])
    )


    # -----------------------------------
    # RUN LANGGRAPH
    # -----------------------------------

    try:

        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(content=user_input)
                ]
            },
            config=config
        )


        # -----------------------------------
        # GET ONLY NEW AI MESSAGES
        # -----------------------------------

        new_messages = result["messages"][previous_message_count:]

        assistant_messages = []

        for message in new_messages:

            if isinstance(message, AIMessage):
                assistant_messages.append(message.content)


        # -----------------------------------
        # DISPLAY AI RESPONSES
        # -----------------------------------

        if assistant_messages:

            with st.chat_message("assistant"):

                for message in assistant_messages:

                    st.write(message)

                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": message
                        }
                    )

        else:

            st.info("No new assistant response was generated.")


    except Exception as e:

        st.error(
            f"An error occurred: {str(e)}"
        )
