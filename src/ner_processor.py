#!/usr/bin/env python3
"""
NER Processor 
Spacy based
"""

import json
import os
import spacy
from typing import List, Dict, Set
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
from bs4 import BeautifulSoup
import re


class NERProcessor:
    def __init__(self):
        self.data_dir = "data"
        self.articles_file = os.path.join(self.data_dir, "articles.json")
        self.entities_file = os.path.join(self.data_dir, "entities.json")
        
        # Load spacy french model
        print("Load spacy french model...")
        try:
            self.nlp = spacy.load("fr_core_news_lg")
        except OSError:
            print("[error]: could not find fr_core_news_lg.")
            os.system("python -m spacy download fr_core_news_lg")
            self.nlp = spacy.load("fr_core_news_lg")
        
        # Geocoding
        self.geolocator = Nominatim(user_agent="locust_tracker_madagascar")
        
        # Alternartive names for Madagascar most populated region and cities
        self.madagascar_locations = {
            "antananarivo", "tananarive", "toamasina", "tamatave",
            "antsirabe", "mahajanga", "majunga", "toliara", "tuléar",
            "antsiranana", "diego-suarez", "fianarantsoa", "tolagnaro",
            "fort-dauphin", "morondava", "nosy be", "hell-ville",
            "ambositra", "manakara", "sambava", "antalaha", "maroantsetra"
        }
    
    def load_articles(self) -> List[Dict]:
        """Load all articles through JSON file"""
        if not os.path.exists(self.articles_file):
            print(f"[error]: File {self.articles_file} not found")
            return []
        
        with open(self.articles_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def clean_html(self, text: str) -> str:
        """Clean HTML"""
        if not text:
            return ""
        
        # Remove HTML tags
        soup = BeautifulSoup(text, 'html.parser')
        
        # Extract text inside tags
        clean_text = soup.get_text(separator=' ')
        
        # replace HTML encodage
        clean_text = clean_text.replace('&nbsp;', ' ')
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&quot;', '"')
        clean_text = clean_text.replace('&#39;', "'")
        
        # clean up multiplie spaces
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # Delete space at the begin and at the end
        clean_text = clean_text.strip()
        
        return clean_text
    
    def extract_locations(self, text: str) -> Set[str]:
        """SpaCy NER extraction"""
        clean_text = self.clean_html(text)
        
        # if text empty after clean up
        if not clean_text or len(clean_text) < 3:
            return set()
        
        doc = self.nlp(clean_text)
        
        locations = set()
        
        # Extract LOC (location) and GPE (geo-political entity)
        for ent in doc.ents:
            if ent.label_ in ["LOC", "GPE"]:
                location = ent.text.strip()
                # Filter out small entities
                if len(location) > 2:
                    locations.add(location)
        
        return locations
    
    def geocode_location(self, location: str, retry_count: int = 3) -> Dict:
        # Add "Madagascar" into the request
        query = f"{location}, Madagascar"
        
        for attempt in range(retry_count):
            try:
                time.sleep(1)  # Nominatim API limitation
                
                result = self.geolocator.geocode(query, timeout=10)
                
                if result:
                    return {
                        "name": location,
                        "full_name": result.address,
                        "latitude": result.latitude,
                        "longitude": result.longitude,
                        "query": query
                    }
                else:
                    # Try query withou mentioning Madagascar
                    if attempt == 0:
                        result = self.geolocator.geocode(location, timeout=10)
                        if result:
                            return {
                                "name": location,
                                "full_name": result.address,
                                "latitude": result.latitude,
                                "longitude": result.longitude,
                                "query": location
                            }
                
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                print(f"[error]: geocoding (attempt {attempt + 1}/{retry_count}): {e}")
                time.sleep(2)
        
        return None
    
    def process_articles(self) -> List[Dict]:
        """Process all articles and extract locations"""
        articles = self.load_articles()
        
        if not articles:
            print("[error]: none articles found")
            return []
        
        print(f"Processing {len(articles)} articles...")
        
        processed_data = []
        all_locations = {}  # Cache 
        
        for idx, article in enumerate(articles, 1):
            print(f"\n[{idx}/{len(articles)}] {article['title'][:50]}...")
            
            # Extract location from titles and summary
            combined_text = f"{article['title']} {article['summary']}"
            locations = self.extract_locations(combined_text)
            
            print(f"   location found: {', '.join(locations) if locations else 'none'}")
            
            article_locations = []
            
            # Geocode each location
            for location in locations:
                if location in all_locations:
                    # Use cache
                    article_locations.append(all_locations[location])
                else:
                    # geocode
                    geo_data = self.geocode_location(location)
                    if geo_data:
                        all_locations[location] = geo_data
                        article_locations.append(geo_data)
                        print(f"   ✅ {location} → {geo_data['latitude']:.4f}, {geo_data['longitude']:.4f}")
                    else:
                        print(f"   ❌ {location} → geocodage failed")
            
            # Append articles processed
            processed_data.append({
                "article": article,
                "locations": article_locations,
                "location_count": len(article_locations)
            })
        
        return processed_data
    
    def save_entities(self, processed_data: List[Dict]):
        """Save entities found"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        with open(self.entities_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n Entities saved: {self.entities_file}")
    
    def run(self):
        """RUN NER"""
        print("=" * 60)
        print("🧠 NER PROCESSOR - LOCATION EXTRACTION")
        print("=" * 60)
        
        processed_data = self.process_articles()
        
        if processed_data:
            self.save_entities(processed_data)
            
            # Statistiques
            total_locations = sum(item['location_count'] for item in processed_data)
            articles_with_locations = sum(1 for item in processed_data if item['location_count'] > 0)
            
            print("\n" + "=" * 60)
            print("  NER done!")
            print(f"   - Articles processed: {len(processed_data)}")
            print(f"   - Articles with localisation: {articles_with_locations}")
            print(f"   - Total locations geocoded: {total_locations}")
            print("=" * 60)
        else:
            print("[warning]: Nothing to save...")


if __name__ == "__main__":
    processor = NERProcessor()
    processor.run()