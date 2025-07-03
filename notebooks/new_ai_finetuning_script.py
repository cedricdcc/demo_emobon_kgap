import torch
from datasets import load_dataset, DatasetDict
from transformers import (
    T5ForConditionalGeneration,
    T5Tokenizer,
    DataCollatorForSeq2Seq
from transformers.trainer_seq2seq import Seq2SeqTrainer
from transformers.training_args_seq2seq import Seq2SeqTrainingArguments
)
try:
    from peft import PeftModel, PeftConfig, LoraConfig, get_peft_model
except ImportError:
    raise ImportError("The 'peft' library is not installed. Install it using 'pip install peft'.")
import numpy as np
import os
import json
from tqdm import tqdm

# Configuration
MODEL_NAME = "t5-small"
DATA_FILE = "./all_generated_questions.json"
TARGET_MODEL_DIR = "t5_sparql_generator"
MAX_INPUT_LENGTH = 128  # For natural language questions
MAX_TARGET_LENGTH = 256  # For SPARQL queries
BATCH_SIZE = 8
GRAD_ACCUM_STEPS = 4
NUM_EPOCHS = 10
LEARNING_RATE = 3e-4
LORA_R = 8  # LoRA attention dimension
LORA_ALPHA = 32  # Alpha parameter for LoRA scaling

os.makedirs(TARGET_MODEL_DIR, exist_ok=True)
torch.cuda.empty_cache()


# 1. Token Length Analysis --------------------------------
def analyze_token_lengths(dataset, tokenizer):
    """Analyze token lengths to optimize max lengths"""
    questions = dataset["train"]["question"]
    sparqls = dataset["train"]["sparql_query"]

    question_lengths = [len(tokenizer.tokenize(q)) for q in questions]
    sparql_lengths = [len(tokenizer.tokenize(s)) for s in sparqls]

    stats = {
        "questions": {
            "max": int(max(question_lengths)),
            "95th": int(np.percentile(question_lengths, 95)),
            "99th": int(np.percentile(question_lengths, 99)),
        },
        "sparql": {
            "max": int(max(sparql_lengths)),
            "95th": int(np.percentile(sparql_lengths, 95)),
            "99th": int(np.percentile(sparql_lengths, 99)),
        },
    }

    print("\nToken Length Statistics:")
    print(json.dumps(stats, indent=2))

    # Use 99th percentile + buffer as max lengths
    global MAX_INPUT_LENGTH, MAX_TARGET_LENGTH
    MAX_INPUT_LENGTH = min(stats["questions"]["99th"] + 10, 256)
    MAX_TARGET_LENGTH = min(stats["sparql"]["99th"] + 20, 512)

    print(f"Using MAX_INPUT_LENGTH: {MAX_INPUT_LENGTH}")
    print(f"Using MAX_TARGET_LENGTH: {MAX_TARGET_LENGTH}\n")
    return stats


# 2. Data Loading & Filtering ----------------------------
def load_and_filter_data():
    dataset = load_dataset("json", data_files=DATA_FILE)["train"]

    # Filter invalid entries
    dataset = dataset.filter(
        lambda x: not (
            x["question"].startswith("SELECT") or x["sparql_query"].endswith("...")
        )
    )

    # Split dataset
    train_test = dataset.train_test_split(test_size=0.05, seed=42)
    train_val = train_test["train"].train_test_split(test_size=0.1, seed=42)

    return DatasetDict(
        {
            "train": train_val["train"],
            "validation": train_val["test"],
            "test": train_test["test"],
        }
    )


# 3. Tokenization & Preprocessing ------------------------
def preprocess_function(examples):
    """Prepare inputs and targets for T5"""
    inputs = ["translate to SPARQL: " + q for q in examples["question"]]
    targets = [s for s in examples["sparql_query"]]

    model_inputs = tokenizer(
        inputs, max_length=MAX_INPUT_LENGTH, truncation=True, padding="max_length"
    )

    # Setup tokenizer for targets
    with tokenizer.as_target_tokenizer():
        labels = tokenizer(
            targets, max_length=MAX_TARGET_LENGTH, truncation=True, padding="max_length"
        )

    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


