from langchain_community.graphs import OntotextGraphDBGraph
from langchain_community.chains.graph_qa.ontotext_graphdb import OntotextGraphDBQAChain
from langchain_ollama import OllamaLLM

READ_URI_STORE = "http://localhost:7200/repositories/kgap"
WRITE_URI_STORE = "http://localhost:7200/repositories/kgap/statements"

MODEL = "llama3.1:8b"  # llama3:8b

# Initialize the graph
graph = OntotextGraphDBGraph(
    query_endpoint=READ_URI_STORE,
    query_ontology="CONSTRUCT  {?s ?p ?o} FROM <urn:sync:emobon_ontology.ttl> WHERE {?s ?p ?o}",
)

# Specify ollama endpoint
llama_three = OllamaLLM(model=MODEL)

# Create the QA chain
chain = OntotextGraphDBQAChain.from_llm(
    llm=llama_three, graph=graph, verbose=True, allow_dangerous_requests=True
)


# Terminal-based chatbot
def chatbot():
    print("Welcome to the Emobon Chatbot!")
    print("Type 'exit' to quit the chatbot.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        try:
            response = chain.invoke({chain.input_key: user_input})[chain.output_key]
            print(f"Assistant: {response}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    chatbot()
