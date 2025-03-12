import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.vectorstores import FAISS
# from langchain_openai import OpenAIEmbeddings
from langchain.embeddings.openai import OpenAIEmbeddings
from transformers import pipeline
from langchain.schema import HumanMessage
from tools1 import tools

# Logging setup
logging.basicConfig(
    filename="chatbot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.info("Chatbot started")

# Load API key
load_dotenv()
OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")
if not OPEN_AI_KEY:
    raise ValueError("Missing OpenAI API key. Ensure it is set in your environment.")

# Initialize LLM
llm = ChatOpenAI(
    temperature=0,
    model="gpt-4",
    openai_api_key=OPEN_AI_KEY,
    max_tokens=2000
)

# Initialize sentiment analysis
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Conversation memory
memory = ConversationBufferWindowMemory(k=5, return_messages=True)

def custom_error_handler(e):
    return f"Parsing error: {str(e)}"

# Function to analyze sentiment
def analyze_sentiment(user_input):
    """Analyze the sentiment of the user's input."""
    result = sentiment_analyzer(user_input)[0]
    return result['label'], result['score']

# Initialize agent with dynamic handling
def initialize_real_estate_agent(memory):
    """Initialize and return the real estate agent."""
    return initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=custom_error_handler,
        memory=memory,
        max_iterations=10
    )

# Initialize the agent
agent = initialize_real_estate_agent(memory)

def process_input_with_sentiment(user_input):
    """Process user input with sentiment analysis and generate a response."""
    sentiment_label, sentiment_score = analyze_sentiment(user_input)
    logging.info(f"User input: {user_input}, Sentiment: {sentiment_label}, Score: {sentiment_score}")

    chat_history = "\n".join([f"{msg.type}: {msg.content}" for msg in memory.chat_memory.messages]) or "No previous conversation."

    prompt = f"""
    You are an intelligent real estate chatbot. Analyze the conversation history and user input to provide a concise, helpful response:
    - If it's a greeting, respond appropriately.
    - If it's a general question about real estate, provide an informative answer.
    - If it's a property search query, check for missing details (location, budget).
      - If missing, ask the user to provide the necessary details. If the user responds like "no, show me directly" or gives a similar response, then proceed directly.
      - If all details are present, retrieve suitable property recommendations.
      - Do NOT repeatedly call tools unless explicitly needed for general info.
    - If the user provides an amount in words such as '5 cr' or '1 lakh', convert it into its numerical form before proceeding.

    Conversation History:
    {chat_history}
      
    User Input: "{user_input}"
    Sentiment: {sentiment_label} (Confidence: {sentiment_score})
    Your Response:
    """

    try:
        # Debugging: Print the prompt
        print("Generated Prompt:", prompt)
        # logging.info(f"Generated Prompt: {prompt}")

        # Add user input to memory
        memory.chat_memory.add_user_message(user_input)

        # Generate response using agent
        response = agent.run(prompt)  # Use .run() instead of .invoke()

        # Ensure response is valid
        if not response or response.strip() == "":
            response = "I'm not sure how to respond. Can you rephrase?"

        # Add assistant response to memory
        memory.chat_memory.add_ai_message(response)

        return response

    except Exception as e:
        logging.error(f"Error processing input: {e}")
        return "I'm sorry, but I encountered an issue while processing your request."


def generate_dynamic_suggestions(user_input):
    """Generates 4 relevant follow-up suggestions based on the user's last message and sentiment."""
    sentiment_label, _ = analyze_sentiment(user_input)

    prompt = f"""
    Based on the user's input: '{user_input}' (Sentiment: {sentiment_label}), 
    generate 4 relevant follow-up questions that the user might want to ask next.
    Provide the suggestions as a list of strings, focusing on real estate-related queries.
    Ensure the suggestions are concise, specific, and contextually appropriate.
    """

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        suggestions = response.content.strip().split("\n")
        suggestions = [s.strip().lstrip("1234. -") for s in suggestions if s.strip()]
        return suggestions[:4]
    except Exception as e:
        logging.error(f"Suggestion generation error: {e}")
        return [
            "What are the properties near this location?",
            "Can you show me price trends in this area?",
            "Are there any RERA-approved projects here?",
            "What’s the EMI for a property in this range?"
        ]

# Export required objects and functions
__all__ = ["agent", "process_input_with_sentiment", "generate_dynamic_suggestions", "memory"]