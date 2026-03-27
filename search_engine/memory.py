import os
import json
from datetime import datetime
import urllib.request

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "..", "memory.json")

def supa_get(table, filters=""):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    url = f"{SUPABASE_URL}/rest/v1/{table}?{filters}"
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode())
    except:
        return None

def supa_upsert(table, data):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal"
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return True
    except:
        return False

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

def get_artist_memory(artiste):
    key = artist_key(artiste)
    rows = supa_get("memory", f"artist_key=eq.{key}&select=data")
    if rows and len(rows) > 0:
        return rows[0].get("data", {})
    memory = load_json(MEMORY_FILE, {})
    return memory.get(key, {})

def save_artist_memory(artiste, data):
    key = artist_key(artiste)
    current = get_artist_memory(artiste)
    current.update(data)
    current["updated_at"] = datetime.now().isoformat()
    supa_upsert("memory", {
        "artist_key": key,
        "artist_name": artiste,
        "data": current,
        "updated_at": current["updated_at"]
    })
    memory = load_json(MEMORY_FILE, {})
    memory[key] = current
    save_json(MEMORY_FILE, memory)
