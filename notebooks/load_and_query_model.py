import torch
from transformers import AutoModelForCausalLM
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
        model = AutoModelForCausalLM.from_pretrained("bigscience/bloomz-560m")

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


def query_model(model, question):
    """
    Query the model with a given question.
    Args:
        model (torch.nn.Module): The loaded PyTorch model.
        question (str): The input question.
    Returns:
        str: The model's response.
    """
    # Assuming the model takes a string input and outputs a string response
    # Modify this logic based on the actual model's input/output requirements
    try:
        response = model(question)
        return response
    except Exception as e:
        raise RuntimeError(f"Error during model inference: {e}")


def main():
    """
    Main function to load the model, accept user input, and query the model.
    """
    model_path = "saved_models/trained_model.pt"

    try:
        # Load the model
        model = load_model(model_path)
        print("Model loaded successfully.")

        # Accept a question from the user
        question = input("Enter your question: ")

        # Query the model
        response = query_model(model, question)
        print(f"Model's response: {response}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
