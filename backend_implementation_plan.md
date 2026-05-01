# NyayaDrishti — Backend Implementation Plan

> Person B's detailed guide. Django 5 + DRF + NVIDIA NIM + Hybrid RAG + InLegalBERT + LoRA + IndicTrans2

---

## 1. NVIDIA NIM Setup (Your API Key)

All three services use the same `nvapi-` key, OpenAI-compatible format:

```python
# config/nvidia_client.py
from openai import OpenAI

nim_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=settings.NVIDIA_API_KEY  # nvapi-xxxxx
)

# LLM Extraction
response = nim_client.chat.completions.create(
    model="meta/llama-3.3-70b-instruct",
    messages=[{"role": "system", "content": LEGAL_SYSTEM_PROMPT}, ...],
    response_format={"type": "json_object"},
    temperature=0.1
)

# Embeddings
embed_resp = nim_client.embeddings.create(
    model="nvidia/nv-embedqa-e5-v5",
    input=["chunk text here"]
)

# Reranking (uses requests, not openai SDK)
import requests
rerank_resp = requests.post(
    "https://integrate.api.nvidia.com/v1/rerank",
    headers={"Authorization": f"Bearer {settings.NVIDIA_API_KEY}"},
    json={
        "model": "nvidia/llama-3.2-nv-rerankqa-1b-v2",
        "query": "compliance deadline",
        "documents": ["chunk1", "chunk2", ...],
        "top_n": 5
    }
)
```

---

## 2. Database Models

```python
# apps/accounts/models.py
class User(AbstractUser):
    ROLES = [('reviewer','Reviewer'), ('dept_officer','Dept Officer'),
             ('dept_head','Dept Head'), ('legal_advisor','Legal Advisor')]
    role = models.CharField(max_length=20, choices=ROLES)
    department = models.CharField(max_length=200, blank=True)
    language = models.CharField(max_length=5, default='en')  # en / kn

# apps/cases/models.py
class Case(models.Model):
    case_number = models.CharField(max_length=100, unique=True)
    court = models.CharField(max_length=200)
    bench = models.CharField(max_length=300, blank=True)
    petitioner = models.TextField()
    respondent = models.TextField()
    case_type = models.CharField(max_length=50)
    judgment_date = models.DateField()
    pdf_file = models.FileField(upload_to='judgments/')
    status = models.CharField(max_length=30)
    ocr_confidence = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ExtractedData(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE)
    header_data = models.JSONField()
    operative_order = models.TextField()
    court_directions = models.JSONField()
    order_type = models.CharField(max_length=50)
    entities = models.JSONField()
    extraction_confidence = models.FloatField()
    source_references = models.JSONField()

# apps/action_plans/models.py
class ActionPlan(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE)
    recommendation = models.CharField(max_length=20)
    recommendation_reasoning = models.TextField()
    compliance_actions = models.JSONField()
    legal_deadline = models.DateField()
    internal_deadline = models.DateField()
    responsible_departments = models.JSONField()
    ccms_stage = models.CharField(max_length=100)
    contempt_risk = models.CharField(max_length=10)
    similar_cases = models.JSONField(default=list)
    verification_status = models.CharField(max_length=20, default='pending')

# apps/reviews/models.py
class ReviewLog(models.Model):
    action_plan = models.ForeignKey(ActionPlan, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    review_level = models.CharField(max_length=20)
    action = models.CharField(max_length=20)
    changes = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class TrainingPair(models.Model):
    """Stores AI output vs human correction for LoRA training"""
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=100)
    ai_output = models.TextField()
    human_correction = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    used_for_training = models.BooleanField(default=False)
```

---

## 3. Hybrid RAG Pipeline (Detail)

