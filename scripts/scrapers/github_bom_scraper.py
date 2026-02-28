"""
GitHub BOM Scraper for Reference Medical Device Designs
Searches GitHub for medical device projects and extracts Bill of Materials
"""
import os
import requests
import json
import csv
import io
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import base64
from dotenv import load_dotenv

class GitHubBOMScraper:
    """Scraper for GitHub repositories containing medical device BOMs"""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv('GITHUB_API_TOKEN')
        # GitHub API works without token but has much lower rate limits (60/hour vs 5000/hour)
        
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.api_token:
            self.headers["Authorization"] = f"token {self.api_token}"
        
        self.cache_dir = Path(__file__).parent.parent.parent / "documents" / "reference_designs"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting
        self.rate_limit_delay = 2 if self.api_token else 60  # With token: 2s, without: 60s
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def search_medical_device_repos(self, limit: int = 20) -> List[Dict]:
        """
        Search GitHub for medical device repositories
        
        Returns:
            List of repository information
        """
        queries = [
            "ventilator medical device",
            "medical device hardware opensource",
            "hemodialysis machine",
            "patient monitor hardware",
            "medical device bill of materials",
            "FDA medical device hardware"
        ]
        
        repos = []
        seen_urls = set()
        
        for query in queries:
            print(f"Searching GitHub: {query}")
            self._rate_limit()
            
            try:
                response = requests.get(
                    f"{self.base_url}/search/repositories",
                    headers=self.headers,
                    params={
                        "q": query,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": 10
                    },
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                for item in data.get("items", []):
                    url = item.get("html_url")
                    if url in seen_urls:
                        continue
                    
                    seen_urls.add(url)
                    repos.append({
                        "name": item.get("name"),
                        "full_name": item.get("full_name"),
                        "description": item.get("description"),
                        "url": url,
                        "stars": item.get("stargazers_count"),
                        "language": item.get("language"),
                        "topics": item.get("topics", [])
                    })
                    
                    if len(repos) >= limit:
                        break
                
                if len(repos) >= limit:
                    break
                    
            except requests.RequestException as e:
                print(f"  Error: {e}")
                continue
        
        print(f"Found {len(repos)} repositories")
        return repos
    
    def search_bom_files(self, repo_full_name: str) -> List[Dict]:
        """
        Search for BOM files in a repository
        
        Args:
            repo_full_name: Repository full name (e.g., "owner/repo")
            
        Returns:
            List of BOM file information
        """
        self._rate_limit()
        
        # Search for common BOM file names
        bom_patterns = [
            "BOM.csv", "bom.csv", "bill_of_materials.csv",
            "BOM.xlsx", "bom.xlsx", "BoM.csv",
            "components.csv", "parts_list.csv"
        ]
        
        bom_files = []
        
        try:
            # Search repository contents
            response = requests.get(
                f"{self.base_url}/search/code",
                headers=self.headers,
                params={
                    "q": f"repo:{repo_full_name} filename:BOM OR filename:bom OR filename:bill_of_materials extension:csv extension:xlsx",
                    "per_page": 10
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    bom_files.append({
                        "name": item.get("name"),
                        "path": item.get("path"),
                        "url": item.get("html_url"),
                        "download_url": item.get("url")
                    })
            
        except requests.RequestException as e:
            print(f"  Error searching {repo_full_name}: {e}")
        
        return bom_files
    
    def download_bom_file(self, file_info: Dict, repo_full_name: str) -> Optional[str]:
        """
        Download BOM file content
        
        Returns:
            File content as string, or None if download fails
        """
        self._rate_limit()
        
        try:
            response = requests.get(
                file_info["download_url"],
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            # GitHub API returns base64 encoded content
            content_data = response.json()
            if "content" in content_data:
                content = base64.b64decode(content_data["content"]).decode('utf-8', errors='ignore')
                return content
            
        except Exception as e:
            print(f"  Error downloading {file_info['name']}: {e}")
        
        return None
    
    def parse_bom_csv(self, content: str) -> List[Dict]:
        """
        Parse CSV BOM file
        
        Returns:
            List of component dictionaries
        """
        components = []
        
        try:
            reader = csv.DictReader(io.StringIO(content))
            
            for row in reader:
                # Normalize common column names
                component = {}
                
                # Try to find part number
                for key in ['Part Number', 'PartNumber', 'Part_Number', 'MPN', 'P/N', 'part_number']:
                    if key in row and row[key]:
                        component['part_number'] = row[key].strip()
                        break
                
                # Try to find manufacturer
                for key in ['Manufacturer', 'Mfr', 'Vendor', 'manufacturer']:
                    if key in row and row[key]:
                        component['manufacturer'] = row[key].strip()
                        break
                
                # Try to find description
                for key in ['Description', 'Part Description', 'description', 'title']:
                    if key in row and row[key]:
                        component['description'] = row[key].strip()
                        break
                
                # Try to find quantity
                for key in ['Quantity', 'Qty', 'quantity', 'qty']:
                    if key in row and row[key]:
                        try:
                            component['quantity'] = int(row[key])
                        except:
                            pass
                        break
                
                # Try to find reference designator
                for key in ['Reference', 'Ref', 'RefDes', 'Designator', 'reference']:
                    if key in row and row[key]:
                        component['reference'] = row[key].strip()
                        break
                
                if component.get('part_number') or component.get('description'):
                    components.append(component)
        
        except Exception as e:
            print(f"  Error parsing CSV: {e}")
        
        return components
    
    def scrape_all_medical_device_boms(self) -> Dict:
        """
        Scrape BOMs from medical device repositories
        
        Returns:
            Dictionary mapping repo name to extracted components
        """
        print("Searching for medical device repositories...")
        repos = self.search_medical_device_repos(limit=20)
        
        all_boms = {}
        
        for repo in repos:
            print(f"\nAnalyzing: {repo['full_name']}")
            print(f"  Description: {repo.get('description', 'N/A')}")
            print(f"  Stars: {repo.get('stars', 0)}")
            
            bom_files = self.search_bom_files(repo['full_name'])
            
            if not bom_files:
                print("  No BOM files found")
                continue
            
            print(f"  Found {len(bom_files)} BOM file(s)")
            
            repo_boms = []
            
            for bom_file in bom_files:
                print(f"    Downloading: {bom_file['name']}")
                content = self.download_bom_file(bom_file, repo['full_name'])
                
                if content and bom_file['name'].endswith('.csv'):
                    components = self.parse_bom_csv(content)
                    if components:
                        print(f"      Extracted {len(components)} components")
                        repo_boms.append({
                            "file": bom_file['name'],
                            "path": bom_file['path'],
                            "url": bom_file['url'],
                            "components": components
                        })
            
            if repo_boms:
                all_boms[repo['full_name']] = {
                    "repo": repo,
                    "boms": repo_boms,
                    "scraped_at": datetime.utcnow().isoformat()
                }
        
        return all_boms
    
    def extract_bom_from_repo(self, repo: Dict) -> List[Dict]:
        """Extract BOM from a single repository (simplified for setup script)"""
        bom_files = self.search_bom_files(repo['full_name'])
        
        all_components = []
        
        for bom_file in bom_files:
            content = self.download_bom_file(bom_file, repo['full_name'])
            
            if content and bom_file['name'].endswith('.csv'):
                components = self.parse_bom_csv(content)
                for comp in components:
                    comp['repository'] = repo['full_name']
                    comp['source_file'] = bom_file['name']
                all_components.extend(components)
        
        return all_components
    
    def save_to_cache(self, boms: Dict, filename: str = "github_boms.json"):
        """Save BOM data to cache"""
        cache_file = self.cache_dir / filename
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(boms, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved BOMs from {len(boms)} repositories to {cache_file}")


def main():
    """Main execution"""
    # Load environment variables from .env file
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
    
    print("=== GitHub Medical Device BOM Scraper ===\n")
    
    scraper = GitHubBOMScraper()
    
    if not scraper.api_token:
        print("⚠️  No GitHub API token found. Rate limit: 60 requests/hour")
        print("   With token: 5000 requests/hour")
        print("\nTo get a GitHub token:")
        print("1. Visit https://github.com/settings/tokens")
        print("2. Generate new token (classic)")
        print("3. Select scope: 'public_repo'")
        print("4. Add to .env file: GITHUB_API_TOKEN=your_token_here\n")
        
        response = input("Continue without token? (y/n): ")
        if response.lower() != 'y':
            return
    
    print("Scraping medical device BOMs from GitHub...")
    print("This may take several minutes due to rate limiting.\n")
    
    boms = scraper.scrape_all_medical_device_boms()
    scraper.save_to_cache(boms)
    
    # Print summary
    print("\n=== Summary ===")
    total_boms = 0
    total_components = 0
    for repo_name, data in boms.items():
        bom_count = len(data['boms'])
        component_count = sum(len(bom['components']) for bom in data['boms'])
        total_boms += bom_count
        total_components += component_count
        print(f"{repo_name}: {bom_count} BOMs, {component_count} components")
    
    print(f"\nTotal: {total_boms} BOMs with {total_components} components from {len(boms)} repositories")
    print("\nNext step: Run 'python scripts/ingest_components.py' to add to RAG database")


if __name__ == "__main__":
    main()
