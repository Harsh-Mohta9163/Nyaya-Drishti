import os
import glob
import logging
import pandas as pd
from django.core.management.base import BaseCommand
from apps.action_plans.services.rag_engine import HybridRAGEngine
from apps.rag.embedder import chunk_text

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Chunk and embed judgment texts into ChromaDB using InLegalBERT"

    def add_arguments(self, parser):
        parser.add_argument("--courts", type=str, default="sc",
                          help="Comma-separated: sc,hc. Default: sc only")

    def handle(self, *args, **options):
        courts = options["courts"].split(",")
        base_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "data", "parquet"
        )
        
        all_files = glob.glob(os.path.join(base_dir, '**', 'metadata_enriched.parquet'), recursive=True)
        
        # Filter by court type
        parquet_files = []
        for f in all_files:
            if "sc" in courts and os.sep + "sc" + os.sep in f:
                parquet_files.append(f)
            if "hc" in courts and os.sep + "hc" + os.sep in f:
                parquet_files.append(f)
        
        if not parquet_files:
            self.stdout.write(self.style.WARNING("No enriched parquet files found."))
            return
            
        self.stdout.write(self.style.SUCCESS(f"Found {len(parquet_files)} parquet files to embed."))
        
        # Initialize RAG Engine which uses ChromaDB
        rag = HybridRAGEngine()
        
        # We need the tokenizer for chunking
        # RAG engine already loaded the embedding function, we can reuse its tokenizer
        try:
            tokenizer = rag.collection.embedding_function.tokenizer
        except AttributeError:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained("law-ai/InLegalBERT")
            
        total_chunks_added = 0
            
        for file_path in parquet_files:
            self.stdout.write(f"\nProcessing {file_path} for vector embeddings...")
            try:
                df = pd.read_parquet(file_path)
                
                # Filter out cases with completely empty texts (keep descriptions)
                if 'text_length' in df.columns:
                    df = df[df['text_length'] >= 50]
                    
                self.stdout.write(f"  {len(df)} cases have sufficient text to embed.")
                
                documents_to_add = []
                
                for _, row in df.iterrows():
                    case_id = str(row.get('cnr', row.get('case_id', '')))
                    if not case_id:
                        continue
                        
                    text = str(row.get('judgment_text', ''))
                    if not text.strip():
                        continue
                        
                    chunks = chunk_text(text, tokenizer, max_tokens=512, overlap=128)
                    
                    for i, chunk in enumerate(chunks):
                        metadata = {
                            "id": f"{case_id}_chunk_{i}",
                            "case_id": case_id,
                            "court": str(row.get('court', '')),
                            "area_of_law": str(row.get('area_of_law', 'unknown')),
                            "cluster_id": int(row.get('cluster_id', -1)) if pd.notna(row.get('cluster_id')) else -1,
                            "disposal_nature": str(row.get('disposal_nature', '')),
                            "decision_date": str(row.get('decision_date', '')),
                            "petitioner": str(row.get('petitioner', ''))[:100],
                            "respondent": str(row.get('respondent', ''))[:100],
                            "chunk_index": i
                        }
                        
                        documents_to_add.append({
                            "text": chunk,
                            "metadata": metadata
                        })
                        
                if documents_to_add:
                    self.stdout.write(f"  Adding {len(documents_to_add)} chunks to ChromaDB...")
                    rag.add_documents(documents_to_add)
                    total_chunks_added += len(documents_to_add)
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Failed to process {file_path}: {e}"))
                
        self.stdout.write(self.style.SUCCESS(f"\nFinished! Added {total_chunks_added} chunks to ChromaDB."))
