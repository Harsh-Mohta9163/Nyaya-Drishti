# ============================================================================
# NyayaDrishti — Kaggle GPU Embedding Pipeline
# ============================================================================
# Run this on Kaggle with GPU enabled (T4).
# Output: Two parquet files with pre-computed InLegalBERT embeddings
#   1. sc_embeddings.parquet  (20 years of Supreme Court)
#   2. hc_embeddings.parquet  (10 years of Karnataka HC Division Bench)
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
SC_YEARS = list(range(2019, 2025))   # 6 years: 2019-2024 (~4,500 cases, ~30 min on GPU)
HC_YEARS = list(range(2020, 2025))   # 5 years: 2020-2024 (Division Bench only)
HC_COURT_CODE = "29_3"               # Karnataka

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
        if (i // batch_size) % 50 == 0:
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
# RULE-BASED CLASSIFICATION (matches local classify_parquet.py exactly)
# ============================================================================
CASE_TYPE_MAP = {
    # Constitutional & Civil Rights
    "WP": "constitutional",
    "W.P": "constitutional",
    "PIL": "constitutional",
    # Criminal
    "CRL": "criminal_law",
    "CRIMINAL": "criminal_law",
    "BAIL": "criminal_law",
    "SLP(CRL)": "criminal_law",
    # Motor Vehicles & Torts
    "MFA": "motor_vehicles",
    "M.F.A": "motor_vehicles",
    "MAC": "motor_vehicles",
    # Property & Civil
    "RFA": "property_law",
    "R.F.A": "property_law",
    "RSA": "property_law",
    "CIVIL APPEAL": "property_law",
    # Tax & Finance
    "TAX": "tax_law",
    "STA": "tax_law",
    "CESTAT": "tax_law",
    "INCOME TAX": "tax_law",
    "GST": "tax_law",
    "CUSTOMS": "tax_law",
    # Commercial & Corporate
    "COM": "commercial",
    "COMPANY": "commercial",
    "ARB": "commercial",
    "ARBITRATION": "commercial",
    "INSOLVENCY": "commercial",
    "IBC": "commercial",
    # Family & Matrimonial
    "MAT": "family_law",
    "FC": "family_law",
    "DIVORCE": "family_law",
    "GUARDIAN": "family_law",
    "MATRIMONIAL": "family_law",
    # Service & Employment
    "WA": "service_law",
    "W.A": "service_law",
    "SLP": "service_law",
    "SERVICE": "service_law",
    # Labour
    "LAB": "labour_law",
    "LCA": "labour_law",
    "INDUSTRIAL": "labour_law",
    "WORKMEN": "labour_law",
    # Constitutional (SC specific)
    "WRIT PETITION (CIVIL)": "constitutional",
    "WRIT PETITION (CRIMINAL)": "criminal_law",
}

def classify_title(title):
    t = str(title).upper()
    # Check longer phrases first to avoid false matches
    for key in sorted(CASE_TYPE_MAP.keys(), key=len, reverse=True):
        if key in t:
            return CASE_TYPE_MAP[key]
    return "civil_procedure"  # Default fallback

# ============================================================================
# S3 CLIENT
# ============================================================================
s3 = boto3.client('s3', region_name='ap-south-1', config=Config(signature_version=UNSIGNED))

# ============================================================================
# PART 1: SUPREME COURT (20 YEARS)
# ============================================================================
print("\n" + "="*60)
print("PART 1: SUPREME COURT")
print("="*60)

sc_chunks = []  # List of dicts: {chunk_id, case_id, court, text, area_of_law, disposal_nature, decision_date, ...}

for year in SC_YEARS:
    print(f"\n--- SC {year} ---")
    
    # 1. Download metadata parquet
    parquet_key = f"metadata/parquet/year={year}/metadata.parquet"
    try:
        obj = s3.get_object(Bucket='indian-supreme-court-judgments', Key=parquet_key)
        df = pd.read_parquet(io.BytesIO(obj['Body'].read()))
        print(f"  Metadata: {len(df)} cases")
    except Exception as e:
        print(f"  Metadata not found for {year}: {e}")
        continue
    
    # 2. Download English TAR and extract text
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
                            text = ""
                            for page in doc:
                                text += page.get_text("text") + "\n"
                            path_key = member.name.replace("_EN.pdf", "")
                            texts_by_path[path_key] = text.strip()
                        except:
                            pass
        print(f"  Extracted text from {len(texts_by_path)} PDFs")
        del tar_bytes  # Free memory
    except Exception as e:
        print(f"  TAR download failed for {year}: {e}")
        continue
    
    # 3. Chunk and prepare
    for _, row in df.iterrows():
        path = str(row.get('path', ''))
        text = texts_by_path.get(path, '')
        if len(text) < 200:
            continue
        
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
    
    print(f"  Total SC chunks so far: {len(sc_chunks)}")

# 4. Embed all SC chunks on GPU
print(f"\nEmbedding {len(sc_chunks)} SC chunks on GPU...")
if sc_chunks:
    sc_texts = [c['text'] for c in sc_chunks]
    sc_embeddings = embed_texts(sc_texts, batch_size=64)
    
    sc_df = pd.DataFrame(sc_chunks)
    sc_df['embedding'] = list(sc_embeddings.astype(np.float16))
    sc_df.to_parquet('/kaggle/working/sc_embeddings.parquet')
    print(f"Saved sc_embeddings.parquet ({len(sc_df)} chunks)")
    
    del sc_embeddings, sc_texts  # Free memory

# ============================================================================
# PART 2: KARNATAKA HC DIVISION BENCH (10 YEARS)
# ============================================================================
print("\n" + "="*60)
print("PART 2: KARNATAKA HC DIVISION BENCH")
print("="*60)

hc_chunks = []

for year in HC_YEARS:
    print(f"\n--- HC Karnataka {year} ---")
    
    # 1. List all bench parquets for this court/year
    prefix = f"metadata/parquet/year={year}/court={HC_COURT_CODE}/"
    try:
        resp = s3.list_objects_v2(Bucket='indian-high-court-judgments', Prefix=prefix)
        parquet_keys = [o['Key'] for o in resp.get('Contents', []) if o['Key'].endswith('.parquet')]
    except Exception as e:
        print(f"  Failed to list: {e}")
        continue
    
    for pkey in parquet_keys:
        bench = pkey.split('bench=')[1].split('/')[0] if 'bench=' in pkey else 'unknown'
        
        try:
            obj = s3.get_object(Bucket='indian-high-court-judgments', Key=pkey)
            df = pd.read_parquet(io.BytesIO(obj['Body'].read()))
        except Exception as e:
            print(f"  Failed parquet {pkey}: {e}")
            continue
        
        # 2. Filter: Division Bench only (judge field contains multiple judges)
        # Division Bench = 2+ judges. Single judge entries typically have one name.
        # We detect by checking for "AND" or comma in judge names
        if 'judge' in df.columns:
            judge_col = df['judge'].fillna('')
            is_division = judge_col.str.contains(' AND ', case=False) | judge_col.str.contains(',', case=False)
            df_div = df[is_division].copy()
        else:
            df_div = df.copy()
        
        # 3. Filter: Final judgments only (not pending/interim)
        if 'disposal_nature' in df.columns:
            final_disposals = ['DISPOSED', 'DISMISSED', 'ALLOWED', 'PARTLY ALLOWED', 
                             'DISPOSED OF', 'DECREED', 'Appeal(s) allowed', 
                             'Disposed off', 'Dismissed']
            disposal_col = df_div['disposal_nature'].fillna('').str.upper()
            is_final = disposal_col.str.len() > 0  # Any non-empty disposal = final
            df_div = df_div[is_final].copy()
        
        if len(df_div) == 0:
            continue
            
        print(f"  {bench}: {len(df_div)} Division Bench final judgments (out of {len(df)} total)")
        
        # 4. For HC, we only have the description (~290 chars) as text
        # We'll try to download individual PDFs for Division Bench cases
        # But if that's too slow, we fall back to description
        
        for _, row in df_div.iterrows():
            case_id = str(row.get('cnr', ''))
            title = str(row.get('title', ''))
            desc = str(row.get('description', ''))
            text = f"{title} {desc}".strip()
            
            if len(text) < 30:
                continue
            
            area = classify_title(title)
            
            # HC descriptions are short (~290 chars), no need to chunk
            hc_chunks.append({
                'chunk_id': f"{case_id}_chunk_0",
                'case_id': case_id,
                'court': 'High Court of Karnataka',
                'area_of_law': area,
                'disposal_nature': str(row.get('disposal_nature', '')),
                'decision_date': str(row.get('decision_date', '')),
                'petitioner': '',  # HC doesn't have separate petitioner/respondent columns
                'respondent': '',
                'title': title[:200],
                'chunk_index': 0,
                'text': text,
            })
    
    print(f"  Total HC chunks so far: {len(hc_chunks)}")

# 5. Embed all HC chunks on GPU
print(f"\nEmbedding {len(hc_chunks)} HC chunks on GPU...")
if hc_chunks:
    hc_texts = [c['text'] for c in hc_chunks]
    hc_embeddings = embed_texts(hc_texts, batch_size=64)
    
    hc_df = pd.DataFrame(hc_chunks)
    hc_df['embedding'] = list(hc_embeddings.astype(np.float16))
    hc_df.to_parquet('/kaggle/working/hc_embeddings.parquet')
    print(f"Saved hc_embeddings.parquet ({len(hc_df)} chunks)")

print("\n" + "="*60)
print("DONE! Download sc_embeddings.parquet and hc_embeddings.parquet")
print("Then run locally: python manage.py import_kaggle_embeddings")
print("="*60)
