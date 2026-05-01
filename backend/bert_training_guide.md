# Fine-Tuning InLegalBERT for Contempt Risk Classification

This notebook provides the exact code needed to fine-tune `InLegalBERT` on your Colab instance and export the model so you can plug it into the NyayaDrishti backend.

## 1. Install Dependencies
```python
!pip install transformers torch datasets scikit-learn
```

## 2. Load the Pre-trained Model and Tokenizer
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# We use InLegalBERT, which is pre-trained on Indian legal texts
model_name = "law-ai/InLegalBERT"
tokenizer = AutoTokenizer.from_pretrained(model_name)

# 3 Classes: Low (0), Medium (1), High (2) Contempt Risk
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=3)
```

## 3. Prepare Your Dataset
You will need to export the `TrainingPair` data from your Django backend.
```python
from datasets import Dataset

# Example of how your data should look (you will export this from your Django DB)
data = [
    {"text": "The Secretary shall personally ensure compliance, failing which coercive action including contempt proceedings will be initiated.", "label": 2}, # High
    {"text": "The respondent is directed to consider the representation within 30 days.", "label": 1}, # Medium
    {"text": "The petition is dismissed. No costs.", "label": 0}, # Low
]

dataset = Dataset.from_list(data)

def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=256)

tokenized_datasets = dataset.map(tokenize_function, batched=True)

# Split into train/test
tokenized_datasets = tokenized_datasets.train_test_split(test_size=0.2)
```

## 4. Train the Model
```python
from transformers import TrainingArguments, Trainer
import numpy as np
from datasets import load_metric

metric = load_metric("accuracy")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)

training_args = TrainingArguments(
    output_dir="./results",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=5,
    weight_decay=0.01,
    evaluation_strategy="epoch",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["test"],
    compute_metrics=compute_metrics,
)

# Start training
trainer.train()
```

## 5. Save and Export
```python
# Save the model and tokenizer
model.save_pretrained("./contempt_classifier_inlegalbert")
tokenizer.save_pretrained("./contempt_classifier_inlegalbert")

# Zip the folder to download it
!zip -r contempt_classifier_inlegalbert.zip ./contempt_classifier_inlegalbert
```

## 6. How to Plug it into the Backend
Once you download the zip file, extract it to `backend/apps/action_plans/models/contempt_classifier_inlegalbert`.
Then, in `backend/apps/action_plans/services/risk_classifier.py`, replace the keyword-based logic with:

```python
from transformers import pipeline

classifier = pipeline("text-classification", model="apps/action_plans/models/contempt_classifier_inlegalbert")

def classify_contempt_risk(text: str) -> str:
    result = classifier(text)[0]
    label = result['label']
    
    if label == "LABEL_2": return "High"
    elif label == "LABEL_1": return "Medium"
    else: return "Low"
```
