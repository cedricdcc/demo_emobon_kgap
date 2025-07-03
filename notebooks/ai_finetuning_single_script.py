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
tokenizer = AutoTokenizer.from_pretrained("HuggingFaceTB/SmolLM2-135M")
print(dataset["train"])

if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id
    # does not quite work , hardcoded manx length
target_max_length = len(tokenizer(dataset["train"]["sparql_query"]))
print(target_max_length)
max_length = 1024  # max token length of answer


def preprocess_function(examples, text_column="question", label_column="sparql_query"):
    batch_size = len(examples[text_column])
    inputs = [f"{text_column} : {x} Label : " for x in examples[text_column]]
    targets = [str(x) for x in examples[label_column]]
    model_inputs = tokenizer(inputs)
    labels = tokenizer(targets)
    for i in range(batch_size):
        sample_input_ids = model_inputs["input_ids"][i]
        label_input_ids = labels["input_ids"][i]
        model_inputs["input_ids"][i] = [tokenizer.pad_token_id] * (
            max_length - len(sample_input_ids)
        ) + sample_input_ids
        model_inputs["attention_mask"][i] = [0] * (
            max_length - len(sample_input_ids)
        ) + model_inputs["attention_mask"][i]
        labels["input_ids"][i] = [-100] * (
            max_length - len(label_input_ids)
        ) + label_input_ids
        model_inputs["input_ids"][i] = torch.tensor(
            model_inputs["input_ids"][i][:max_length]
        )
        model_inputs["attention_mask"][i] = torch.tensor(
            model_inputs["attention_mask"][i][:max_length]
        )
        labels["input_ids"][i] = torch.tensor(labels["input_ids"][i][:max_length])
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


model_inputs = preprocess_function(dataset["train"])
print(model_inputs.keys())

ds = dataset
processed_ds = ds.map(
    preprocess_function,
    batched=True,
    num_proc=1,
    remove_columns=ds["train"].column_names,
    load_from_cache_file=False,
    desc="Running tokenizer on dataset",
)
print(processed_ds)


train_ds = processed_ds["train"]
eval_ds = processed_ds["test"]

batch_size = 1

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

model = AutoModelForCausalLM.from_pretrained("bigscience/bloomz-560m")


peft_config = PromptEncoderConfig(
    task_type="CAUSAL_LM", num_virtual_tokens=20, encoder_hidden_size=128
)
model = get_peft_model(model, peft_config)
model.print_trainable_parameters()


lr = 3e-2
num_epochs = 3
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

# Ensure the 'saved_models/' directory exists
save_dir = "saved_models"
current_dir_file = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(current_dir_file, save_dir), exist_ok=True)

# Save the trained model after each epoch
save_path = os.path.join(current_dir_file, save_dir, "trained_model.pt")

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

    # Save the model at the end of training
    torch.save(model.state_dict(), save_path)
    print(f"Model saved to {save_path}")
