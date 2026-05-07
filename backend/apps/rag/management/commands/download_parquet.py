import os
import io
import tarfile
import logging
import boto3
from botocore import UNSIGNED
from botocore.config import Config
import pandas as pd
import fitz  # PyMuPDF

from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Downloads AWS Parquet metadata and enriches it with SC judgment text"

    def add_arguments(self, parser):
        parser.add_argument("--years", type=str, default="2023,2024", help="Comma-separated years to download")
        parser.add_argument("--courts", type=str, default="sc", help="sc,karnataka,delhi,bombay etc.")
        
    def handle(self, *args, **options):
        years = options["years"].split(",")
        courts = options["courts"].split(",")
        
        # We will store everything in backend/data/parquet/
        base_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "data", "parquet"
        )
        os.makedirs(base_dir, exist_ok=True)
        
        s3 = boto3.client('s3', region_name='ap-south-1', config=Config(signature_version=UNSIGNED))
        
        for year in years:
            if "sc" in courts:
                self.stdout.write(self.style.SUCCESS(f"\nProcessing Supreme Court for year {year}..."))
                self._process_sc(s3, base_dir, year)
                
            if "karnataka" in courts:
                self.stdout.write(self.style.SUCCESS(f"\nProcessing Karnataka High Court for year {year}..."))
                self._process_hc(s3, base_dir, year, "29_3")

    def _process_sc(self, s3, base_dir, year):
        bucket = "indian-supreme-court-judgments"
        parquet_key = f"metadata/parquet/year={year}/metadata.parquet"
        tar_key = f"data/tar/year={year}/english/english.tar"
        
        out_dir = os.path.join(base_dir, "sc", year)
        os.makedirs(out_dir, exist_ok=True)
        out_parquet = os.path.join(out_dir, "metadata_enriched.parquet")
        
        if os.path.exists(out_parquet):
            self.stdout.write(f"  Skipping: {out_parquet} already exists.")
            return

        # 1. Download Parquet
        self.stdout.write(f"  Downloading parquet metadata: {parquet_key}")
        try:
            obj = s3.get_object(Bucket=bucket, Key=parquet_key)
            df = pd.read_parquet(io.BytesIO(obj['Body'].read()))
            self.stdout.write(f"  Loaded {len(df)} rows.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Failed to load parquet: {e}"))
            return

        # 2. Add empty text columns
        df['judgment_text'] = ""
        df['text_length'] = 0

        # 3. Download and stream TAR file to extract text from PDFs
        self.stdout.write(f"  Downloading & extracting TAR (this might take a while): {tar_key}")
        try:
            # We stream the tar object directly into memory
            obj = s3.get_object(Bucket=bucket, Key=tar_key)
            tar_bytes = io.BytesIO(obj['Body'].read())
            
            extracted_count = 0
            with tarfile.open(fileobj=tar_bytes, mode='r') as tar:
                for member in tar.getmembers():
                    if member.name.endswith('.pdf'):
                        # SC paths in parquet look like "2024_10_108_125". 
                        # Inside tar, files are "2024_10_108_125_EN.pdf"
                        f = tar.extractfile(member)
                        if f:
                            pdf_bytes = f.read()
                            try:
                                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                                text = ""
                                for page in doc:
                                    text += page.get_text("text") + "\n"
                                
                                # Match with dataframe
                                path_match = member.name.replace("_EN.pdf", "")
                                # df['path'] matches this exactly
                                mask = df['path'] == path_match
                                if mask.any():
                                    df.loc[mask, 'judgment_text'] = text.strip()
                                    df.loc[mask, 'text_length'] = len(text.strip())
                                    extracted_count += 1
                                    
                            except Exception as e:
                                logger.error(f"Error parsing PDF {member.name}: {e}")
                                
            self.stdout.write(f"  Extracted text for {extracted_count} / {len(df)} cases.")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Failed to process TAR: {e}"))
            
        # 4. Save enriched parquet
        df.to_parquet(out_parquet)
        self.stdout.write(self.style.SUCCESS(f"  Saved enriched parquet to {out_parquet}"))


    def _process_hc(self, s3, base_dir, year, court_code):
        # HC is massive. We only pull the metadata for now.
        bucket = "indian-high-court-judgments"
        # Since bench folders are dynamic, we list them first
        prefix = f"metadata/parquet/year={year}/court={court_code}/"
        
        try:
            resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
            for obj in resp.get('Contents', []):
                if obj['Key'].endswith('metadata.parquet'):
                    # e.g., metadata/parquet/year=2024/court=29_3/bench=karnataka_bng_old/metadata.parquet
                    parts = obj['Key'].split('/')
                    bench = parts[4].split('=')[1]
                    
                    out_dir = os.path.join(base_dir, "hc", court_code, year, bench)
                    os.makedirs(out_dir, exist_ok=True)
                    out_parquet = os.path.join(out_dir, "metadata_enriched.parquet")
                    
                    if os.path.exists(out_parquet):
                        self.stdout.write(f"  Skipping: {out_parquet} already exists.")
                        continue
                        
                    self.stdout.write(f"  Downloading parquet: {obj['Key']}")
                    parquet_obj = s3.get_object(Bucket=bucket, Key=obj['Key'])
                    df = pd.read_parquet(io.BytesIO(parquet_obj['Body'].read()))
                    
                    # For HC, we use the `description` (header) as the `judgment_text` 
                    # since it's the only text we have without downloading gigabytes of individual PDFs
                    df['judgment_text'] = df['description'].fillna("")
                    df['text_length'] = df['judgment_text'].str.len()
                    
                    df.to_parquet(out_parquet)
                    self.stdout.write(f"  Saved {len(df)} rows to {out_parquet}")
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Failed to list HC keys: {e}"))
