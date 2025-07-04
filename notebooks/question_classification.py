# python notebook to investigate the question classification for nl questions

import json
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain_core.prompts import ChatPromptTemplate
import os
import pandas as pd

# Specify the model name
MODEL_NAME = "Qwen/Qwen3-8B"

# Initialize the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

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

for index, row in dataset.head(3).iterrows():
    question = row["question"]
    print(question)

    messages = prompt.format_messages(question=question)

    text = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
    print(text)

    # Generate a response
    outputs = model.generate(text, max_length=150, num_return_sequences=1)

    # Decode the response
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(response)
