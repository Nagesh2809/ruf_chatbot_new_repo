
# streamlit run  streamlit_app.py

import os
import logging
import base64
import streamlit as st
from ruf11 import agent, process_input_with_sentiment, generate_dynamic_suggestions, memory
from tools1 import calculate_emi_tool

# Encode the image
try:
    with open("konu-1.png", "rb") as img_file:
        encoded_img = base64.b64encode(img_file.read()).decode()
except FileNotFoundError:
    encoded_img = ""

# Streamlit configuration
st.set_page_config(page_title="Konu Real Estate Assistant", layout="centered")

# Display header with logo
st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="data:image/png;base64,{encoded_img}" alt="KONU Logo" width="200">
        <h1 style="color: #F4004D; margin-top: 10px;">Real Estate Assistant</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

def main_chat():
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "suggestion_clicked" not in st.session_state:
        st.session_state.suggestion_clicked = False

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Type your question here...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.suggestion_clicked = False
        process_input(prompt)
        st.rerun()

    last_user_message = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), None)
    if last_user_message:
        suggestions = generate_dynamic_suggestions(last_user_message)
        st.subheader("Suggested Questions")
        cols = st.columns(2)
        for i, question in enumerate(suggestions):
            if cols[i % 2].button(question, key=f"sugg_dynamic_{i}"):
                st.session_state.messages.append({"role": "user", "content": question})
                st.session_state.suggestion_clicked = False
                process_input(question)
                st.rerun()

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.suggestion_clicked = False
        st.rerun()

def process_input(prompt):
    """Handles user input and generates a sentiment-aware response."""
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = process_input_with_sentiment(prompt)  # Use sentiment-aware function
                print("Agent Response:", response)  # Debugging
                st.write("Agent Response:", response)  # Debugging
            except Exception as e:
                response = f"An error occurred: {e}"
                logging.error(f"Processing error: {e}")

            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main_chat()