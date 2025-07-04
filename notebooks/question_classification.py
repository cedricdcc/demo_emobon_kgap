# python notebook to investigate the question classification for nl questions

import json
import json
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import os
import pandas as pd

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
            "#   - value_type: The type of the value (e.g., 'int', 'float', 'str').",
        ),
        ("user", "Extract key information for the following questions: {question}"),
    ]
)


# function to clean up the answer of the llm
def clean_answer(answer) -> dict | None:
    # Remove any leading or trailing whitespace
    answer = answer.strip()
    # Ensure the answer is a valid JSON string
    if not answer.startswith("{") or not answer.endswith("}"):
        print("The answer is not a valid JSON object.")
        return None
    return answer


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


outfile = "./question_variables.json"
data_file = "./all_generated_questions.json"
dataset = load_and_filter_data(data_file)
print(f"Loaded {len(dataset)} rows from {data_file}")

for index, row in dataset.head(30).iterrows():
    question = row["question"]
    print(question)

    print(f"Generating variables for:  {question}")
    messages = prompt.format_messages(question=question)
    response = llm.invoke(messages)
    print(f"Response: {response}")
    if response := clean_answer(response):
        print(f"Cleaned Response: {response}")
        # make object with question and response
        question_variables = {
            "question": question,
            "variables": clean_answer(response),
        }
        print(f"Question Variables: {question_variables}")
        # Save the question variables to a JSON file
        with open(outfile, "a") as f:
            json.dump(question_variables, f, indent=2)
        print(f"Question variables saved to {outfile}")
