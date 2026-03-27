import json
import unicodedata
import re
from datetime import datetime

def normalize_name(name: str) -> str:
    n = unicodedata.normalize("NFKD", name.lower().strip())
    n = "".join(c for c in n if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9\s]", "", n).strip()

def extract_json(raw: str):
    if not raw or not raw.strip():
        return []
    clean = raw.replace("```json", "").replace("```", "").strip()
    s = clean.find("[")
    e = clean.rfind("]") + 1
    if s != -1 and e > s:
        try:
            return json.loads(clean[s:e])
        except:
            pass
    return []

def deduplicate_local(events):
    seen = set()
    result = []
    for ev in events:
        date = (ev.get("date") or "").strip().lower()
        lieu = (ev.get("lieu") or "").split(",")[0].strip().lower()
        key = f"{date}|{lieu}"
        if key not in seen:
            seen.add(key)
            result.append(ev)
    # simple date sort attempt (best-effort)
    def sort_key(ev):
        d = ev.get("date", "")
        try:
            parts = d.split()
            if len(parts) >= 3:
                return (int(parts[2]), parts[1].lower(), int(parts[0]))
        except:
            pass
        return (9999, "", 0)
    result.sort(key=sort_key)
    return result
