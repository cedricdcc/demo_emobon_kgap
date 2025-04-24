from flask import Flask, request, jsonify
from langchain.chains import OntotextGraphDBQAChain
from langchain_community.graphs import OntotextGraphDBGraph
from langchain_ollama import OllamaLLM

from flask_cors import CORS

app = Flask(__name__)
CORS(app)
MODEL = "llama3.1:8b"
# Specify ollama endpoint
llama_three = OllamaLLM(model=MODEL)

READ_URI_STORE = "http://localhost:7200/repositories/kgap"
WRITE_URI_STORE = "http://localhost:7200/repositories/kgap/statements"

# Configure the Ontotext GraphDB connection
graph = OntotextGraphDBGraph(
    query_endpoint=READ_URI_STORE,
    query_ontology="CONSTRUCT  {?s ?p ?o} FROM <urn:sync:emobon_ontology.ttl> WHERE {?s ?p ?o}",
)

# Initialize the QA chain
qa_chain = OntotextGraphDBQAChain.from_llm(
    llm=llama_three, graph=graph, verbose=True, allow_dangerous_requests=True
)


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
    app.run(debug=True)
