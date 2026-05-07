"""Quick inspection of AWS dataset structure"""
import boto3, json, tarfile, io
from botocore import UNSIGNED
from botocore.config import Config

s3 = boto3.client('s3', region_name='ap-south-1', config=Config(signature_version=UNSIGNED))

# 1. SC English TAR index
print("=== SC English TAR Index ===")
obj = s3.get_object(Bucket='indian-supreme-court-judgments', Key='data/tar/year=2024/english/english.index.json')
idx = json.loads(obj['Body'].read())
print(f"  File count: {idx.get('file_count')}")
print(f"  Size: {idx.get('tar_size_human')}")
for p in idx.get('parts', [])[:3]:
    print(f"  Part: {p['name']} -> {p['file_count']} files")
    # Show first few file names
    for fn in p.get('files', [])[:3]:
        print(f"    - {fn}")

# 2. SC Metadata TAR index
print("\n=== SC Metadata TAR Index ===")
obj2 = s3.get_object(Bucket='indian-supreme-court-judgments', Key='metadata/tar/year=2024/metadata.index.json')
idx2 = json.loads(obj2['Body'].read())
print(f"  File count: {idx2.get('file_count')}")
for p in idx2.get('parts', [])[:2]:
    print(f"  Part: {p['name']} -> {p['file_count']} files")
    for fn in p.get('files', [])[:3]:
        print(f"    - {fn}")

# 3. Download a tiny sample from the SC metadata tar to see the JSON structure
print("\n=== Sample SC Metadata JSON ===")
obj3 = s3.get_object(Bucket='indian-supreme-court-judgments', Key='metadata/tar/year=2024/metadata.tar', Range='bytes=0-1048576')
tar_bytes = io.BytesIO(obj3['Body'].read())
try:
    with tarfile.open(fileobj=tar_bytes, mode='r:') as tar:
        members = tar.getmembers()[:1]
        for m in members:
            f = tar.extractfile(m)
            if f:
                data = json.loads(f.read())
                print(f"  File: {m.name}")
                for k, v in data.items():
                    val = str(v)[:150] if v else 'NULL'
                    print(f"  {k:25s}: {val}")
except Exception as e:
    print(f"  Error reading tar: {e}")
