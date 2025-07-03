import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    default_data_collator,
    get_linear_schedule_with_warmup,
)
from peft import PeftModel, PeftConfig, PromptEncoderConfig, get_peft_model
from torch.utils.data import DataLoader
from tqdm import tqdm
import json
import os

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"


# Step 1: Load the dataset
def load_and_filter_data(file_path):
    dataset = load_dataset("json", data_files=file_path)
    df = dataset["train"].to_pandas()

    # Filter rows where 'question' starts with 'SELECT'
    filtered_question = df[df["question"].str.startswith("{")]

    # Filter rows where 'sparql_select' ends with '...'
    filtered_sparql = df[df["sparql_query"].str.endswith("...")]

    # Exclude the filtered rows
    df = df[~df["question"].str.startswith("SELECT")]
    df = df[~df["sparql_query"].str.endswith("...")]

    # Split the dataset into train and eval subsets
    train_size = int(0.95 * len(df))
    train_df = df.iloc[:train_size]
    eval_df = df.iloc[train_size:]

    # Convert back to dataset format
    dataset["train"] = dataset["train"].from_pandas(train_df)
    dataset["test"] = dataset["train"].from_pandas(eval_df)

    # Print dataset sizes
    print(f"\nTotal number of rows after filtering: {len(df)}")
    print(f"Train subset size: {len(dataset['train'])}")
    print(f"Eval subset size: {len(dataset['test'])}")
    return dataset


data_file = "./all_generated_questions.json"
dataset = load_and_filter_data(data_file)

# preprocessing data
tokenizer = AutoTokenizer.from_pretrained("bigscience/bloomz-560m")

if tokenizer.pad_token_id is None:
    tokenizer.pad_token = tokenizer.eos_token

max_length = 512  # Reduce to avoid OOM
target_max_length = 128  # Separate max length for targets


def preprocess_function(examples):
    inputs = [f"question: {q} Label:" for q in examples["question"]]
    targets = [str(s) for s in examples["sparql_query"]]

    model_inputs = tokenizer(
        inputs, max_length=max_length, truncation=True, padding="max_length"
    )
    labels = tokenizer(
        targets, max_length=target_max_length, truncation=True, padding="max_length"
    )

    # Mask padding tokens in labels
    labels["input_ids"] = [
        [(token if token != tokenizer.pad_token_id else -100) for token in label]
        for label in labels["input_ids"]
    ]
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


model_inputs = preprocess_function(dataset["train"])
print(model_inputs.keys())

ds = dataset
processed_ds = ds.map(
    preprocess_function,
    batched=True,
    num_proc=4,
    remove_columns=ds["train"].column_names,
    load_from_cache_file=False,
    desc="Running tokenizer on dataset",
)
print(processed_ds)


train_ds = processed_ds["train"]
eval_ds = processed_ds["test"]

batch_size = 8  # Adjust batch size as needed

train_dataloader = DataLoader(
    train_ds,
    shuffle=True,
    collate_fn=default_data_collator,
    batch_size=batch_size,
    pin_memory=True,
)
eval_dataloader = DataLoader(
    eval_ds, collate_fn=default_data_collator, batch_size=batch_size, pin_memory=True
)

model = AutoModelForCausalLM.from_pretrained(
    "bigscience/bloomz-560m",
    torch_dtype=torch.float16,  # Use float16 to reduce memory
    device_map="auto",  # Automatically allocate to available GPUs
)


peft_config = PromptEncoderConfig(
    task_type="CAUSAL_LM", num_virtual_tokens=20, encoder_hidden_size=128
)
model = get_peft_model(model, peft_config)
model.print_trainable_parameters()


lr = 3e-2
num_epochs = 50
torch.cuda.empty_cache()
torch.cuda.ipc_collect()
optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
lr_scheduler = get_linear_schedule_with_warmup(
    optimizer=optimizer,
    num_warmup_steps=0,
    num_training_steps=(len(train_dataloader) * num_epochs),
)


def check_cuda():
    if torch.cuda.is_available():
        print("CUDA is available!")
        print(f"Number of GPUs available: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
    else:
        print("CUDA is not available. Only CPU is available.")


check_cuda()
device = "cuda"
model = model.to(device)

for epoch in range(num_epochs):
    model.train()
    total_loss = 0
    for step, batch in enumerate(tqdm(train_dataloader)):
        batch = {k: v.to(device) for k, v in batch.items()}
        outputs = model(**batch)
        loss = outputs.loss
        total_loss += loss.detach().float()
        loss.backward()
        optimizer.step()
        lr_scheduler.step()
        optimizer.zero_grad()

    model.eval()
    eval_loss = 0
    eval_preds = []
    for step, batch in enumerate(tqdm(eval_dataloader)):
        batch = {k: v.to(device) for k, v in batch.items()}
        with torch.no_grad():
            outputs = model(**batch)
        loss = outputs.loss
        eval_loss += loss.detach().float()
        eval_preds.extend(
            tokenizer.batch_decode(
                torch.argmax(outputs.logits, -1).detach().cpu().numpy(),
                skip_special_tokens=True,
            )
        )

    eval_epoch_loss = eval_loss / len(eval_dataloader)
    eval_ppl = torch.exp(eval_epoch_loss)
    train_epoch_loss = total_loss / len(train_dataloader)
    train_ppl = torch.exp(train_epoch_loss)
    print(f"{epoch=}: {train_ppl=} {train_epoch_loss=} {eval_ppl=} {eval_epoch_loss=}")
