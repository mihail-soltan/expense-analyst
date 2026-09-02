import streamlit as st
from assistant import create_assistant
from db.db_save import save_conversation, save_feedback
from judge import evaluate_relevance

assistant = create_assistant()

st.title("Expense Analyst")

user_input = st.text_input("Enter your question:")

if st.button("Ask"):
    with st.spinner("Processing..."):
        input_messages = [
                    {'type': 'user_input', 'content': [{"type": "text", "text":user_input}]}
                ]
        answer = assistant.rag(input_messages)
        st.success("Completed!")
        st.write(answer["output"])

        record = assistant.last_call
        st.write(f"Response time: {record.response_time:.2f}s")
        st.write(f"Prompt tokens: {record.prompt_tokens}")
        st.write(f"Completion tokens: {record.completion_tokens}")
        st.write(f"Cost: ${record.cost}")

        conversation_id = save_conversation(record, user_input)
        st.session_state.conversation_id = conversation_id

        relevance, explanation = evaluate_relevance(user_input, answer)
        save_feedback(conversation_id, "judge",
                relevance=relevance, explanation=explanation)
        st.write(f"Relevance: {relevance}")
        st.write(f"Explanation: {explanation}")

conversation_id = st.session_state.get("conversation_id")

if conversation_id is not None:
    col1, col2 = st.columns(2)

    with col1:
        if st.button("+1", key=f"feedback_up_{conversation_id}"):
            save_feedback(conversation_id, "user", score=1)
            st.success("Thanks!")

    with col2:
        if st.button("-1", key=f"feedback_down_{conversation_id}"):
            save_feedback(conversation_id, "user", score=-1)
            st.success("Thanks for the feedback!")