```python
# apps/action_plans/services/rag_engine.py
from rank_bm25 import BM25Okapi
import chromadb

class HybridRAGEngine:
    def __init__(self):
        self.chroma = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma.get_or_create_collection("karnataka_hc")
        self.bm25_corpus = []  # loaded from DB
        self.bm25_index = None

    def build_index(self, documents):
        """Build both BM25 + vector indices"""
        # 1. BM25 sparse index
        tokenized = [doc.split() for doc in documents]
        self.bm25_index = BM25Okapi(tokenized)

        # 2. Dense embeddings via NVIDIA NIM
        for i, doc in enumerate(documents):
            embedding = nim_client.embeddings.create(
                model="nvidia/nv-embedqa-e5-v5", input=[doc]
            ).data[0].embedding
            self.collection.add(ids=[f"doc_{i}"], embeddings=[embedding],
                               documents=[doc], metadatas=[{"idx": i}])

    def query(self, query_text, top_k=5):
        # Step 1: BM25 sparse search → top 50
        bm25_scores = self.bm25_index.get_scores(query_text.split())
        bm25_top50 = sorted(range(len(bm25_scores)),
                            key=lambda i: bm25_scores[i], reverse=True)[:50]

        # Step 2: Dense vector search → top 50
        query_emb = nim_client.embeddings.create(
            model="nvidia/nv-embedqa-e5-v5", input=[query_text]
        ).data[0].embedding
        dense_results = self.collection.query(
            query_embeddings=[query_emb], n_results=50)

        # Step 3: Reciprocal Rank Fusion
        candidates = self._rrf_merge(bm25_top50, dense_results, k=60)

        # Step 4: NVIDIA Reranker (cross-encoder)
        candidate_texts = [self.bm25_corpus[i] for i in candidates[:20]]
        rerank_resp = requests.post(
            "https://integrate.api.nvidia.com/v1/rerank",
            headers={"Authorization": f"Bearer {settings.NVIDIA_API_KEY}"},
            json={
                "model": "nvidia/llama-3.2-nv-rerankqa-1b-v2",
                "query": query_text,
                "documents": candidate_texts,
                "top_n": top_k
            }
        )
        return rerank_resp.json()["results"]

    def _rrf_merge(self, bm25_ids, dense_results, k=60):
        """Reciprocal Rank Fusion"""
        scores = {}
        for rank, doc_id in enumerate(bm25_ids):
            scores[doc_id] = scores.get(doc_id, 0) + 1/(k + rank + 1)
        for rank, doc_id in enumerate(dense_results):
            scores[doc_id] = scores.get(doc_id, 0) + 1/(k + rank + 1)
        return sorted(scores, key=scores.get, reverse=True)
```

### Chunking Strategy (Legal-Aware)
```python
# Structure-aware chunking for legal documents
def chunk_judgment(sections):
    chunks = []
    for section_name, text in sections.items():
        if section_name == "operative_order":
            # Small chunks (200 tokens) for precise directive matching
            chunks += split_by_directives(text, max_tokens=200)
        elif section_name == "header":
            # Single chunk with full metadata
            chunks.append({"text": text, "type": "header", "tokens": len(text.split())})
        else:
            # Medium chunks (500 tokens) for context sections
            chunks += split_by_paragraphs(text, max_tokens=500)
    return chunks
```

---

## 4. InLegalBERT Contempt Classifier

### Training Script (Colab)
```python
# ml/bert_trainer.py — Run on Google Colab with T4 GPU
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset

LABELS = {"low": 0, "medium": 1, "high": 2}

tokenizer = AutoTokenizer.from_pretrained("law-ai/InLegalBERT")
model = AutoModelForSequenceClassification.from_pretrained(
    "law-ai/InLegalBERT", num_labels=3
)

# Load labeled contempt directive phrases
# Format: {"text": "shall comply failing which contempt...", "label": 2}
train_data = Dataset.from_json("data/training/contempt_labels.jsonl")

def tokenize(examples):
    return tokenizer(examples["text"], padding="max_length",
                     truncation=True, max_length=256)

training_args = TrainingArguments(
    output_dir="./results", num_train_epochs=5,
    per_device_train_batch_size=16, learning_rate=5e-5,
    eval_strategy="epoch", save_strategy="epoch",
    load_best_model_at_end=True
)

trainer = Trainer(model=model, args=training_args,
                  train_dataset=train_data.map(tokenize, batched=True))
trainer.train()
model.save_pretrained("ml/models/contempt_classifier")
```

### Inference in Django (CPU)
```python
# apps/action_plans/services/risk_classifier.py
from transformers import pipeline

classifier = pipeline("text-classification",
    model="ml/models/contempt_classifier",
    tokenizer="law-ai/InLegalBERT")

def classify_contempt_risk(directive_text: str) -> str:
    result = classifier(directive_text[:512])[0]
    return {"LABEL_0": "Low", "LABEL_1": "Medium", "LABEL_2": "High"}[result["label"]]
```

---

## 5. LoRA Continuous Learning

```python
# ml/lora_trainer.py — Run on Colab periodically
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load base model (small, e.g., Llama 3.2 3B for fine-tuning)
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-3B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-3B-Instruct")

lora_config = LoraConfig(
    r=8, lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05, task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)

# Load training pairs exported from Django TrainingPair model
# Format: {"prompt": "Extract...", "completion": "corrected output"}
training_data = load_training_pairs_from_export()

trainer = SFTTrainer(
    model=model, tokenizer=tokenizer,
    train_dataset=training_data,
    args=SFTConfig(output_dir="./lora_adapters", num_train_epochs=3,
                   per_device_train_batch_size=4, learning_rate=2e-5)
)
trainer.train()
model.save_pretrained("ml/models/lora_adapter_v1")
```

### Export Training Data Endpoint
```python
# apps/reviews/views.py
class ExportTrainingDataView(APIView):
    def get(self, request):
        pairs = TrainingPair.objects.filter(used_for_training=False)
        data = [{"prompt": p.ai_output, "completion": p.human_correction}
                for p in pairs]
        pairs.update(used_for_training=True)
        return Response(data)
```

---

