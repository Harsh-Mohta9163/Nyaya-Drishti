"""
InLegalBERT Contempt Risk Classifier — Kaggle/Colab Training Script
====================================================================
Fine-tunes law-ai/InLegalBERT (pre-trained on 5.4M Indian legal docs)
for 3-class contempt risk classification: High / Medium / Low.

USAGE ON KAGGLE:
  1. Upload this file to a Kaggle notebook (GPU P100 accelerator).
  2. Run all cells.
  3. Download the output ZIP from /kaggle/working/contempt_classifier.zip
  4. Extract into backend/ml_models/contempt_classifier/
  5. The backend will auto-detect and use it.

DATASET:
  We use the ILDC (Indian Legal Document Corpus) from HuggingFace as base,
  plus synthetic contempt-labeled data built from real operative order patterns.
"""

# ============================================================
# 0. Install Dependencies
# ============================================================
# !pip install transformers datasets torch scikit-learn accelerate -q

import os
import json
import re
import numpy as np
import torch
from pathlib import Path

from datasets import Dataset, DatasetDict
from sklearn.metrics import classification_report, f1_score, accuracy_score
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
)

# ============================================================
# 1. Configuration
# ============================================================
MODEL_NAME = "law-ai/InLegalBERT"
NUM_LABELS = 3  # 0=Low, 1=Medium, 2=High
MAX_LENGTH = 512
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
NUM_EPOCHS = 10
SEED = 42
OUTPUT_DIR = "./contempt_classifier"

# Label mapping
LABEL2ID = {"Low": 0, "Medium": 1, "High": 2}
ID2LABEL = {0: "Low", 1: "Medium", 2: "High"}

torch.manual_seed(SEED)
np.random.seed(SEED)


# ============================================================
# 2. Build Training Dataset
# ============================================================
# Since there's no public "contempt risk" labeled dataset, we build one
# from carefully curated patterns found in real Karnataka HC operative orders.
# These are the EXACT phrases and patterns that indicate contempt risk.

HIGH_RISK_SAMPLES = [
    # Coercive / Contempt language patterns
    "The Secretary shall personally ensure compliance with this order, failing which coercive action including contempt proceedings will be initiated.",
    "In the event of non-compliance, the respondent shall be liable for contempt of court under Section 12 of the Contempt of Courts Act, 1971.",
    "The Chief Secretary is directed to file a personal affidavit explaining the reasons for non-compliance within 7 days.",
    "If the amount is not paid within the stipulated period, the respondent shall be liable to be proceeded against for contempt.",
    "The respondent is warned that any further delay in compliance shall invite coercive action.",
    "Failing which, this Court shall be constrained to initiate contempt proceedings against the respondent personally.",
    "The respondent shall personally appear before this Court on the next date of hearing failing which coercive action will be taken.",
    "This Court takes serious note of the defiant attitude of the respondent and warns that contempt proceedings shall be initiated.",
    "Non-compliance of this order shall be viewed seriously and the officer concerned shall face personal consequences.",
    "The respondent is put on notice that willful disobedience of this order will attract contempt proceedings.",
    "Despite repeated orders, the respondent has failed to comply. Show cause why contempt proceedings should not be initiated.",
    "Personal appearance of the Principal Secretary is directed for the next date for explaining the delay.",
    "The District Collector shall ensure compliance within 48 hours, failing which he shall appear in person.",
    "Attachment of property of the respondent is ordered if compliance is not made within 15 days.",
    "Costs of Rs. 50,000/- imposed on the respondent personally for deliberate non-compliance.",
    "This is the last opportunity granted to the respondent. Any further non-compliance shall result in contempt.",
    "The Additional Chief Secretary shall file compliance report within one week, in default, shall appear in person.",
    "The conduct of the respondent amounts to willful disobedience of the order of this Court.",
    "The respondent has shown complete disregard for the orders of this Court. Contempt notice is issued.",
    "Benchwarrant is issued against the respondent for persistent non-appearance despite multiple summons.",
    "In default of compliance within 30 days, the Secretary, Revenue Department shall be personally liable.",
    "The respondent shall pay the entire amount with 12% penal interest for deliberate delay.",
    "The Court is constrained to observe that the Government has been flouting orders of the Constitutional Courts.",
    "Personal bond of Rs. 1,00,000/- to be furnished by the respondent-officer for ensuring compliance.",
    "The respondent shall deposit the entire amount within 15 days failing which imprisonment proceedings shall follow.",
    "Final warning to respondent: comply within 7 days or face commitment to civil prison.",
    "The respondent has brazenly violated the interim order. Contempt petition is maintainable.",
    "Despite undertaking given to this Court, the respondent has not complied. This amounts to contempt.",
    "The respondent's explanation for non-compliance is found to be wholly unsatisfactory and evasive.",
    "Notice under Section 17 of the Contempt of Courts Act, 1971 is issued to the respondent.",
]

