from langchain_community.graphs import OntotextGraphDBGraph
from langchain_community.llms import ollama
from langchain.chains.graph_qa.ontotext_graphdb import OntotextGraphDBQAChain

READ_URI_STORE = "http://localhost:7200/repositories/kgap"
WRITE_URI_STORE = "http://localhost:7200/repositories/kgap/statements"

DEMO_QUESTION = "How many observations are there?"
MODEL = "qwen:0.5b"  # llama3:8b


# the main problem that i'm facing right now is the query ontology
# how are we going to define our classes
graph = OntotextGraphDBGraph(
    query_endpoint=READ_URI_STORE,
    query_ontology="CONSTRUCT  {?s ?p ?o} FROM <urn:sync:emobon_ontology.ttl> WHERE {?s ?p ?o}",
)

# specify ollama endpoint

llama_three = ollama.Ollama(model=MODEL)

chain = OntotextGraphDBQAChain.from_llm(llama_three, graph=graph, verbose=True)

chain.invoke({chain.input_key: DEMO_QUESTION})[chain.output_key]
