import os
import logging
from flask import Flask, request, jsonify
from search_engine.threads import run_search_for_artist
from search_engine.memory import get_artist_memory, save_artist_memory
from search_engine.cache import get_cache, save_cache

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Capta Vidéo proxy (optimized)"})

@app.route("/api/search", methods=["POST"])
def search():
    data = request.get_json() or {}
    artiste = (data.get("artiste") or "").strip()
    key_gpt = data.get("key_gpt") or os.environ.get("OPENAI_API_KEY", "")
    mode = data.get("mode", "full")  # "fast" or "full"
    if not artiste:
        return jsonify({"error": "Artiste manquant"}), 400
    if not key_gpt:
        return jsonify({"error": "Clé OpenAI manquante"}), 400

    # 1) cache check
    cached = get_cache(artiste)
    if cached is not None and mode == "fast":
        return jsonify({"results": cached, "source": "cache", "message": "cache hit (fast mode)"})

    # 2) run search (threads + scrapers + conditional logic)
    try:
        results, sources_used = run_search_for_artist(
            artiste=artiste,
            key_gpt=key_gpt,
            mode=mode,
            request_payload=data
        )
    except Exception as e:
        logger.exception("Search failed: %s", e)
        return jsonify({"error": "Recherche échouée"}), 500

    # 3) save cache and memory updates if any
    save_cache(artiste, results)
    return jsonify({"results": results, "sources_used": sources_used, "source": "live"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