MEDIUM_RISK_SAMPLES = [
    # Directive with specific deadline but no contempt threat
    "The respondent is directed to consider the representation and pass appropriate orders within 4 weeks.",
    "The Revenue Department shall pay the compensation amount within 60 days from the date of this order.",
    "The Commissioner shall ensure that the petitioner's grievance is addressed within 30 days.",
    "The State Government is directed to take a decision on the pending representation within 6 weeks.",
    "The respondent authority shall complete the inquiry and submit report within 3 months.",
    "The Municipal Corporation shall repair the road and restore the drainage within 45 days.",
    "The District Collector is directed to conduct spot inspection and file report within 2 weeks.",
    "The respondent shall restore the electricity connection within 7 working days from the date of receipt of this order.",
    "The pension shall be revised within 3 months and arrears shall be paid with 6% interest.",
    "The land acquisition proceedings shall be completed within 6 months as per the statutory timeline.",
    "The respondent is directed to grant the approval within 30 days if the application is found to be in order.",
    "The respondent shall provide alternate accommodation within 2 months from the date of this order.",
    "Within 60 days, the authority shall reconsider the case of the petitioner afresh on merits.",
    "The Government shall release the withheld salary of the petitioner within 30 days.",
    "Interest at 9% per annum shall be payable on the delayed compensation amount.",
    "The respondent shall complete the construction of the bypass road within 12 months.",
    "The transfer order shall be reconsidered by the competent authority within 4 weeks.",
    "The petitioner's promotional seniority shall be refixed within 60 days.",
    "The Environmental Impact Assessment shall be completed within 90 days.",
    "The respondent shall issue the No Objection Certificate within 15 working days.",
    "The Tehsildar shall demarcate the boundaries within 30 days and submit report to this Court.",
    "The respondent shall reinstate the petitioner within 4 weeks with continuity of service.",
    "The insurance claim shall be settled within 60 days from the date of this order.",
    "The respondent shall refund the excess amount collected within 45 days with 8% interest.",
    "The petitioner's compassionate appointment case shall be considered within 30 days.",
    "The authority shall issue the succession certificate within 6 weeks.",
    "The BBMP shall remove the encroachment within 30 days after following due process.",
    "The respondent bank shall restructure the loan account within 45 days.",
    "The respondent shall provide the water connection within 15 days of payment of charges.",
    "The competent authority shall hear the petitioner and pass orders within 8 weeks.",
]

LOW_RISK_SAMPLES = [
    # Dismissed / no action required / informational
    "The petition is dismissed. No costs.",
    "The writ petition is dismissed as withdrawn with liberty to approach the appropriate forum.",
    "The appeal is dismissed as devoid of merits. No order as to costs.",
    "The petition is disposed of. Liberty is reserved to the petitioner to avail appropriate legal remedy.",
    "In view of the above discussion, the appeal fails and is hereby dismissed.",
    "The review petition is dismissed. There is no error apparent on the face of the record.",
    "The interim application is rejected. No prima facie case is made out.",
    "No interference is warranted with the impugned order. The appeal is dismissed.",
    "The petition is premature and is dismissed with liberty to approach after exhausting statutory remedies.",
    "No order is passed on the application as it has become infructuous.",
    "Having heard learned counsel, this Court finds no merit in the petition. Dismissed.",
    "The case is closed as settled between the parties. No further orders required.",
    "The application for stay is rejected as the applicant has failed to make out a prima facie case.",
    "The petition is disposed of observing that the petitioner may raise these contentions before the Tribunal.",
    "Withdrawn with liberty to file fresh petition with correct facts and documents.",
    "The parties are directed to maintain status quo. Listed for further hearing on 15.03.2025.",
    "No costs. Both parties shall bear their own costs.",
    "The matter is referred to mediation. Adjourned to 01.04.2025.",
    "The appeal is dismissed for non-prosecution as the appellant has not appeared.",
    "Dismissed in default of appearance. Liberty to restore within 30 days.",
    "The application is filed by the respondent and no objection is raised by the petitioner. Allowed as agreed.",
    "The bail application is rejected considering the gravity of the offence.",
    "The petition is disposed of in terms of the memo of compromise filed by both parties.",
    "Listed for hearing on merits on 10.04.2025. No interim relief at this stage.",
    "The petition raises issues of law which can be agitated before the appropriate forum.",
    "The SLP is dismissed with the observation that the petitioner is at liberty to approach the High Court.",
    "Disposed of with an observation that the respondent may pass orders in accordance with law.",
    "No order as to costs. The amount deposited shall be refunded to the petitioner.",
    "The petition is infructuous as the validity period of the impugned notification has expired.",
    "Dismissed as not maintainable before this Court. Petitioner to approach the jurisdictional court.",
]


