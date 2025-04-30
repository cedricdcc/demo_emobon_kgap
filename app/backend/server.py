from flask import Flask, request, jsonify
from langchain_community.chains.graph_qa.ontotext_graphdb import OntotextGraphDBQAChain
from langchain_community.graphs import OntotextGraphDBGraph
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from flask_cors import CORS
from flask import stream_with_context, Response
import time
import json
import logging

app = Flask(__name__)
CORS(app)
# MODEL = "llama3.1:8b"  # llama3.1:8b" # Specify the model you want to use

# for lower end models, use the following:
# MODEL = "gemma3:1b" # or 4b or qwen3:0.6b
MODEL = "qwen3:8b"  # Specify the model you want to use llama3.1:8b deepseek-r1:1.5b

dev_mode = True  # Set to True if running in development mode

# ollama url
url_ollama = "http://ollama:11434"  # Specify the URL of your Ollama instance
if dev_mode:
    url_ollama = "http://localhost:11434"  # Specify the URL of your Ollama instance

# Specify ollama endpoint
llm = OllamaLLM(
    model=MODEL,
    base_url=url_ollama,
    temperature=0.7,
    num_predict=-1,
    repeat_penalty=1.3,
    repeat_last_n=256,
    num_ctx=8192,
)

READ_URI_STORE = (
    "http://graphdb:7200/repositories/kgap"  # localhost if running in development mode
)
WRITE_URI_STORE = (
    "http://graphdb:7200/repositories/kgap/statements"  # localhos tin dev mode
)


if dev_mode:
    # If running in development mode, use localhost
    READ_URI_STORE = "http://localhost:7200/repositories/kgap"
    WRITE_URI_STORE = "http://localhost:7200/repositories/kgap/statements"

# Configure logging
logging.basicConfig(level=logging.INFO)

if not dev_mode:
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
    max_fix_retries=2,
)

SYSTEM = """You are a helpful assistant. You will be given a question and you need to answer it based on the provided knowledge graph.
If you don't know the answer, say "I don't know". If the question is not related to the knowledge graph, say "I can't help with that".
Be concise and clear in your answers.
You are not allowed to use any external knowledge or information outside of the provided knowledge graph.
Keep your answers short and to the point.
Do not include any explanations or apologies in your responses.
"""

USER_PROMPT = """
Write a SPARQL SELECT query for querying a graph database.
The ontology schema delimited by triple backticks in Turtle format is:
```
{graph}
```
Use only the classes and properties provided in the schema to construct the SPARQL query.
Do not use any classes or properties that are not explicitly provided in the SPARQL query.
Include all necessary prefixes.
Do not include any explanations or apologies in your responses.
Do not wrap the query in backticks.
Do not include any text except the SPARQL query generated.
The question delimited by triple backticks is:
```
{question}
```
"""


##### Define the Flask routes
@app.route("/")
def index():
    return "to be implemented"


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
        response = qa_chain.invoke(user_message)
        logging.info(f"Response: {response}")
        bot_reply = (
            response if response else "I couldn't find an answer to your question."
        )
    except Exception as e:
        bot_reply = f"Error: {str(e)}"

    return jsonify({"reply": bot_reply})


@app.route("/api/chat", methods=["POST"])
def chat():
    prompt_template = ChatPromptTemplate(
        [
            ("system", SYSTEM),
            ("user", USER_PROMPT),
        ]
    )
    user_message = request.json.get("message", "")
    logging.info(f"Received message: {user_message}")
    if not user_message:
        return jsonify({"reply": "Error: No message provided."}), 400

    try:
        prompt = prompt_template.invoke(
            {"question": user_message, "graph": graph.schema}
        )
        logging.info(f"Prompt: {prompt}")
        response = llm.invoke(prompt)
        logging.info(f"Response: {response}")
        bot_reply = (
            response if response else "I couldn't find an answer to your question."
        )
        return jsonify({"reply": bot_reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def generate_tokens(prompt):
    """
    Generate tokens for the given prompt using the LLM.
    """
    for chunks in llm.stream(prompt):
        yield chunks


@app.route("/users/chat", methods=["POST"])
def users_chat():
    """
    Streams responses based on the user's message.
    """
    prompt_template = ChatPromptTemplate(
        [
            ("system", SYSTEM),
            ("user", USER_PROMPT),
        ]
    )
    user_message = request.json.get("message", "")
    logging.info(f"Received message: {user_message}")
    if not user_message:
        return jsonify({"reply": "Error: No message provided."}), 400

    def generate_json(user_message, graph):
        prompt = prompt_template.invoke({"question": user_message, "graph": graph})
        logging.info(f"Prompt: {prompt}")
        full_response = ""
        for token in generate_tokens(prompt):
            full_response += token
            json_response = {
                "reply": token,
                "done": False,
            }
            json_str = json.dumps(json_response)
            json_bytes = json_str.encode("utf-8")
            yield json_bytes
            yield b"\n"
        # when streaming is done, send the final response
        json_response = {
            "reply": full_response,
            "done": True,
        }
        json_str = json.dumps(json_response)
        json_bytes = json_str.encode("utf-8")
        yield json_bytes

    # response to user message
    return Response(
        stream_with_context(generate_json(user_message, graph.schema)),
        mimetype="application/json",
    )


@app.route("/test/streaming", methods=["GET", "POST"])
def test_streaming():
    """
    Test streaming response.
    """
    prompt_template = ChatPromptTemplate(
        [
            ("system", SYSTEM),
            ("user", USER_PROMPT),
        ]
    )
    user_message = "what is emobon?"
    logging.info(f"Received message: {user_message}")
    if not user_message:
        return jsonify({"reply": "Error: No message provided."}), 400

    def generate_json(user_message, graph):
        prompt = prompt_template.invoke({"question": user_message, "graph": graph})
        logging.info(f"Prompt: {prompt}")
        full_response = ""
        for token in generate_tokens(prompt):
            full_response += token
            print(f"Token: {token}")
            json_response = {
                "reply": token,
                "full_response": full_response,
                "done": False,
            }
            json_str = json.dumps(json_response)
            yield json_str.encode("utf-8")
            yield b"\n"

    generate_json(user_message, graph.schema)
    return Response(
        stream_with_context(generate_json(user_message, graph.schema)),
        mimetype="application/json",
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
