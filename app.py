from flask import Flask, request, jsonify
import uuid
import openai
import os
import pandas as pd
from pydantic import BaseModel
from dotenv import load_dotenv

app = Flask(__name__)

# Load the CSV file
database_file = "database.csv"
df = pd.read_csv(database_file)

# OpenAI API Key (set as an environment variable for security)
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# In-memory storage for conversations
conversations = {}

hello_message = "Hello, I can help you check the status of, and cancel your current orders. How may I help you today?"

# Entry state
conversation_start = {
    "turn": 1,
    "agent_utterance": hello_message,
    "user_response": "",
    "role": "assistant"
}

def query_order_status(order_id):
    order = df[df['order_id'] == order_id]
    if not order.empty:
        return order.iloc[0]['status']
    return "Order not found"

def cancel_order(order_id):
    global df
    if order_id in df['order_id'].values:
        df.loc[df['order_id'] == order_id, 'status'] = 'canceled'
        df.to_csv(database_file, index=False)
        return "Order has been canceled"
    return "Order not found"

example_jsons = [
    {"intent": "query", "id": 12345},
    {"intent": "cancel", "id": 23456}
]

class UttClassification(BaseModel):
    intent: str
    id: int

def process_user_message(message):
    try:
        response = openai.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a classifier. Extract the intent and return a JSON object with 'intent' and 'id' (5-digit integer). You have two classifications possible on return, 'query' or 'cancel'. When a user asks anything like 'What is the status of order 12345' the intent is 'query' and the id is 12345. If the user wants to 'cancel order 12345' the intent will be 'cancel' and the id is again 12345. Here are some example JSONs: {example_jsons}"
                },
                {"role": "user", "content": message}
            ],
            response_format=UttClassification,
        )
        classification = response.choices[0].message.parsed.model_dump()
        return {"intent": classification.get("intent", "unknown"), "id": classification.get("id", "unknown")}
    except Exception as e:
        print(f"Exception: {e}")  # Print the actual error
        return {"error": str(e)}

@app.route('/')
def home():
    return "Flask API is running!"

# Error handling for internal server errors
@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": "Internal server error", "message": str(error)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not found", "message": str(error)}), 404

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({"error": "Bad request", "message": str(error)}), 400

@app.route('/conversations', methods=['POST'])
def start_conversation():
    conversation_id = str(uuid.uuid4())
    conversations[conversation_id] = [conversation_start.copy()]
    return jsonify({"agent_utterance": conversation_start["agent_utterance"], "conversation_id": conversation_id}), 201

@app.route('/conversations/<conversation_id>/messages', methods=['GET'])
def get_messages(conversation_id):
    if conversation_id not in conversations:
        return jsonify({"error": "Conversation not found"}), 404
    return jsonify({"messages": conversations[conversation_id]}), 200

@app.route('/conversations/<conversation_id>/messages', methods=['POST'])
def add_message(conversation_id):
    if conversation_id not in conversations:
        return jsonify({"error": "Conversation not found"}), 404
    
    data = request.get_json()
    if "message" not in data:
        return jsonify({"error": "Message content is required"}), 400
    
    # Get user message
    user_message = data.get("message")
    conversation = conversations[conversation_id]
    for turn in conversation:
        if turn["turn"] == len(conversation):
            turn["user_response"] = user_message


    # Get response from OpenAI model
    agent_response = process_user_message(user_message)
    id_to_lookup = agent_response['id']

    if agent_response['intent'] == 'query':
        query_response = query_order_status(order_id=id_to_lookup)
        agent_reply = f"The status of your order {id_to_lookup} is {query_response}"
    elif agent_response['intent'] == 'cancel':
        cancel_order(order_id=id_to_lookup)
        agent_reply = f"Order {id_to_lookup} has been cancelled"
    else:
        agent_reply = "I didn't understand your request."

    # Update conversation with new turn
    new_turn = {
        "turn": len(conversation) + 1,
        "agent_utterance": agent_reply,
        "user_response": "",
        "role": "assistant"
    }
    conversations[conversation_id].append(new_turn)
    return jsonify({"agent_utterance": agent_reply, "id": conversation_id}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
