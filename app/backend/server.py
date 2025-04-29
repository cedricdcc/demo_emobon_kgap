from flask import Flask, request, jsonify
from langchain.chains import OntotextGraphDBQAChain
from langchain_community.graphs import OntotextGraphDBGraph
from langchain_ollama import OllamaLLM
from flask_cors import CORS
import time
import logging

app = Flask(__name__)
CORS(app)
# MODEL = "llama3.1:8b"  # llama3.1:8b" # Specify the model you want to use

# for lower end models, use the following:
# MODEL = "gemma3:1b" # or 4b
MODEL = "llama3.1:8b"  # Specify the model you want to use llama3.1:8b deepseek-r1:1.5b

# ollama url
url_ollama = "http://ollama:11434"  # Specify the URL of your Ollama instance


# Specify ollama endpoint
llama_three = OllamaLLM(model=MODEL, base_url=url_ollama)

READ_URI_STORE = "http://graphdb:7200/repositories/kgap"
WRITE_URI_STORE = "http://graphdb:7200/repositories/kgap/statements"

# Configure logging
logging.basicConfig(level=logging.INFO)

time.sleep(10)  # Wait for the GraphDB service to be ready

# Configure the Ontotext GraphDB connection
graph = OntotextGraphDBGraph(
    query_endpoint=READ_URI_STORE,
    query_ontology="CONSTRUCT  {?s ?p ?o} FROM <urn:sync:emobon_ontology.ttl> WHERE {?s ?p ?o}",
)

# Initialize the QA chain
qa_chain = OntotextGraphDBQAChain.from_llm(
    llm=llama_three, graph=graph, verbose=True, allow_dangerous_requests=True
)


@app.route("/test", methods=["GET"])
def hello_world():
    return "Hello, World!"


@app.route("/api/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    print(f"User message: {user_message}")
    if not user_message:
        return jsonify({"reply": "Error: No message provided."}), 400

    try:
        # Use the QA chain to process the user's message
        response = qa_chain.run(user_message)
        bot_reply = (
            response if response else "I couldn't find an answer to your question."
        )
    except Exception as e:
        bot_reply = f"Error: {str(e)}"

    return jsonify({"reply": bot_reply})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
