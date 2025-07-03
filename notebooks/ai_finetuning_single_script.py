import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    default_data_collator,
    get_linear_schedule_with_warmup,
)
from peft import PromptEncoderConfig, get_peft_model
from torch.utils.data import DataLoader
from tqdm import tqdm
import json
import os
import numpy as np
import re

# Set environment variables first
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Prevent tokenizer deadlocks


# Step 1: Optimized dataset loading
def load_and_filter_data(file_path):
    dataset = load_dataset("json", data_files=file_path)
    df = dataset["train"].to_pandas()

    # More efficient filtering using vectorized operations
    mask = ~(
        df["question"].str.startswith("SELECT") | df["sparql_query"].str.endswith("...")
    )
    df = df[mask]

    # Split dataset
    train_size = int(0.95 * len(df))
    train_df = df.iloc[:train_size]
    eval_df = df.iloc[train_size:]

    # Convert back to dataset format
    return {
        "train": dataset["train"].from_pandas(train_df),
        "test": dataset["train"].from_pandas(eval_df),
    }


data_file = "./all_generated_questions.json"
dataset = load_and_filter_data(data_file)

print(f"\nTotal train rows: {len(dataset['train'])}")
print(f"Total test rows: {len(dataset['test'])}")

# Initialize tokenizer with padding
tokenizer = AutoTokenizer.from_pretrained("bigscience/bloomz-560m")
tokenizer.pad_token = tokenizer.eos_token  # Properly set padding token


# Calculate optimal max_length from data
def calculate_max_lengths(data):
    question_lengths = [len(tokenizer.tokenize(q)) for q in data["train"]["question"]]
    sparql_lengths = [len(tokenizer.tokenize(s)) for s in data["train"]["sparql_query"]]

    # Use 95th percentile + buffer
    input_max = int(np.percentile(question_lengths, 95)) + 20
    target_max = int(np.percentile(sparql_lengths, 95)) + 30

    return min(input_max, 512), min(target_max, 512)  # Cap at 512


max_input_length, max_target_length = calculate_max_lengths(dataset)
print(
    f"Using max_input_length: {max_input_length}, max_target_length: {max_target_length}"
)


# Optimized preprocessing with batched tokenization
def preprocess_function(examples):
    inputs = [f"Question: {q} SPARQL:" for q in examples["question"]]
    targets = [str(s) for s in examples["sparql_query"]]

    # Tokenize inputs and targets in batches
    model_inputs = tokenizer(
        inputs,
        max_length=max_input_length,
        padding="max_length",
        truncation=True,
        return_tensors="pt",
    )

    with tokenizer.as_target_tokenizer():
        labels = tokenizer(
            targets,
            max_length=max_target_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

    # Replace padding token with -100 for loss calculation
    labels = labels["input_ids"]
    labels[labels == tokenizer.pad_token_id] = -100

    return {
        "input_ids": model_inputs["input_ids"],
        "attention_mask": model_inputs["attention_mask"],
        "labels": labels,
    }


# Apply preprocessing
processed_ds = {
    "train": dataset["train"].map(
        preprocess_function,
        batched=True,
        batch_size=32,  # Process in batches for speed
        remove_columns=dataset["train"].column_names,
        desc="Tokenizing dataset",
    ),
    "test": dataset["test"].map(
        preprocess_function,
        batched=True,
        batch_size=32,
        remove_columns=dataset["test"].column_names,
        desc="Tokenizing dataset",
    ),
}

# Use larger batch size with gradient accumulation
batch_size = 4
grad_accum_steps = 4

train_dataloader = DataLoader(
    processed_ds["train"],
    shuffle=True,
    collate_fn=default_data_collator,
    batch_size=batch_size,
    pin_memory=True,
)
eval_dataloader = DataLoader(
    processed_ds["test"],
    collate_fn=default_data_collator,
    batch_size=batch_size,
    pin_memory=True,
)

# Model initialization with cache optimization
model = AutoModelForCausalLM.from_pretrained(
    "bigscience/bloomz-560m",
    device_map="auto",  # Let HF handle device placement
    torch_dtype=torch.float16,  # Use mixed precision
)

# PEFT configuration with optimized settings
peft_config = PromptEncoderConfig(
    task_type="CAUSAL_LM",
    num_virtual_tokens=32,  # Increased for better performance
    encoder_hidden_size=192,
    encoder_dropout=0.1,
)
model = get_peft_model(model, peft_config)
model.print_trainable_parameters()

# Training setup with optimized parameters
lr = 1e-3  # Lower learning rate for stability
num_epochs = 5
total_steps = len(train_dataloader) * num_epochs // grad_accum_steps

optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
lr_scheduler = get_linear_schedule_with_warmup(
    optimizer=optimizer,
    num_warmup_steps=int(0.1 * total_steps),
    num_training_steps=total_steps,
)

# Memory optimization
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

# Directory setup
save_dir = "saved_models"
os.makedirs(save_dir, exist_ok=True)

# Training loop with gradient accumulation
for epoch in range(num_epochs):
    model.train()
    total_loss = 0
    optimizer.zero_grad()

    for step, batch in enumerate(tqdm(train_dataloader, desc=f"Epoch {epoch+1}")):
        batch = {k: v.to(device) for k, v in batch.items()}
        outputs = model(**batch)
        loss = outputs.loss / grad_accum_steps
        loss.backward()
        total_loss += loss.item()

        if (step + 1) % grad_accum_steps == 0:
            optimizer.step()
            lr_scheduler.step()
            optimizer.zero_grad()

    # Validation
    model.eval()
    eval_loss = 0
    for batch in tqdm(eval_dataloader, desc="Evaluating"):
        batch = {k: v.to(device) for k, v in batch.items()}
        with torch.no_grad():
            outputs = model(**batch)
        eval_loss += outputs.loss.item()

    # Calculate metrics
    avg_train_loss = total_loss / len(train_dataloader)
    avg_eval_loss = eval_loss / len(eval_dataloader)

    print(
        f"Epoch {epoch+1}/{num_epochs} | "
        f"Train Loss: {avg_train_loss:.4f} | "
        f"Eval Loss: {avg_eval_loss:.4f}"
    )

    # Save model checkpoint
    checkpoint_path = os.path.join(save_dir, f"model_epoch_{epoch+1}.pt")
    torch.save(model.state_dict(), checkpoint_path)
    print(f"Model saved to {checkpoint_path}")
