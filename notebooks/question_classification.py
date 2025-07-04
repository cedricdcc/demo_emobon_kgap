# python notebook to investigate the question classification for nl questions

import json
import json
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import os
import jsonschema
from jsonschema import validate
import pandas as pd
from conneg_functions import generate_sparql
from sema.query import DefaultSparqlBuilder, GraphSource as KGSource, QueryResult

GDB_BASE: str = os.getenv("GDB_BASE", "http://localhost:7200/")
# print(f"{os.getenv('GDB_BASE')=}")
# print(f"{GDB_BASE=}")
GDB_REPO: str = os.getenv("GDB_REPO", "kgap")
GDB_ENDPOINT: str = f"{GDB_BASE}repositories/{GDB_REPO}"
# print(f"{GDB_ENDPOINT=}")
GDB: KGSource = KGSource.build(GDB_ENDPOINT)

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
# Define the prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant that extracts key information from questions."
            "Only return a dictionary with key-value pairs, nothing else."
            "The keys that can be used are:"
            "# - marine_region_id: The ID of the marine region to filter by."
            "# - marine_region: The name of the marine region to filter by."
            "# - observatories: The list of observatories to filter by (optional)."
            "# - depth: The depth range to filter by (optional)."
            "#   depth is a dict with keys value and operator."
            "# - contact: List of names of people or organizations to filter by (optional)."
            "# - datetime_begin: The start date for the sampling (inclusive)."
            "# - datetime_end: The end date for the sampling (inclusive)."
            "# - sampling_method: The method of sampling to filter by."
            "# - species_name: The scientific name of the species to filter by."
            "# - taxon_rank: The taxonomic rank to filter by."
            "# - taxon_id: The taxonomic ID to filter by."
            "# - sampling_id: The ID of the sampling event to filter by."
            "# - sampling_type: The type of sampling to filter by."
            "# - abundance_threshold: The threshold for sampling abundance to filter by (minimum value)."
            "# - property_filters: A list of dictionaries for filtering based on property values. Each dictionary contains:"
            "#   - property: The property to filter by."
            "#   - value: The value to filter by."
            "#   - operator: The operator to use for filtering (e.g., '=', '>', '<', '>=', '<=')."
            "#   - value_type: The type of the value (e.g., 'int', 'float', 'str')."
            "follow the json schema: {schema} provided to you, and do not include any other text in the response.",
        ),
        ("user", "Extract key information for the following questions: {question}"),
    ]
)

prompt_check_properties = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant corrects a given dictionary and checks if values are filled in correctly."
            "the dictionary wil be in the following format: {schema}"
            "first check if any property filters should have been other values in the dictionary,"
            "check if the key represents a key that is given in the json schema: {schema},"
            "then check if any of the property_fitlers are not in the list of properties: {properties}"
            "if not correct them to the closest related value in the list of properties,"
            "if there are no properties in the list that match the property filter, remove the property filter from the dictionary."
            "Only return the corrected dictionary with key-value pairs, nothing else.",
        ),
        ("user", "correct the following dictionary: {dictionary}"),
    ]
)

schema = {
    "type": "object",
    "properties": {
        "marine_region_id": {"type": "string"},
        "marine_region": {"type": "string"},
        "observatories": {"type": "array", "items": {"type": "string"}},
        "depth": {
            "type": "object",
            "properties": {"value": {"type": "number"}, "operator": {"type": "string"}},
            "required": ["value", "operator"],
        },
        "contact": {"type": "array", "items": {"type": "string"}},
        "datetime_begin": {"type": "string", "format": "date-time"},
        "datetime_end": {"type": "string", "format": "date-time"},
        "sampling_method": {"type": "string"},
        "species_name": {"type": "string"},
        "taxon_rank": {"type": "string"},
        "taxon_id": {"type": "string"},
        "sampling_id": {"type": "string"},
        "sampling_type": {"type": "string"},
        "abundance_threshold": {"type": "number"},
        "property_filters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "property": {"type": "string"},
                    "value": {},
                    "operator": {"type": "string"},
                    "value_type": {"type": "string"},
                },
                "required": ["property", "value", "operator", "value_type"],
            },
        },
    },
}


# Function to validate JSON
def validate_json(data):
    try:
        validate(instance=data, schema=schema)
        return True, "JSON is valid."
    except jsonschema.exceptions.ValidationError as err:
        return False, f"JSON validation error: {err.message}"


