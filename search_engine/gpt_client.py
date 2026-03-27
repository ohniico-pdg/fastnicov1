import os
import json
import urllib.request
import urllib.error
from typing import Optional

GPT_MODEL = os.environ.get("GPT_MODEL", "gpt-4o")
GPT_MINI  = os.environ.get("GPT_MINI", "gpt-4o-mini")

SYSTEM_INSTRUCTIONS = (
    "Tu es un expert en recherche d'événements culturels français (spectacles, stand-up, humour). "
    "Tu retournes TOUJOURS un tableau JSON valide commençant par [ et finissant par ]. "
    "Les résultats sont DÉDUPLIQUÉS et TRIÉS par date croissante. "
    "Uniquement des dates 2025-2026. Si rien trouvé: []"
)

def http_post(url, body, headers, timeout=90):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode())
            msg = err.get("error", {}).get("message") or str(err)
        except:
            msg = "HTTP " + str(e.code)
        raise Exception(msg)
    except Exception as e:
        raise

def gpt_search(api_key: str, prompt: str, model: Optional[str] = None, timeout: int = 90):
    model = model or GPT_MODEL
    max_tokens = 1500 if model == GPT_MINI else 3000
    body = {
        "model": model,
        "max_output_tokens": max_tokens,
        "tools": [{"type": "web_search_preview"}],
        "instructions": SYSTEM_INSTRUCTIONS,
        "input": prompt
    }
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
    return http_post("https://api.openai.com/v1/responses", body, headers, timeout=timeout)
