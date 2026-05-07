import os
import glob
import logging
import pandas as pd
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

# Rule-based mapping based on Indian Court abbreviations
CASE_TYPE_MAP = {
    "WP": "constitutional",
    "W.P": "constitutional",
    "CRL": "criminal_law",
    "CRIMINAL": "criminal_law",
    "MFA": "motor_vehicles",
    "M.F.A": "motor_vehicles",
    "RFA": "property_law",
    "R.F.A": "property_law",
    "TAX": "tax_law",
    "STA": "tax_law",
    "COM": "commercial",
    "COMPANY": "commercial",
    "ARB": "commercial",
    "MAT": "family_law",
    "FC": "family_law",
    "WA": "service_law", # Writ Appeals often involve service matters
    "W.A": "service_law",
    "LAB": "labour_law",
    "LCA": "labour_law"
}

def classify_by_title(title: str) -> str:
    title_upper = str(title).upper()
    for key, domain in CASE_TYPE_MAP.items():
        if key in title_upper:
            return domain
    return "civil_procedure" # Default fallback for miscellaneous cases

class Command(BaseCommand):
    help = "Instantly classify Parquet files using rule-based title matching"

    def handle(self, *args, **options):
        base_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "data", "parquet"
        )
        
        parquet_files = glob.glob(os.path.join(base_dir, '**', 'metadata_enriched.parquet'), recursive=True)
        
        if not parquet_files:
            self.stdout.write(self.style.WARNING("No enriched parquet files found. Run download_parquet first."))
            return
            
        self.stdout.write(self.style.SUCCESS(f"Found {len(parquet_files)} parquet files to classify."))
        
        for file_path in parquet_files:
            self.stdout.write(f"\nProcessing {file_path}...")
            try:
                df = pd.read_parquet(file_path)
                
                # We just use rule-based matching on the title
                titles = df.get('title', '').fillna('')
                
                self.stdout.write(f"  Classifying {len(df)} rows using fast rules...")
                
                df['area_of_law'] = titles.apply(classify_by_title)
                df['confidence'] = 1.0 # Rules are deterministic
                df['cluster_id'] = -1  # Skip clustering
                
                # Save back to same file
                df.to_parquet(file_path)
                
                # Print stats
                area_counts = df['area_of_law'].value_counts()
                self.stdout.write(self.style.SUCCESS(f"  Saved classified parquet. Top areas:"))
                for area, count in area_counts.head(5).items():
                    self.stdout.write(f"    - {area}: {count}")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Failed to classify {file_path}: {e}"))
