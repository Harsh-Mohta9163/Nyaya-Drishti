"""
Import pre-computed embeddings from Kaggle into ChromaDB.
Usage: python manage.py import_kaggle_embeddings --path C:/path/to/downloaded/
"""
import os
import logging
import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Import Kaggle-generated embeddings into ChromaDB"

    def add_arguments(self, parser):
        parser.add_argument("--path", type=str, required=True,
                          help="Path to folder containing sc_embeddings.parquet and/or hc_embeddings.parquet")
        parser.add_argument("--offset", type=int, default=0,
                          help="Offset to start importing from (useful for resuming)")

    def handle(self, *args, **options):
        import_path = options["path"]
        offset = options["offset"]
        
        # Import ChromaDB with the InLegalBERT embedding function
        from apps.action_plans.services.rag_engine import _get_collection, _rebuild_bm25
        collection = _get_collection()
        
        total_imported = 0
        
        for filename in ['sc_embeddings.parquet', 'hc_embeddings.parquet']:
            filepath = os.path.join(import_path, filename)
            if not os.path.exists(filepath):
                self.stdout.write(f"  Skipping {filename} (not found)")
                continue
                
            self.stdout.write(self.style.SUCCESS(f"\nImporting {filename}..."))
            df = pd.read_parquet(filepath)
            self.stdout.write(f"  Loaded {len(df)} chunks")
            
            # Apply offset if provided
            start_idx = offset if offset > 0 else 0
            
            # Process in batches to avoid memory issues
            batch_size = 500
            for i in range(start_idx, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                
                ids = batch['chunk_id'].tolist()
                documents = batch['text'].tolist()
                
                # Convert float16 embeddings back to float32 lists
                embeddings = [np.array(e, dtype=np.float32).tolist() for e in batch['embedding'].tolist()]
                
                # Build metadata dicts
                meta_cols = ['case_id', 'court', 'area_of_law', 'disposal_nature',
                           'decision_date', 'petitioner', 'respondent', 'title', 'chunk_index']
                metadatas = []
                for _, row in batch.iterrows():
                    meta = {}
                    for col in meta_cols:
                        val = row.get(col, '')
                        if val is None or (isinstance(val, float) and np.isnan(val)):
                            continue
                        if isinstance(val, (str, int, float, bool)):
                            meta[col] = val
                        else:
                            meta[col] = str(val)
                    metadatas.append(meta)
                
                # Upsert with pre-computed embeddings (no re-embedding needed!)
                collection.upsert(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )
                
                if (i // batch_size) % 10 == 0:
                    self.stdout.write(f"  Imported {i+len(batch)}/{len(df)} chunks...")
            
            total_imported += len(df)
            self.stdout.write(self.style.SUCCESS(f"  Done: {len(df)} chunks from {filename}"))
        
        # Rebuild BM25 index
        self.stdout.write("\nRebuilding BM25 index...")
        _rebuild_bm25()
        
        self.stdout.write(self.style.SUCCESS(f"\nTotal imported: {total_imported} chunks into ChromaDB"))
