import json
import os
import time

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

load_dotenv()

# models get retired a lot on groq, so it lives in .env
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

_client = None


def get_client():
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("no GROQ_API_KEY found, check your .env")
        _client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
    return _client


def ask_json(system, user):
    # groq free tier rate limits a lot, so retry a few times instead of dying
    for attempt in range(3):
        try:
            res = get_client().chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            return json.loads(res.choices[0].message.content)
        except RateLimitError:
            wait = 5 * (attempt + 1)
            print(f"rate limited, waiting {wait}s...")
            time.sleep(wait)
    raise RuntimeError("still rate limited, try again in a minute")