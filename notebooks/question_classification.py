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

"""
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
    question_variables = {
        "question": user_question,
        "variables": cleaned,
    }
    # Generate SPARQL query using the cleaned variables
    sparql_query: str = generate_sparql("metagenomic_sampling_subset", **cleaned)
    print(f"Generated SPARQL query: {sparql_query}")
