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
    
    # Download the zip file
    huggingface-cli download "$HF_DATASET_ID" chroma_db_export.zip --repo-type dataset --local-dir /app/data
    
    # Download the parquet files
    huggingface-cli download "$HF_DATASET_ID" --repo-type dataset --local-dir /app/data --include "*.parquet"
    
    # Unzip the Chroma DB
    if [ -f "/app/data/chroma_db_export.zip" ]; then
        echo "Unzipping chroma_db_export.zip..."
        unzip -o -q /app/data/chroma_db_export.zip -d /app/data/
        echo "Unzip complete."
    fi
fi

# 3. Apply database migrations (Creates the SQLite DB if it doesn't exist)
echo "Applying database migrations..."
python manage.py migrate --noinput

# 4. Start the server
echo "Starting Django Server..."
exec gunicorn --bind 0.0.0.0:7860 --workers 2 --threads 4 --timeout 120 config.wsgi:application
