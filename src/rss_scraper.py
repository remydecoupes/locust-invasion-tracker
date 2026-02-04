#!/usr/bin/env python3
"""
RSS Scraper for Google News
"""

import feedparser
import json
import os
import re
from datetime import datetime
from typing import List, Dict
import requests
from bs4 import BeautifulSoup


class GoogleNewsRSScraper:
    def __init__(self):
        self.data_dir = "data"
        self.articles_file = os.path.join(self.data_dir, "articles.json")
        
        self.keywords = [
            "criquet", "criquets", "locust", "locusts",
            "acridien", "invasion", "essaim",
            "madagascar", "malgache"
        ]
        
        # URL  flux RSS Google News for: Madagascar + criquets
        self.rss_url = "https://news.google.com/rss/search?q=criquet+madagascar&hl=fr&gl=MG&ceid=MG:fr"
        
    def fetch_rss_feed(self) -> List[Dict]:
        """Get and parse google news"""
        print(f"Get flux RSS: {self.rss_url}")
        
        try:
            feed = feedparser.parse(self.rss_url)
            
            if feed.bozo:
                print(f"[Warning]: can't parse RSS")
            
            print(f"✅ {len(feed.entries)} entries found")
            return feed.entries
            
        except Exception as e:
            print(f"[error]: {e}")
            return []
    
    def is_relevant(self, entry: Dict) -> bool:
        """Relevant article check"""
        title = entry.get('title', '').lower()
        summary = entry.get('summary', '').lower()
        
        combined_text = f"{title} {summary}"
        
        # Keyword list
        has_locust_keyword = any(kw in combined_text for kw in 
                                 ["criquet", "criquets", "locust", "locusts", "acridien", "essaim"])
        has_madagascar = "madagascar" in combined_text or "malgache" in combined_text
        
        return has_locust_keyword and has_madagascar
    
    def extract_article_data(self, entry: Dict) -> Dict:
        """Metadata extraction"""
        return {
            "id": entry.get('id', ''),
            "title": entry.get('title', ''),
            "link": entry.get('link', ''),
            "published": entry.get('published', ''),
            "summary": entry.get('summary', ''),
            "source": entry.get('source', {}).get('title', 'Google News'),
            "scraped_at": datetime.now().isoformat()
        }
    
    def load_existing_articles(self) -> List[Dict]:
        """Load JSON file with all articles"""
        if not os.path.exists(self.articles_file):
            return []
        
        try:
            with open(self.articles_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[error]: could not load artciles: {e}")
            return []
    
    def save_articles(self, articles: List[Dict]):
        """Save articles into a JSON file"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        with open(self.articles_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        print(f"{len(articles)} articles saved in {self.articles_file}")
    
    def run(self):
        """Run scrapping"""
        print("=" * 60)
        print("🦗 SCRAPER RSS - Locust invasion in MADAGASCAR")
        print("=" * 60)
        
        # Get RSS
        entries = self.fetch_rss_feed()
        
        if not entries:
            print("[error]: can not find any flux RSS")
            return
        
        # Load article
        existing_articles = self.load_existing_articles()
        existing_ids = {article['id'] for article in existing_articles}
        
        # Filtrer releveant articles
        new_articles = []
        for entry in entries:
            if self.is_relevant(entry):
                article_data = self.extract_article_data(entry)
                
                # Add if new articles
                if article_data['id'] not in existing_ids:
                    new_articles.append(article_data)
                    print(f"📰 Nouvel article: {article_data['title'][:60]}...")
        
        # Enlarge list of articles
        all_articles = existing_articles + new_articles
        
        # Save all articles
        self.save_articles(all_articles)
        
        print("\n" + "=" * 60)
        print(f"Scraping done!")
        print(f"   - New relevant articles found: {len([e for e in entries if self.is_relevant(e)])}")
        print(f"   - New articles added: {len(new_articles)}")
        print(f"   - Total articles in database: {len(all_articles)}")
        print("=" * 60)


if __name__ == "__main__":
    scraper = GoogleNewsRSScraper()
    scraper.run()