# function to clean up the answer of the llm
def clean_answer(answer) -> dict | None:
    # Remove any leading or trailing whitespace
    try:
        answer = answer.strip()
    except AttributeError:
        print("The answer is not a string.")
        return answer
    # Ensure the answer is a valid JSON string
    if not answer.startswith("{") or not answer.endswith("}"):
        print("The answer is not a valid JSON object.")
        return None
    json_answer = json.loads(answer)
    is_valid, message = validate_json(json_answer)
    print(message)

    return json_answer if is_valid else None


"""
# Load and filter data
def load_and_filter_data(file_path):
    # Load the JSON data
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Convert the data to a DataFrame
    df = pd.DataFrame(data)

    # Filter rows where 'question' starts with 'SELECT'
    filtered_question = df[df["question"].str.startswith("{")]

    # Filter rows where 'sparql_select' ends with '...'
    filtered_sparql = df[df["sparql_query"].str.endswith("...")]

    # Exclude the filtered rows
    df = df[~df["question"].str.startswith("SELECT")]
    df = df[~df["question"].str.startswith("{")]
    df = df[~df["sparql_query"].str.endswith("...")]

    return df


data_file = "./all_generated_questions.json"
dataset = load_and_filter_data(data_file)
print(f"Loaded {len(dataset)} rows from {data_file}")


for index, row in dataset.iterrows():
    question = row["question"]
    print(question)

    print(f"Generating variables for:  {question}")
    messages = prompt.format_messages(question=question, schema=schema)
    response = llm.invoke(messages)
    print(f"Response: {response}")
    if response := clean_answer(response):
        print(f"Cleaned Response: {response}")
        # make object with question and response
        question_variables = {
            "question": question,
            "variables": clean_answer(response),
        }
"""

# Prompt the user for a question instead of reading from the file
user_question = input("Enter your question: ")
print(f"Generating variables for: {user_question}")
messages = prompt.format_messages(question=user_question, schema=schema)
response = llm.invoke(messages)
print(f"Response: {response}")
if cleaned := clean_answer(response):
    print(f"Cleaned Response: {cleaned}")

    # there should be a qc on the values of the cleaned response
    # to make sure that the inserted values are valid for the sparql query
    sparql = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#> 
    PREFIX sosa: <http://www.w3.org/ns/sosa/>
    PREFIX purl: <http://purl.org/dc/terms/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX sampl: <https://data.emobon.embrc.eu/ns/sampling#>
    SELECT DISTINCT ?labelproperty
    WHERE  {
    ?sample a sosa:Sample .
    ?sample sosa:isResultOf ?event .
    ?event sampl:linkedToObservatory ?observatory .
    ?observations a sosa:Observation .
    ?observations sosa:hasFeatureOfInterest ?sample .
    ?observations sosa:observedProperty ?property .
    ?property rdfs:label ?labelproperty .
    }
    """
    result: QueryResult = GDB.query(sparql=sparql)
    print(f"Distinct properties: {result.to_dict()}")
    # for the sake of timesaving lets already get the properties.
    properties: dict[str, list[str]] = {
        "labelproperty": [
            "redox_potential",
            "sediment_temp",
            "sea_surf_salinity",
            "ph",
            "sea_surf_temp",
            "sea_subsurf_temp",
            "sea_subsurf_salinity",
            "chlorophyll",
            "nitrate",
            "diss_oxygen",
            "organism_count",
            "density",
            "phaeopigments",
            "ammonium",
            "conduc",
            "pigments",
            "turbidity",
            "silicate",
            "nitrite",
            "phosphate",
            "down_par",
            "pressure",
        ]
    }

    # Check if the property filters are valid
    messages = prompt_check_properties.format_messages(
        schema=schema, dictionary=cleaned, properties=properties["labelproperty"]
    )
    response = llm.invoke(messages)
    print(f"Response from property check: {response}")
    cleaned = clean_answer(response)
    if cleaned is None:
        print("The response from the property check is not valid.")
        exit(1)
    print(f"Cleaned Response after property check: {cleaned}")

    # Generate SPARQL query using the cleaned variables
    sparql_query: str = generate_sparql("metagenomic_sampling_subset.sparql", **cleaned)
    print(f"Generated SPARQL query: {sparql_query}")
