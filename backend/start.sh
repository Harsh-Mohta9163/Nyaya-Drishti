#!/bin/bash

echo "Starting deployment script..."

# The application writable data directory
mkdir -p /app/data

# 1. Download the Dataset using Hugging Face CLI
if [ -z "$HF_DATASET_ID" ]; then
    echo "WARNING: HF_DATASET_ID environment variable is not set. Cannot download dataset."
else
    echo "Downloading dataset $HF_DATASET_ID from Hugging Face..."
    # Install huggingface_hub if not present
    pip install huggingface_hub
    
    python -c "
import os, zipfile
from huggingface_hub import hf_hub_download, snapshot_download

repo = os.environ.get('HF_DATASET_ID')
print('Downloading parquet files...')
snapshot_download(repo_id=repo, repo_type='dataset', allow_patterns='*.parquet', local_dir='/app/data')

print('Downloading chroma_db_export.zip...')
zip_path = hf_hub_download(repo_id=repo, filename='chroma_db_export.zip', repo_type='dataset')

print('Unzipping chroma db...')
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall('/app/data/')
print('Dataset download and extraction complete.')
"
fi

# 3. Apply database migrations (Creates the SQLite DB if it doesn't exist)
echo "Applying database migrations..."
python manage.py migrate --noinput

# 4. Seed departments and demo users (idempotent — safe to re-run)
echo "Seeding demo data..."
python manage.py seed_demo_data

# 5. Start the server
echo "Starting Django Server..."
exec gunicorn --bind 0.0.0.0:7860 --workers 2 --threads 4 --timeout 120 config.wsgi:application
