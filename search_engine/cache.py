import os
import json
from datetime import datetime
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "..", "cache.json")

def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def artist_key(name):
    return name.lower().strip().replace(" ", "_")

def get_cache(artiste):
    cache = load_json(CACHE_FILE, {})
    entry = cache.get(artist_key(artiste))
    if not entry:
        return None
    try:
        diff = datetime.now() - datetime.fromisoformat(entry.get("cached_at", "1970-01-01T00:00:00"))
        if diff.total_seconds() < 86400:
            return entry.get("results", [])
    except:
        pass
    return None

def save_cache(artiste, results):
    cache = load_json(CACHE_FILE, {})
    cache[artist_key(artiste)] = {"cached_at": datetime.now().isoformat(), "results": results}
    save_json(CACHE_FILE, cache)
