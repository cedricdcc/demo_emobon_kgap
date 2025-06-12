# this file is a testfile to see if the concept of taking in a sparql query and asking
# a llm to generate a question that matches the query works
import json
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import os


MODEL = "qwen3:8b"  # Specify the model you want to use
llm = OllamaLLM(
    model=MODEL,
    base_url="http://localhost:11434",  # Specify the URL of your Ollama instance
    temperature=0.7,
    num_predict=-1,
    repeat_penalty=1.3,
    repeat_last_n=256,
    num_ctx=8192,
    format="json",  # Ensure the response is in JSON format
)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant that generates questions based on SPARQL queries."
            "Only return the question, do not include any additional text."
            "when encountering a '~*' in the query with * being a number, assume it is a wildcard"
            "and replace it with a space in the question."
            "for instance ('ROSKOGO~5 VB~5') are 2 separate terms with a wildcard and should be ROSKOGO or VB in the question."
            "Do not use any markdown in the question, just plain text."
            "Generate questions with different levels of specificity based on the query."
            "Also generate questions asking for different aspects of the query, for instance,"
            "if sample, observatory, and event are in the query, you can ask about the sample,"
            "the observatory, or the event, or a combination of them."
            "Make sure to always include the main entities and relationships in all the questions."
            "These will be in the lines where there is onto:fts , FILTER regex and FILTER"
            "give the reponse in format of a dictionary with keys sparql_query and question, like this: "
            "'sparql_query': your_sparql_query, 'questions': ['your_question1', 'your_question2']"
            "do not include any other text in the response.",
        ),
        ("user", "Generate a question for the following SPARQL query: {sparql_query}"),
    ]
)

# Example SPARQL query
sparql_query = """
PREFIX prod: <https://data.emobon.embrc.eu/ns/product#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX emobon: <https://data.emobon.embrc.eu/ns/core#>
PREFIX sampl: <https://data.emobon.embrc.eu/ns/sampling#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX onto: <http://www.ontotext.com/>
PREFIX qudt: <http://qudt.org/schema/qudt/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT
  ?sample
  ?observatory
  ?event
  
  ?taxonannotation
  ?taxonid
    
  ?rank
WHERE {
  ?sample a sosa:Sample .
  # link event
  ?sample sosa:isResultOf ?event .
  # link observatory
  ?event sampl:linkedToObservatory ?observatory .
  # Optional filters
  # name of observatory
  
  ?observatory emobon:observatoryId ?observatory_id .
  ?observatory_id onto:fts ("ROSKOGO~5 VB~5") .# depth filter
  
  ?event prov:startedAtTime ?datetime_begin . 
  
  # linking between taxon annotations and sample
  ?taxonannotation a prod:TaxonomicAnnotation .
  ?taxonannotation prod:ofSample ?sample .
  ?taxonannotation dct:identifier ?taxonid .
      
  ?taxonid dct:taxonRank ?rank .
  ?rank onto:fts ("super kingdom~5") .
}
"""


# Generate the question using the LLM
def generate_question(sparql_query):
    messages = prompt.format_messages(sparql_query=sparql_query)
    response = llm.invoke(messages)

    # Ensure the response is parsed as structured output
    try:
        response_data = eval(response)  # Convert string to dictionary
        if not isinstance(response_data, dict) or "questions" not in response_data:
            raise ValueError(
                "Response does not contain the expected structured output."
            )
    except Exception as e:
        raise ValueError(f"Failed to parse structured output: {e}")

    # Handle response as a string or list
    if isinstance(response, str):
        return response_data
    elif (
        isinstance(response, list)
        and len(response) > 0
        and hasattr(response[0], "content")
    ):
        return response[0].content
    else:
        raise ValueError("Unexpected response format from OllamaLLM.invoke")


if __name__ == "__main__":

    # ammount of sparql query to generate question for
    test = 3
    folder_generated_sparql = "generated_sparql_queries"
    # use range to loop over files in the folder
    for i in range(test):
        # Read the SPARQL query from a file
        sparql_file_path = os.path.join(folder_generated_sparql, f"query_{i}.sparql")
        with open(sparql_file_path, "r") as f:
            sparql_query = f.read().strip()
        # Generate the question based on the SPARQL query
        print(f"Generating question for SPARQL query from {sparql_file_path}")
        question = generate_question(sparql_query)
        with open(f"generated_question_{i}.txt", "w") as f:
            json.dump(question, f, indent=2)
        print(f"Generated question for query_{i}.sparql:", question)
