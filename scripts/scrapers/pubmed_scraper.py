#!/usr/bin/env python3
"""
PubMed/NCBI API Scraper - fetches medical literature abstracts.

API Docs: https://www.ncbi.nlm.nih.gov/books/NBK25501/
Rate limit: 3 requests/second (no API key), 10/sec with key
"""
import os
import json
import time
import requests
from pathlib import Path
from typing import List, Dict
from xml.etree import ElementTree as ET

CACHE_DIR = Path(__file__).resolve().parents[2] / "documents" / "pubmed_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def search_pubmed(query: str, max_results: int = 50) -> List[str]:
    """
    Search PubMed and return list of PMIDs.
    
    Args:
        query: Search query (e.g., "medical device ventilator design")
        max_results: Max PMIDs to return
    
    Returns:
        List of PubMed IDs
    """
    print(f"Searching PubMed for: {query}")
    
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance"
    }
    
    try:
        resp = requests.get(PUBMED_SEARCH_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        pmids = data.get("esearchresult", {}).get("idlist", [])
        print(f"Found {len(pmids)} articles")
        return pmids
        
    except Exception as e:
        print(f"Error searching PubMed: {e}")
        return []


def fetch_abstracts(pmids: List[str]) -> List[Dict]:
    """
    Fetch article metadata and abstracts for given PMIDs.
    
    Returns:
        List of article records with title, abstract, authors, etc.
    """
    if not pmids:
        return []
    
    print(f"Fetching {len(pmids)} abstracts...")
    
    # Fetch in batches of 20
    batch_size = 20
    results = []
    
    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i+batch_size]
        
        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "xml"
        }
        
        try:
            resp = requests.get(PUBMED_FETCH_URL, params=params, timeout=30)
            resp.raise_for_status()
            
            root = ET.fromstring(resp.content)
            
            for article in root.findall(".//PubmedArticle"):
                try:
                    pmid = article.find(".//PMID").text if article.find(".//PMID") is not None else ""
                    title_elem = article.find(".//ArticleTitle")
                    title = title_elem.text if title_elem is not None else ""
                    
                    # Extract abstract
                    abstract_parts = []
                    for abs_text in article.findall(".//AbstractText"):
                        if abs_text.text:
                            label = abs_text.get("Label", "")
                            text = abs_text.text
                            abstract_parts.append(f"{label}: {text}" if label else text)
                    abstract = " ".join(abstract_parts)
                    
                    # Extract authors
                    authors = []
                    for author in article.findall(".//Author"):
                        last = author.find("LastName")
                        first = author.find("ForeName")
                        if last is not None and first is not None:
                            authors.append(f"{last.text} {first.text}")
                    
                    # Extract year
                    year_elem = article.find(".//PubDate/Year")
                    year = year_elem.text if year_elem is not None else ""
                    
                    doc = {
                        "pmid": pmid,
                        "title": title,
                        "abstract": abstract[:2000],  # Truncate long abstracts
                        "authors": ", ".join(authors[:5]),  # First 5 authors
                        "year": year,
                        "source_type": "medical_literature",
                        "authority_level": 2
                    }
                    results.append(doc)
                    
                except Exception as e:
                    print(f"Warning: Failed to parse article: {e}")
                    continue
            
            time.sleep(0.4)  # Rate limit: ~3/sec
            
        except Exception as e:
            print(f"Error fetching batch: {e}")
            continue
    
    print(f"Fetched {len(results)} abstracts")
    return results


def run_pubmed_scraper(queries: List[str] = None, max_per_query: int = 30):
    """
    Main entry point for PubMed scraper.
    
    Args:
        queries: List of search queries
        max_per_query: Max results per query
    """
    print("=" * 60)
    print("PubMed Medical Literature Scraper")
    print("=" * 60)
    
    if not queries:
        queries = [
            "medical device design ISO 14971",
            "ventilator design safety",
            "pulse oximeter accuracy clinical",
            "dialysis machine risk management",
            "medical device usability IEC 62366",
            "infusion pump failure modes"
        ]
    
    all_results = []
    
    for query in queries:
        pmids = search_pubmed(query, max_results=max_per_query)
        articles = fetch_abstracts(pmids)
        all_results.extend(articles)
        time.sleep(1)  # Polite delay between queries
    
    # Cache results
    if all_results:
        cache_file = CACHE_DIR / f"pubmed_results_{int(time.time())}.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nCached {len(all_results)} articles to: {cache_file}")
    
    print("Done. Run indexer to add to RAG database.")
    return all_results


if __name__ == "__main__":
    run_pubmed_scraper()
