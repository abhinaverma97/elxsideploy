"""
KiCad Footprint Library Parser
Downloads and parses KiCad footprint libraries for PCB component data
"""
import os
import re
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import zipfile
import io

class KiCadFootprintParser:
    """Parser for KiCad footprint libraries"""
    
    def __init__(self):
        self.cache_dir = Path(__file__).parent.parent.parent / "documents" / "kicad_footprints"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # KiCad official library repositories
        self.library_repos = [
            "https://gitlab.com/kicad/libraries/kicad-footprints/-/archive/master/kicad-footprints-master.zip"
        ]
    
    def download_kicad_library(self) -> Optional[Path]:
        """
        Download KiCad footprint library
        
        Returns:
            Path to extracted library directory
        """
        print("Downloading KiCad footprint library...")
        print("Note: This is ~100MB, may take a few minutes")
        
        library_dir = self.cache_dir / "kicad-footprints-master"
        
        # Skip if already downloaded
        if library_dir.exists():
            print(f"✓ Library already exists at {library_dir}")
            return library_dir
        
        try:
            response = requests.get(self.library_repos[0], stream=True, timeout=300)
            response.raise_for_status()
            
            # Extract zip in memory
            print("Extracting library...")
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                zf.extractall(self.cache_dir)
            
            print(f"✓ Library downloaded to {library_dir}")
            return library_dir
            
        except Exception as e:
            print(f"❌ Error downloading library: {e}")
            return None
    
    def parse_footprint_file(self, file_path: Path) -> Optional[Dict]:
        """
        Parse a .kicad_mod footprint file
        
        Returns:
            Dictionary with footprint metadata
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            footprint = {
                "name": file_path.stem,
                "library": file_path.parent.name,
                "file_path": str(file_path),
                "parsed_at": datetime.utcnow().isoformat()
            }
            
            # Extract description
            desc_match = re.search(r'\(descr\s+"([^"]+)"\)', content)
            if desc_match:
                footprint["description"] = desc_match.group(1)
            
            # Extract tags
            tags_match = re.search(r'\(tags\s+"([^"]+)"\)', content)
            if tags_match:
                footprint["tags"] = tags_match.group(1).split()
            
            # Extract attributes
            attr_match = re.search(r'\(attr\s+([^\)]+)\)', content)
            if attr_match:
                footprint["attributes"] = attr_match.group(1).split()
            
            # Count pads (gives idea of package type)
            pad_matches = re.findall(r'\(pad\s+"([^"]+)"', content)
            footprint["pad_count"] = len(pad_matches)
            footprint["pad_numbers"] = list(set(pad_matches))
            
            # Extract pad types
            pad_types = re.findall(r'\(pad\s+"[^"]+"\s+(\w+)', content)
            footprint["pad_types"] = list(set(pad_types))
            
            # Try to determine package type from library and description
            library_lower = footprint["library"].lower()
            desc_lower = footprint.get("description", "").lower()
            
            if any(x in library_lower for x in ["qfp", "qfn", "bga", "lga"]):
                footprint["package_family"] = "IC"
            elif any(x in library_lower for x in ["resistor", "capacitor", "inductor"]):
                footprint["package_family"] = "Passive"
            elif any(x in library_lower for x in ["connector", "header", "socket"]):
                footprint["package_family"] = "Connector"
            elif any(x in library_lower for x in ["led", "diode"]):
                footprint["package_family"] = "Discrete"
            else:
                footprint["package_family"] = "Other"
            
            return footprint
            
        except Exception as e:
            print(f"  Error parsing {file_path.name}: {e}")
            return None
    
    def parse_library(self, library_dir: Path, categories: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """
        Parse footprint library
        
        Args:
            library_dir: Path to library directory
            categories: List of library categories to parse (None = all)
            
        Returns:
            Dictionary mapping category to list of footprints
        """
        if categories is None:
            # Focus on medical device relevant categories
            categories = [
                "Package_SO",      # Small Outline (ICs)
                "Package_QFP",     # Quad Flat Pack (MCUs)
                "Package_DFN_QFN", # Dual/Quad Flat No-lead
                "Package_BGA",     # Ball Grid Array
                "Resistor_SMD",    # Surface mount resistors
                "Capacitor_SMD",   # Surface mount capacitors
                "Connector_*",     # All connectors
                "LED_SMD",         # LEDs
                "Sensor_*",        # Sensors
                "Button_Switch_*", # Switches
                "Display_*"        # Displays
            ]
        
        footprints_by_category = {}
        
        for category_pattern in categories:
            # Find matching directories
            if "*" in category_pattern:
                pattern = category_pattern.replace("*", "")
                matching_dirs = [d for d in library_dir.iterdir() 
                               if d.is_dir() and pattern in d.name]
            else:
                matching_dirs = [library_dir / category_pattern] if (library_dir / category_pattern).exists() else []
            
            for lib_dir in matching_dirs:
                if not lib_dir.exists():
                    continue
                
                category_name = lib_dir.name
                print(f"\nParsing library: {category_name}")
                
                footprints = []
                footprint_files = list(lib_dir.glob("*.kicad_mod"))
                
                print(f"  Found {len(footprint_files)} footprints")
                
                for i, fp_file in enumerate(footprint_files):
                    if i % 100 == 0 and i > 0:
                        print(f"  Processed {i}/{len(footprint_files)}")
                    
                    footprint = self.parse_footprint_file(fp_file)
                    if footprint:
                        footprints.append(footprint)
                
                footprints_by_category[category_name] = footprints
                print(f"  ✓ Parsed {len(footprints)} footprints")
        
        return footprints_by_category
    
    def parse_all_footprints(self, max_files: int = 100) -> List[Dict]:
        """Parse footprints from library (simplified for setup script)"""
        library_dir = self.cache_dir / "kicad-footprints-master"
        
        if not library_dir.exists():
            return []
        
        # Focus on most relevant categories for medical devices
        # KiCad uses .pretty extension for footprint libraries
        categories = [
            "Package_QFP.pretty",     # MCUs
            "Package_DFN_QFN.pretty", # Sensors
            "Resistor_SMD.pretty",    # Passives
            "Capacitor_SMD.pretty",   # Passives
            "Connector_PinHeader_2.54mm.pretty",  # Headers
        ]
        
        all_footprints = []
        
        for category in categories:
            lib_dir = library_dir / category
            if not lib_dir.exists():
                continue
            
            footprint_files = list(lib_dir.glob("*.kicad_mod"))[:max_files // len(categories)]
            
            for fp_file in footprint_files:
                footprint = self.parse_footprint_file(fp_file)
                if footprint:
                    all_footprints.append(footprint)
        
        return all_footprints
    
    def save_to_cache(self, footprints: Dict[str, List[Dict]], filename: str = "kicad_footprints.json"):
        """Save footprint data to cache"""
        cache_file = self.cache_dir / filename
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(footprints, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved {sum(len(v) for v in footprints.values())} footprints to {cache_file}")
    
    def load_from_cache(self, filename: str = "kicad_footprints.json") -> Optional[Dict]:
        """Load footprint data from cache"""
        cache_file = self.cache_dir / filename
        
        if not cache_file.exists():
            return None
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)


def main():
    """Main execution"""
    print("=== KiCad Footprint Library Parser ===\n")
    
    parser = KiCadFootprintParser()
    
    # Download library
    library_dir = parser.download_kicad_library()
    if not library_dir:
        print("❌ Failed to download library")
        return
    
    print("\nParsing footprint libraries...")
    print("This will take a few minutes.\n")
    
    # Parse relevant categories
    footprints = parser.parse_library(library_dir)
    
    if not footprints:
        print("❌ No footprints parsed")
        return
    
    # Save to cache
    parser.save_to_cache(footprints)
    
    # Print summary
    print("\n=== Summary ===")
    total = 0
    for category, items in footprints.items():
        count = len(items)
        total += count
        print(f"{category}: {count} footprints")
    
    print(f"\nTotal: {total} footprints parsed")
    print("\nNext step: Run 'python scripts/ingest_components.py' to add to RAG database")


if __name__ == "__main__":
    main()
