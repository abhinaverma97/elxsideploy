"""
Nexar API Scraper for Component Data (formerly Octopart)
Fetches component specifications, datasheets, pricing, and availability
"""
import os
import requests
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

class NexarScraper:
    """Scraper for Nexar API (formerly Octopart) to fetch component data"""
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.getenv('NEXAR_ACCESS_TOKEN')
        self.client_id = os.getenv('NEXAR_CLIENT_ID')
        self.client_secret = os.getenv('NEXAR_CLIENT_SECRET')
        
        if not self.access_token:
            raise ValueError("Nexar access token not found. Set NEXAR_ACCESS_TOKEN environment variable.")
        
        self.base_url = "https://api.nexar.com/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        self.cache_dir = Path(__file__).parent.parent.parent / "documents" / "component_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting: Be conservative with evaluation tier
        # 1 request per 3 seconds = 20 per minute
        self.rate_limit_delay = 3
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def search_components(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for components by keyword
        
        Args:
            query: Search query (e.g., "STM32F4 microcontroller")
            limit: Maximum number of results
            
        Returns:
            List of component data dictionaries
        """
        self._rate_limit()
        
        # Nexar API GraphQL query (correct format from docs)
        graphql_query = """
        query partSearch($q: String!, $limit: Int!) {
          supSearch(q: $q, limit: $limit) {
            hits
            results {
              part {
                id
                name
                mpn
                shortDescription
                category {
                  id
                  name
                  parentId
                }
                manufacturer {
                  name
                  homepageUrl
                }
                medianPrice1000 {
                  price
                  quantity
                  currency
                }
                bestDatasheet {
                  url
                }
              }
            }
          }
        }
        """
        
        variables = {
            "q": query,
            "limit": limit
        }
        
        payload = {
            "query": graphql_query,
            "variables": variables
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            # Print response for debugging on error
            if response.status_code != 200:
                print(f"  API Response Status: {response.status_code}")
                print(f"  Response: {response.text[:500]}")
            
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                print(f"  API errors: {data['errors']}")
                return []
            
            # Safely navigate the response structure
            search_data = data.get("data", {})
            if not search_data:
                print(f"  No data in response")
                return []
            
            sup_search = search_data.get("supSearch", {})
            if not sup_search:
                print(f"  No supSearch in response")
                return []
            
            results = sup_search.get("results", [])
            if results is None:
                results = []
            
            components = []
            
            for result in results:
                part = result.get("part", {})
                if not part:
                    continue
                
                # Get price info if available
                price_info = part.get("medianPrice1000")
                price = price_info.get("price") if price_info else None
                currency = price_info.get("currency") if price_info else None
                
                # Get datasheet URL safely
                best_datasheet = part.get("bestDatasheet")
                datasheet_url = best_datasheet.get("url") if best_datasheet else None
                
                component = {
                    "mpn": part.get("mpn"),
                    "name": part.get("name"),
                    "manufacturer": part.get("manufacturer", {}).get("name") if part.get("manufacturer") else None,
                    "description": part.get("shortDescription") or part.get("name") or "",
                    "category": part.get("category", {}).get("name") if part.get("category") else None,
                    "datasheet_url": datasheet_url,
                    "price": price,
                    "currency": currency,
                    "specs": {},
                    "scraped_at": datetime.utcnow().isoformat()
                }
                
                components.append(component)
            
            return components
            
        except requests.RequestException as e:
            print(f"  Error fetching from Nexar: {e}")
            return []
    
    def search_medical_device_components(self) -> Dict[str, List[Dict]]:
        """
        Search for common medical device components by category
        
        Returns:
            Dictionary mapping component category to list of components
        """
        categories = {
            "microcontrollers": [
                "STM32F4 ARM Cortex-M4",
                "STM32H7 medical grade",
                "NXP i.MX RT1060"
            ],
            "sensors_pressure": [
                "Honeywell SSCSANN pressure sensor",
                "TE Connectivity MS5803 pressure",
                "Sensirion SDP800 differential pressure"
            ],
            "sensors_flow": [
                "Sensirion SFM3000 flow sensor",
                "Honeywell HAFBLF flow sensor",
                "TE Connectivity flow sensor medical"
            ],
            "sensors_oxygen": [
                "Sensirion SFM4300 O2 sensor",
                "MaximIntegrated MAX30102 SpO2",
                "Texas Instruments AFE4490 SpO2"
            ],
            "power_supply": [
                "TI TPS65070 medical PMIC",
                "Analog Devices ADP5070",
                "Maxim MAX17687 medical power"
            ],
            "motor_drivers": [
                "TI DRV8825 stepper driver",
                "Allegro A4988 stepper",
                "ST L6470 motor controller"
            ],
            "display": [
                "Newhaven NHD-4.3 TFT medical",
                "Crystalfontz medical grade display",
                "Sharp memory LCD medical"
            ],
            "communication": [
                "Silicon Labs EFM32 USB medical",
                "FTDI FT232H USB medical grade",
                "Texas Instruments AM335x medical"
            ]
        }
        
        all_components = {}
        
        for category, queries in categories.items():
            print(f"\n=== Searching {category} ===")
            all_components[category] = []
            
            for query in queries:
                print(f"  Searching: {query}")
                components = self.search_components(query, limit=5)
                all_components[category].extend(components)
                print(f"  Found {len(components)} components")
        
        return all_components
    
    def save_to_cache(self, components: Dict[str, List[Dict]], filename: str = "nexar_components.json"):
        """Save component data to cache"""
        cache_file = self.cache_dir / filename
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(components, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved {sum(len(v) for v in components.values())} components to {cache_file}")
    
    def load_from_cache(self, filename: str = "nexar_components.json") -> Optional[Dict]:
        """Load component data from cache"""
        cache_file = self.cache_dir / filename
        
        if not cache_file.exists():
            return None
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)


def main():
    """Main execution"""
    # Load environment variables from .env file
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
    
    print("=== Nexar Component Scraper (formerly Octopart) ===\n")
    
    try:
        scraper = NexarScraper()
    except ValueError as e:
        print(f"❌ {e}")
        print("\nTo get Nexar API credentials:")
        print("1. Visit https://portal.nexar.com/sign-up")
        print("2. Sign up for a free account")
        print("3. Create an organization")
        print("4. Use the evaluation app credentials from dashboard")
        print("5. Add to .env file: NEXAR_ACCESS_TOKEN=your_token_here")
        return
    
    print("Fetching medical device components from Nexar...")
    print("This will take several minutes due to rate limiting.\n")
    
    components = scraper.search_medical_device_components()
    scraper.save_to_cache(components)
    
    # Print summary
    print("\n=== Summary ===")
    total = 0
    for category, items in components.items():
        count = len(items)
        total += count
        print(f"{category}: {count} components")
    print(f"\nTotal: {total} components fetched")
    print("\nNext step: Run 'python scripts/ingest_components.py' to add to RAG database")


if __name__ == "__main__":
    main()
