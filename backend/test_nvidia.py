import requests
import json
import os

resp = requests.post(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {os.environ.get('NVIDIA_API_KEY', 'YOUR_API_KEY')}",
        "Content-Type": "application/json",
    },
    json={
        "model": "meta/llama-3.3-70b-instruct",
        "messages": [{"role": "user", "content": 'Reply with valid JSON: {"greeting": "hello"}'}],
        "max_tokens": 50,
        "response_format": {"type": "json_object"},
    },
    timeout=30,
)

print(f"Status: {resp.status_code}")
print(resp.text[:500])
