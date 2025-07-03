import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import sys


def load_model(model_path):
    """
    Load a PyTorch model from the specified path.
    Args:
        model_path (str): Path to the saved model file.
    Returns:
        torch.nn.Module: Loaded PyTorch model.
    Raises:
        FileNotFoundError: If the model file does not exist.
        RuntimeError: If the model file is corrupted or incompatible.
    """
    try:
        # Define the model architecture
        model = AutoModelForCausalLM.from_pretrained("HuggingFaceTB/SmolLM2-135M")

        # Load the state dictionary
        state_dict = torch.load(model_path)
        model.load_state_dict(state_dict, strict=False)

        # Set the model to evaluation mode
        model.eval()
        return model
    except FileNotFoundError:
        raise FileNotFoundError(f"Model file not found at {model_path}.")
    except RuntimeError as e:
        raise RuntimeError(f"Failed to load the model: {e}")


def query_model(model, question, tokenizer):
    """
    Query the model with a given question.
    Args:
        model (torch.nn.Module): The loaded PyTorch model.
        question (str): The input question.
        tokenizer (transformers.PreTrainedTokenizer): Tokenizer for preprocessing the input.
    Returns:
        str: The model's response.
    """
    try:
        # Tokenize the input question
        inputs = tokenizer(question, return_tensors="pt")

        # Perform inference
        outputs = model.generate(**inputs)

        # Decode the output tokens to a string
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
    except Exception as e:
        raise RuntimeError(f"Error during model inference: {e}")


def main():
    """
    Main function to load the model, accept user input, and query the model.
    """
    model_path = "saved_models/trained_model.pt"

    try:
        # Load the tokenizer
        tokenizer = AutoTokenizer.from_pretrained("bigscience/bloomz-560m")

        # Load the model
        model = load_model(model_path)
        print("Model loaded successfully.")

        # Accept a question from the user
        question = input("Enter your question: ")

        # Query the model
        response = query_model(model, question, tokenizer)
        print(f"Model's response: {response}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
