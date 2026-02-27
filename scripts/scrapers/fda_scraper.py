#!/usr/bin/env python3
"""
FDA OpenFDA API Scraper - fetches guidance documents and device classification info.

API Docs: https://open.fda.gov/apis/
Rate limit: 240 requests/minute, 120k requests/day (no API key)
"""
import os
import json
import time
import hashlib
import requests
from pathlib import Path
from typing import List, Dict

CACHE_DIR = Path(__file__).resolve().parents[2] / "documents" / "fda_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

FDA_DEVICE_CLASS_ENDPOINT = "https://api.fda.gov/device/classification.json"
FDA_DEVICE_510K_ENDPOINT = "https://api.fda.gov/device/510k.json"


def fetch_device_classifications(device_types: List[str] = None) -> List[Dict]:
    """
    Fetch device classification data from FDA.
    
    Args:
        device_types: Filter by device names (e.g., ['ventilator', 'oximeter'])
    
    Returns:
        List of classification records with device_name, device_class, regulation_number, etc.
    """
    results = []
    
    if not device_types:
        device_types = ["ventilator", "oximeter", "dialysis", "infusion pump", 
                       "ecg", "blood pressure", "glucose", "defibrillator"]
    
    for dtype in device_types:
        print(f"Fetching FDA classifications for: {dtype}")
        try:
            # Search by device name
            params = {
                "search": f"device_name:\"{dtype}\"",
                "limit": 100
            }
            
            resp = requests.get(FDA_DEVICE_CLASS_ENDPOINT, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if "results" in data:
                for result in data["results"]:
                    doc = {
                        "device_name": result.get("device_name", ""),
                        "device_class": result.get("device_class", ""),
                        "regulation_number": result.get("regulation_number", ""),
                        "medical_specialty": result.get("medical_specialty", ""),
                        "product_code": result.get("product_code", ""),
                        "definition": result.get("definition", ""),
                        "review_panel": result.get("review_panel", ""),
                        "source_type": "fda_classification",
                        "authority_level": 4
                    }
                    results.append(doc)
                    
            time.sleep(0.3)  # Rate limit safety
            
        except Exception as e:
            print(f"Warning: Failed to fetch {dtype}: {e}")
            continue
    
    print(f"Fetched {len(results)} FDA classification records")
    return results


def fetch_510k_summaries(limit: int = 100) -> List[Dict]:
    """
    Fetch recent 510(k) premarket notification summaries.
    
    Returns:
        List of 510(k) records with device description, indications, etc.
    """
    print(f"Fetching {limit} recent 510(k) summaries...")
    results = []
    
    try:
        params = {
            "limit": limit,
            "sort": "date_received:desc"
        }
        
        resp = requests.get(FDA_DEVICE_510K_ENDPOINT, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if "results" in data:
            for result in data["results"]:
                doc = {
                    "k_number": result.get("k_number", ""),
                    "device_name": result.get("device_name", ""),
                    "applicant": result.get("applicant", ""),
                    "device_class": result.get("device_class", ""),
                    "decision_description": result.get("decision_description", ""),
                    "statement_or_summary": result.get("statement_or_summary", ""),
                    "date_received": result.get("date_received", ""),
                    "source_type": "fda_510k",
                    "authority_level": 4
                }
                results.append(doc)
                
    except Exception as e:
        print(f"Warning: Failed to fetch 510(k) data: {e}")
    
    print(f"Fetched {len(results)} 510(k) records")
    return results


def cache_results(data: List[Dict], cache_name: str):
    """Save results to JSON cache."""
    cache_file = CACHE_DIR / f"{cache_name}_{int(time.time())}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Cached to: {cache_file}")


def run_fda_scraper():
    """Main entry point for FDA scraper."""
    print("=" * 60)
    print("FDA OpenFDA API Scraper")
    print("=" * 60)
    
    classifications = fetch_device_classifications()
    cache_results(classifications, "fda_classifications")
    
    summaries = fetch_510k_summaries(limit=50)
    cache_results(summaries, "fda_510k")
    
    print(f"\nTotal records: {len(classifications) + len(summaries)}")
    print("Done. Run indexer to add to RAG database.")
    
    return classifications + summaries


if __name__ == "__main__":
    run_fda_scraper()