# 4. SPARQL Evaluation Metrics ---------------------------
def compute_metrics(eval_preds):
    """Calculate exact match accuracy for SPARQL queries"""
    preds, labels = eval_preds
    if isinstance(preds, tuple):
        preds = preds[0]

    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)

    # Replace -100 in labels as we can't decode them
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

    # Normalize SPARQL for comparison
    def normalize_sparql(query):
        query = query.lower().strip()
import re
        query = re.sub(r"\s+", " ", query)  # Remove extra whitespace
        query = re.sub(
            r"(?<=\W)\s+|\s+(?=\W)", "", query
        )  # Remove space around punctuation
        return query

    correct = 0
    for pred, label in zip(decoded_preds, decoded_labels):
        if normalize_sparql(pred) == normalize_sparql(label):
            correct += 1

    accuracy = correct / len(decoded_labels)
    return {"sparql_accuracy": accuracy}


# 5. Model Setup with LoRA -------------------------------
def setup_model():
    # Load base model
    model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)

    # Configure LoRA
    peft_config = LoraConfig(
        task_type="SEQ_2_SEQ_LM",
        inference_mode=False,
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=0.05,
        target_modules=["q", "v"],  # Apply to query and value layers
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    return model


# Main Execution ----------------------------------------
if __name__ == "__main__":
    # Initialize tokenizer
    tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)

    # Load and analyze data
    dataset = load_and_filter_data()
    token_stats = analyze_token_lengths(dataset, tokenizer)

    # Preprocess dataset
    tokenized_ds = dataset.map(
        preprocess_function,
        batched=True,
        remove_columns=dataset["train"].column_names,
        desc="Tokenizing dataset",
    )

    # Setup model
    model = setup_model()

    # Training arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=TARGET_MODEL_DIR,
        eval_strategy="epoch",
        learning_rate=LEARNING_RATE,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM_STEPS,
        weight_decay=0.01,
        save_total_limit=2,
        num_train_epochs=NUM_EPOCHS,
        predict_with_generate=True,
        generation_max_length=MAX_TARGET_LENGTH,
        fp16=True,
        logging_dir=f"{TARGET_MODEL_DIR}/logs",
        report_to="none",
        load_best_model_at_end=True,
        metric_for_best_model="sparql_accuracy",
        greater_is_better=True,
    )

    # Data collator
    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model, pad_to_multiple_of=8)

    # Initialize Trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_ds["train"],
        eval_dataset=tokenized_ds["validation"],
        data_collator=data_collator,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    # Train model
    trainer.train()

    # Save best model
    trainer.save_model(f"{TARGET_MODEL_DIR}/best")

    # Test inference function
    def generate_sparql(question):
        input_text = "translate to SPARQL: " + question
        inputs = tokenizer(
            input_text,
            return_tensors="pt",
            max_length=MAX_INPUT_LENGTH,
            truncation=True,
        ).to(model.device)

        outputs = model.generate(
            input_ids=inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_length=MAX_TARGET_LENGTH,
            num_beams=3,
            early_stopping=True,
        )
        return tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Test with sample questions
    test_questions = [
        "Who directed Inception?",
        "Which actors appeared in The Dark Knight?",
        "Movies directed by Christopher Nolan",
    ]

    print("\nSPARQL Generation Test:")
    for question in test_questions:
        sparql = generate_sparql(question)
        print(f"Question: {question}")
        print(f"SPARQL: {sparql}\n")

    # Evaluate on test set
    test_results = trainer.evaluate(tokenized_ds["test"])
    print("\nFinal Test Results:")
    print(f"SPARQL Accuracy: {test_results['eval_sparql_accuracy']:.4f}")
    print(f"Loss: {test_results['eval_loss']:.4f}")
