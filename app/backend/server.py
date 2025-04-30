from flask import Flask, request, jsonify
from langchain_community.chains.graph_qa.ontotext_graphdb import OntotextGraphDBQAChain
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
llm = OllamaLLM(
    model=MODEL,
    base_url=url_ollama,
    temperature=0.7,
    num_predict=400,
    repeat_penalty=1.3,
    repeat_last_n=256,
    num_ctx=8192,
)

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
    llm=llm,
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True,
    max_fix_retries=1,
)


@app.route("/test", methods=["GET"])
def hello_world():
    return "Hello, World!"


@app.route("/api/schema", methods=["GET"])
def get_schema():
    try:
        # Get the schema from the graph
        schema = graph.schema
        logging.info(f"Schema: {schema}")
        return jsonify({"schema": schema})
    except Exception as e:
        logging.error(f"Error retrieving schema: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/querysparql", methods=["POST"])
def querysparql():
    user_message = request.json.get("message", "")
    logging.info(f"Received message: {user_message}")
    if not user_message:
        return jsonify({"reply": "Error: No message provided."}), 400

    try:
        # Use the QA chain to process the user's message
        response = qa_chain.run(user_message)
        logging.info(f"Response: {response}")
        bot_reply = (
            response if response else "I couldn't find an answer to your question."
        )
    except Exception as e:
        bot_reply = f"Error: {str(e)}"

    return jsonify({"reply": bot_reply})


@app.route("/api/chat", methods=["POST"])
def chat():
    pass


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