## 6. IndicTrans2 Translation

```python
# apps/translation/services/translator.py
from IndicTransToolkit import IndicProcessor
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

class KannadaTranslator:
    def __init__(self):
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            "ai4bharat/indictrans2-en-indic-dist-200M", trust_remote_code=True)
        self.tokenizer = AutoTokenizer.from_pretrained(
            "ai4bharat/indictrans2-en-indic-dist-200M", trust_remote_code=True)
        self.processor = IndicProcessor(inference=True)

    def translate(self, text: str, src="eng_Latn", tgt="kan_Knda") -> str:
        batch = self.processor.preprocess_batch([text], src_lang=src, tgt_lang=tgt)
        inputs = self.tokenizer(batch, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_length=256)
        result = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        return self.processor.postprocess_batch(result, lang=tgt)[0]
```

---

## 7. Rules Engine

```python
# apps/action_plans/services/rules_engine.py
from datetime import timedelta

LIMITATION_PERIODS = {
    "SLP_to_SC": {"days": 90, "basis": "Article 136, Constitution + Article 116, Limitation Act"},
    "LPA": {"days": 30, "basis": "Section 5, Karnataka HC Act + Clause 15, Letters Patent"},
    "Review_Petition": {"days": 30, "basis": "Order 47 Rule 1 CPC"},
    "Writ_Appeal": {"days": 30, "basis": "Chapter VII, Karnataka HC Rules"},
    "Compliance_Default": {"days": 30, "basis": "General administrative deadline"},
}

def compute_deadlines(judgment_date, order_type, appeal_type=None):
    result = {"legal_deadline": None, "internal_deadline": None, "basis": ""}
    period = LIMITATION_PERIODS.get(appeal_type or "Compliance_Default")
    result["legal_deadline"] = judgment_date + timedelta(days=period["days"])
    result["internal_deadline"] = judgment_date + timedelta(days=max(7, period["days"] - 14))
    result["basis"] = period["basis"]
    return result
```

---

## 8. API Endpoints Summary

| Method | Endpoint | Handler |
|--------|---------|---------|
| POST | `/api/auth/register/` | Register with role |
| POST | `/api/auth/login/` | JWT tokens |
| POST | `/api/auth/refresh/` | Refresh token |
| GET | `/api/auth/me/` | Current user |
| GET | `/api/cases/` | List (paginated, filtered) |
| POST | `/api/cases/` | Upload PDF |
| GET | `/api/cases/{id}/` | Detail + extracted + plan |
| POST | `/api/cases/{id}/extract/` | Trigger extraction |
| POST | `/api/cases/{id}/action-plan/generate/` | Trigger plan gen |
| GET | `/api/reviews/pending/` | Pending reviews |
| POST | `/api/cases/{id}/review/` | Submit review |
| GET | `/api/cases/{id}/review-history/` | Audit trail |
| GET | `/api/dashboard/stats/` | Summary stats |
| GET | `/api/dashboard/deadlines/` | Upcoming deadlines |
| GET | `/api/dashboard/high-risk/` | Contempt risk cases |
| POST | `/api/translate/` | IndicTrans2 translation |
| GET | `/api/reviews/export-training/` | Export LoRA pairs |

---

## 9. Datasets Download Commands

```bash
# 1. Karnataka HC Judgments (AWS Open Data — free, no account)
pip install awscli
aws s3 ls s3://indian-high-court-judgments/ --no-sign-request
aws s3 sync s3://indian-high-court-judgments/karnataka/ ./data/judgments/ --no-sign-request

# 2. ILDC Dataset (HuggingFace — for BERT training supplementary data)
python -c "from datasets import load_dataset; ds = load_dataset('ilab/ildc'); ds.save_to_disk('./data/ildc')"

# 3. Indian Kanoon (for specific contempt cases)
# Manual search: https://indiankanoon.org/search/?formInput=contempt+Karnataka
# Download relevant PDFs for labeling
```

---

## 10. requirements.txt

```
django>=5.0
djangorestframework
djangorestframework-simplejwt
django-cors-headers
psycopg2-binary
gunicorn
whitenoise

# PDF
PyMuPDF
pytesseract
Pillow

# AI/ML
openai              # NVIDIA NIM client (OpenAI-compatible)
chromadb
rank-bm25
sentence-transformers
transformers
torch
peft
trl
datasets

# Translation
IndicTransToolkit
sentencepiece

# Utils
python-dotenv
requests
```

---

## 11. Deployment (Render)

```yaml
# render.yaml
services:
  - type: web
    name: nyaya-drishti-api
    runtime: python
    buildCommand: "cd backend && pip install -r requirements.txt"
    startCommand: "cd backend && gunicorn config.wsgi --bind 0.0.0.0:$PORT"
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: NVIDIA_API_KEY
        sync: false
      - key: DJANGO_SECRET_KEY
        sync: false
      - key: DJANGO_ALLOWED_HOSTS
        sync: false
```
