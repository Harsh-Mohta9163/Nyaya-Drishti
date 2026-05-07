#!/bin/bash

echo "Starting deployment script..."

# The application writable data directory
mkdir -p /app/data

# 1. Unzip the Chroma DB if it's in the mounted Hugging Face dataset
if [ -f "/hf_dataset/chroma_db_export.zip" ]; then
    echo "Found chroma_db_export.zip! Unzipping into /app/data..."
    unzip -o -q /hf_dataset/chroma_db_export.zip -d /app/data/
    echo "Unzip complete."
elif [ -d "/hf_dataset/chroma_db" ]; then
    echo "Found unzipped chroma_db directory! Copying to /app/data..."
    cp -r /hf_dataset/chroma_db /app/data/
fi

# 2. Copy the Parquet files if they exist
if ls /hf_dataset/*.parquet 1> /dev/null 2>&1; then
    echo "Found Parquet files! Copying to /app/data..."
    cp /hf_dataset/*.parquet /app/data/
fi

# 3. Apply database migrations (Creates the SQLite DB if it doesn't exist)
echo "Applying database migrations..."
python manage.py migrate --noinput

# 4. Start the server
echo "Starting Django Server..."
exec gunicorn --bind 0.0.0.0:7860 --workers 2 --threads 4 --timeout 120 config.wsgi:application
