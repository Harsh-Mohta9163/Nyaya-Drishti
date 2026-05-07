# ============================================================================
# NyayaDrishti — Kaggle FAST GPU Embedding (SC 2024 ONLY)
# ============================================================================
# Run this on Kaggle with GPU enabled (T4).
# Output: A single parquet file with pre-computed InLegalBERT embeddings
#   1. sc_2024_embeddings.parquet  (Supreme Court 2024 only)
#
# After downloading, run on your local machine:
#   python manage.py import_kaggle_embeddings --path /path/to/downloaded/
# ============================================================================

# !pip install boto3 pymupdf transformers torch pandas pyarrow -q

import os
import io
import json
import tarfile
import numpy as np
import pandas as pd
import torch
import fitz  # PyMuPDF
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from transformers import AutoTokenizer, AutoModel

# ============================================================================
# CONFIG
# ============================================================================
SC_YEARS = [2024]  # ONLY 2024 (Very Fast!)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")

# ============================================================================
# MODEL SETUP
# ============================================================================
print("Loading InLegalBERT...")
tokenizer = AutoTokenizer.from_pretrained("law-ai/InLegalBERT")
model = AutoModel.from_pretrained("law-ai/InLegalBERT").to(DEVICE)
model.eval()

def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def embed_texts(texts, batch_size=64):
    """Embed texts using InLegalBERT on GPU. Returns numpy array of shape (N, 768)."""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        encoded = tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors='pt').to(DEVICE)
        with torch.no_grad():
            out = model(**encoded)
        embs = mean_pooling(out, encoded['attention_mask'])
        embs = torch.nn.functional.normalize(embs, p=2, dim=1)
        all_embeddings.append(embs.cpu().numpy())
        if (i // batch_size) % 10 == 0:
            print(f"  Embedded {i+len(batch)}/{len(texts)} texts...")
    return np.vstack(all_embeddings)

def chunk_text(text, max_tokens=512, overlap=128):
    """Split text into overlapping token chunks."""
    tokens = tokenizer.encode(text, add_special_tokens=False)
    if len(tokens) <= max_tokens:
        return [text]
    chunks = []
    stride = max_tokens - overlap
    for i in range(0, len(tokens), stride):
        chunk_tokens = tokens[i:i + max_tokens]
        chunks.append(tokenizer.decode(chunk_tokens))
    return chunks

# ============================================================================
# RULE-BASED CLASSIFICATION
# ============================================================================
CASE_TYPE_MAP = {
    "WP": "constitutional", "W.P": "constitutional", "PIL": "constitutional",
    "CRL": "criminal_law", "CRIMINAL": "criminal_law", "BAIL": "criminal_law", "SLP(CRL)": "criminal_law",
    "MFA": "motor_vehicles", "M.F.A": "motor_vehicles", "MAC": "motor_vehicles",
    "RFA": "property_law", "R.F.A": "property_law", "RSA": "property_law", "CIVIL APPEAL": "property_law",
    "TAX": "tax_law", "STA": "tax_law", "CESTAT": "tax_law", "INCOME TAX": "tax_law", "GST": "tax_law", "CUSTOMS": "tax_law",
    "COM": "commercial", "COMPANY": "commercial", "ARB": "commercial", "ARBITRATION": "commercial", "INSOLVENCY": "commercial", "IBC": "commercial",
    "MAT": "family_law", "FC": "family_law", "DIVORCE": "family_law", "GUARDIAN": "family_law", "MATRIMONIAL": "family_law",
    "WA": "service_law", "W.A": "service_law", "SLP": "service_law", "SERVICE": "service_law",
    "LAB": "labour_law", "LCA": "labour_law", "INDUSTRIAL": "labour_law", "WORKMEN": "labour_law",
    "WRIT PETITION (CIVIL)": "constitutional", "WRIT PETITION (CRIMINAL)": "criminal_law",
}

def classify_title(title):
    t = str(title).upper()
    for key in sorted(CASE_TYPE_MAP.keys(), key=len, reverse=True):
        if key in t:
            return CASE_TYPE_MAP[key]
    return "civil_procedure"

# ============================================================================
# S3 CLIENT & PROCESS
# ============================================================================
s3 = boto3.client('s3', region_name='ap-south-1', config=Config(signature_version=UNSIGNED))

sc_chunks = []

for year in SC_YEARS:
    print(f"\n--- SC {year} ---")
    parquet_key = f"metadata/parquet/year={year}/metadata.parquet"
    try:
        obj = s3.get_object(Bucket='indian-supreme-court-judgments', Key=parquet_key)
        df = pd.read_parquet(io.BytesIO(obj['Body'].read()))
        print(f"  Metadata: {len(df)} cases")
    except Exception as e:
        print(f"  Metadata not found: {e}"); continue
    
    tar_key = f"data/tar/year={year}/english/english.tar"
    texts_by_path = {}
    try:
        print(f"  Downloading TAR: {tar_key}")
        obj = s3.get_object(Bucket='indian-supreme-court-judgments', Key=tar_key)
        tar_bytes = io.BytesIO(obj['Body'].read())
        with tarfile.open(fileobj=tar_bytes, mode='r') as tar:
            for member in tar.getmembers():
                if member.name.endswith('.pdf'):
                    f = tar.extractfile(member)
                    if f:
                        try:
                            doc = fitz.open(stream=f.read(), filetype="pdf")
                            text = "\n".join(page.get_text("text") for page in doc)
                            texts_by_path[member.name.replace("_EN.pdf", "")] = text.strip()
                        except: pass
        print(f"  Extracted text from {len(texts_by_path)} PDFs")
    except Exception as e:
        print(f"  TAR download failed: {e}"); continue
    
    for _, row in df.iterrows():
        path, text = str(row.get('path', '')), texts_by_path.get(str(row.get('path', '')), '')
        if len(text) < 200: continue
        
        case_id = str(row.get('cnr', row.get('case_id', '')))
        area = classify_title(str(row.get('title', '')))
        
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            sc_chunks.append({
                'chunk_id': f"{case_id}_chunk_{i}",
                'case_id': case_id,
                'court': 'Supreme Court of India',
                'area_of_law': area,
                'disposal_nature': str(row.get('disposal_nature', '')),
                'decision_date': str(row.get('decision_date', '')),
                'petitioner': str(row.get('petitioner', ''))[:100],
                'respondent': str(row.get('respondent', ''))[:100],
                'title': str(row.get('title', ''))[:200],
                'chunk_index': i,
                'text': chunk,
            })
            
print(f"\nEmbedding {len(sc_chunks)} chunks on GPU...")
if sc_chunks:
    sc_embeddings = embed_texts([c['text'] for c in sc_chunks], batch_size=64)
    sc_df = pd.DataFrame(sc_chunks)
    sc_df['embedding'] = list(sc_embeddings.astype(np.float16))
    # MUST Save as sc_embeddings.parquet so the importer recognizes it
    sc_df.to_parquet('/kaggle/working/sc_embeddings.parquet')
    print(f"Saved sc_embeddings.parquet ({len(sc_df)} chunks)")
