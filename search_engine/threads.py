import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, List
from search_engine.gpt_client import gpt_search, GPT_MODEL, GPT_MINI
from search_engine.scrapers.ticketmaster import scrape_ticketmaster
from search_engine.memory import get_artist_memory, save_artist_memory
from utils import extract_json, deduplicate_local

logger = logging.getLogger(__name__)

MAX_WORKERS = int(__import__("os").environ.get("MAX_WORKERS", "6"))

def should_run_thread(name: str, mem: dict, site_url: str, ig_url: str, scores: dict) -> bool:
    if name == "instagram" and mem.get("instagram_confirmed"):
        return False
    if name == "billetterie_b" and max([scores.get(s, 0) for s in ["ticketmaster.fr","fnacspectacles.com","seetickets.fr"]]) > 0.8:
        return False
    return True

def run_gpt_thread(api_key, name, prompt, model=None, timeout=45):
    try:
        resp = gpt_search(api_key, prompt, model=model, timeout=timeout)
        txt = ""
        for item in resp.get("output", []):
            if item.get("type") == "message":
                for c in item.get("content", []):
                    if c.get("type") == "output_text":
                        txt = c["text"].strip()
                        break
        found = extract_json(txt)
        for ev in found:
            ev["_thread"] = name
        return found, name
    except Exception as e:
        logger.exception("Thread %s error: %s", name, e)
        return [], name

def run_search_for_artist(artiste: str, key_gpt: str, mode: str = "full", request_payload: dict = None) -> Tuple[List[dict], List[str]]:
    mem = get_artist_memory(artiste)
    site_url = request_payload.get("site_artiste") if request_payload else mem.get("site")
    ig_input = (request_payload.get("instagram") or "").strip().replace("@", "") if request_payload else ""
    ig_url = ig_input and f"https://www.instagram.com/{ig_input}/" or mem.get("instagram", "")
    scores = mem.get("source_scores", {})

    # 1) quick scrapers for billetteries A
    results = []
    sources_used = []
    try:
        tm = scrape_ticketmaster(artiste)
        if tm:
            results.extend(tm)
            sources_used.append("ticketmaster_scraper")
    except Exception:
        logger.exception("Ticketmaster scraper failed")

    # 2) prepare prompts (shortened)
    context_lines = []
    if mem.get("site"):
        context_lines.append(f"Site confirmé: {mem['site']}")
    if mem.get("instagram"):
        context_lines.append(f"IG confirmé: {mem['instagram']}")
    if scores:
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        context_lines.append("Top sources: " + ", ".join(s for s,_ in top))
    context = "\n".join(context_lines)

    # minimal event schema hint
    event_schema = '[{"nom":"Nom exact","artistes":"Nom artiste","date":"JJ Mois AAAA","heure":"20h30","lieu":"Salle, Ville","source":"URL"}]'

    # prompts (short)
    prompt_site = f"{context}\nVa sur {site_url} et extrait toutes les dates 2025-2026. JSON: {event_schema}" if site_url else ""
    prompt_ig = f"{context}\nVa sur {ig_url} et lis les 5 derniers posts pour dates 2025-2026. JSON: {event_schema}" if ig_url else ""
    prompt_bill_b = f"{context}\nRecherche sur billetteries secondaires pour {artiste}. JSON: {event_schema}"
    prompt_google = f"{context}\nRecherche Google: \"{artiste} spectacle dates 2025 2026\". Parcours 5 premiers résultats. JSON: {event_schema}"

    # 3) decide threads to run
    tasks = []
    if site_url and should_run_thread("site_officiel", mem, site_url, ig_url, scores):
        tasks.append(("site_officiel", prompt_site, GPT_MODEL))
    if ig_url and should_run_thread("instagram", mem, site_url, ig_url, scores):
        tasks.append(("instagram", prompt_ig, GPT_MINI))
    if should_run_thread("billetterie_b", mem, site_url, ig_url, scores):
        tasks.append(("billetterie_b", prompt_bill_b, GPT_MINI))
    if mode == "full":
        tasks.append(("google", prompt_google, GPT_MINI))

    # 4) run threads in parallel
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(tasks) or 1)) as ex:
        futures = {ex.submit(run_gpt_thread, key_gpt, name, prompt, model): (name, prompt) for name, prompt, model in tasks if prompt}
        for fut in as_completed(futures):
            found, name = fut.result()
            if found:
                results.extend(found)
                sources_used.append(name)

    # 5) dedupe + cross-verify (simple)
    results = deduplicate_local(results)
    return results, sources_used
