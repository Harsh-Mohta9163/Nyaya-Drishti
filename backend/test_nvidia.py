import requests
import json

resp = requests.post(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    headers={
        "Authorization": "Bearer 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",
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
