import pytest
from utils import deduplicate_local, extract_json

def test_deduplicate_local():
    events = [
        {"date":"01 janvier 2025","lieu":"Salle A, Paris"},
        {"date":"01 janvier 2025","lieu":"Salle A, Paris"},
        {"date":"02 janvier 2025","lieu":"Salle B, Lyon"}
    ]
    res = deduplicate_local(events)
    assert len(res) == 2

def test_extract_json_simple():
    raw = "Voici un JSON: ```json [ {\"nom\":\"X\"} ] ```"
    arr = extract_json(raw)
    assert isinstance(arr, list)
    assert arr and arr[0].get("nom") == "X"
