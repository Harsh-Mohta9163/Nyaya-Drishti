import boto3
from botocore import UNSIGNED
from botocore.config import Config

s3 = boto3.client('s3', region_name='ap-south-1', config=Config(signature_version=UNSIGNED))
bucket = 'indian-high-court-judgments'
prefix = 'data/pdf/year=2024/court=29_3/bench=karnataka_bng_old/'

paginator = s3.get_paginator('list_objects_v2')
all_objects = []
for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
    all_objects.extend(page.get('Contents', []))

print(f"Total PDFs in prefix: {len(all_objects)}")

sizes = [o['Size'] for o in all_objects]
under_100 = sum(1 for s in sizes if s < 100*1024)
between = sum(1 for s in sizes if 100*1024 <= s < 200*1024)
over_200 = sum(1 for s in sizes if s >= 200*1024)
over_500 = sum(1 for s in sizes if s >= 500*1024)

print(f"\nSize distribution:")
print(f"  Under 100KB (1-5 page short orders): {under_100}")
print(f"  100-200KB (5-10 pages):              {between}")
print(f"  200-500KB (10-20 pages):             {over_200 - over_500}")
print(f"  Over 500KB (20+ pages, FULL judgments): {over_500}")

print(f"\nTop 15 LARGEST PDFs (likely full judgments):")
for o in sorted(all_objects, key=lambda x: x['Size'], reverse=True)[:15]:
    kb = o['Size'] / 1024
    name = o['Key'].split('/')[-1]
    print(f"  {kb:7.1f} KB | {name}")