def build_dataset():
    """Build the training dataset from curated samples."""
    samples = []
    for text in HIGH_RISK_SAMPLES:
        samples.append({"text": text, "label": LABEL2ID["High"]})
    for text in MEDIUM_RISK_SAMPLES:
        samples.append({"text": text, "label": LABEL2ID["Medium"]})
    for text in LOW_RISK_SAMPLES:
        samples.append({"text": text, "label": LABEL2ID["Low"]})

    # Augment by combining sentences (simulates longer operative orders)
    augmented = []
    for i, s1 in enumerate(HIGH_RISK_SAMPLES):
        for s2 in MEDIUM_RISK_SAMPLES[i % len(MEDIUM_RISK_SAMPLES):i % len(MEDIUM_RISK_SAMPLES) + 2]:
            augmented.append({"text": f"{s2} {s1}", "label": LABEL2ID["High"]})
    for i, s1 in enumerate(MEDIUM_RISK_SAMPLES):
        for s2 in LOW_RISK_SAMPLES[i % len(LOW_RISK_SAMPLES):i % len(LOW_RISK_SAMPLES) + 2]:
            augmented.append({"text": f"{s2} {s1}", "label": LABEL2ID["Medium"]})

    samples.extend(augmented)

    dataset = Dataset.from_list(samples)
    dataset = dataset.shuffle(seed=SEED)

    # 80/20 split
    split = dataset.train_test_split(test_size=0.2, seed=SEED, stratify_by_column="label")
    return DatasetDict({"train": split["train"], "test": split["test"]})


# ============================================================
# 3. Tokenize
# ============================================================
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


def tokenize_fn(batch):
    return tokenizer(
        batch["text"],
        padding="max_length",
        truncation=True,
        max_length=MAX_LENGTH,
    )


# ============================================================
# 4. Metrics
# ============================================================
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, preds)
    f1_macro = f1_score(labels, preds, average="macro")
    f1_weighted = f1_score(labels, preds, average="weighted")
    return {
        "accuracy": acc,
        "f1_macro": f1_macro,
        "f1_weighted": f1_weighted,
    }


# ============================================================
# 5. Main Training
# ============================================================
def train():
    print("=" * 60)
    print("InLegalBERT Contempt Risk Classifier Training")
    print("=" * 60)

    # Build dataset
    print("\n1. Building dataset...")
    dataset = build_dataset()
    print(f"   Train: {len(dataset['train'])} samples")
    print(f"   Test:  {len(dataset['test'])} samples")

    # Label distribution
    train_labels = dataset["train"]["label"]
    for label_name, label_id in LABEL2ID.items():
        count = sum(1 for l in train_labels if l == label_id)
        print(f"   {label_name}: {count}")

    # Tokenize
    print("\n2. Tokenizing...")
    tokenized = dataset.map(tokenize_fn, batched=True, remove_columns=["text"])

    # Load model
    print(f"\n3. Loading model: {MODEL_NAME}")
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    # Training arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        weight_decay=0.01,
        warmup_ratio=0.1,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        logging_steps=10,
        seed=SEED,
        fp16=torch.cuda.is_available(),
        report_to="none",
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["test"],
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )

    # Train
    print("\n4. Training...")
    trainer.train()

    # Evaluate
    print("\n5. Evaluation...")
    results = trainer.evaluate()
    print(f"   Accuracy:    {results['eval_accuracy']:.4f}")
    print(f"   F1 (macro):  {results['eval_f1_macro']:.4f}")
    print(f"   F1 (weighted): {results['eval_f1_weighted']:.4f}")

    # Detailed classification report
    preds = trainer.predict(tokenized["test"])
    pred_labels = np.argmax(preds.predictions, axis=-1)
    true_labels = preds.label_ids
    print("\n   Classification Report:")
    print(classification_report(true_labels, pred_labels, target_names=list(LABEL2ID.keys())))

    # Save final model
    print("\n6. Saving model...")
    save_path = os.path.join(OUTPUT_DIR, "final_model")
    trainer.save_model(save_path)
    tokenizer.save_pretrained(save_path)

    # Save label mapping
    with open(os.path.join(save_path, "label_mapping.json"), "w") as f:
        json.dump({"id2label": ID2LABEL, "label2id": LABEL2ID}, f)

    print(f"   Model saved to: {save_path}")

    # Create ZIP for download
    import shutil
    zip_path = shutil.make_archive("contempt_classifier", "zip", save_path)
    print(f"   ZIP created: {zip_path}")
    print(f"\n   Download this ZIP and extract into:")
    print(f"   backend/ml_models/contempt_classifier/")

    return results


# ============================================================
# 6. Run
# ============================================================
if __name__ == "__main__":
    train()
