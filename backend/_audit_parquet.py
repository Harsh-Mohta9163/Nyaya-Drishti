"""Audit the current state of all parquet files"""
import pandas as pd
import os, glob

base = os.path.join('apps', 'data', 'parquet')
files = glob.glob(os.path.join(base, '**', '*.parquet'), recursive=True)
print(f"Found {len(files)} parquet files:\n")

for f in files:
    df = pd.read_parquet(f)
    print(f"--- {os.path.relpath(f)} ---")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {list(df.columns)}")
    
    if 'text_length' in df.columns:
        stats = df['text_length'].describe()
        print(f"  text_length: min={stats['min']:.0f}, median={stats['50%']:.0f}, max={stats['max']:.0f}, mean={stats['mean']:.0f}")
        print(f"  Cases with text >= 500 chars: {(df['text_length'] >= 500).sum()}")
        print(f"  Cases with text >= 50 chars:  {(df['text_length'] >= 50).sum()}")
        print(f"  Cases with text == 0 chars:   {(df['text_length'] == 0).sum()}")
    
    if 'area_of_law' in df.columns:
        print(f"  area_of_law distribution:")
        for area, count in df['area_of_law'].value_counts().head(6).items():
            print(f"    {area}: {count}")
    else:
        print(f"  area_of_law: NOT CLASSIFIED YET")
    
    # Sample a title to see what the data looks like
    if 'title' in df.columns:
        print(f"  Sample title: {df['title'].iloc[0][:120]}")
    if 'judgment_text' in df.columns:
        sample_text = str(df['judgment_text'].iloc[0])[:200]
        print(f"  Sample judgment_text: {sample_text}")
    
    print()
