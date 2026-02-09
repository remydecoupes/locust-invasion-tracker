#!/usr/bin/env python3
"""
RSS Scraper for Google News
"""

import time
import feedparser
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class GoogleNewsRSScraper:
    def __init__(self):
        self.data_dir = "data"
        self.articles_file = os.path.join(self.data_dir, "articles.json")
        
        self.thematic_keywords = [
            # Français
            "criquet", "criquets", "acridien", "invasion", "essaim",
            # English
            "locust", "locusts", "swarm", "outbreak",
            # Malagasy (approximations courantes)
            "valala", "andiam-balala", "kijeja", "zana-balala",
        ]

        self.geo_keywords = [
            # Country
            "madagascar", "madagaskar", "malagasy", "malgache", "madagasikara",

            # Old province
            "antananarivo", "antsiranana", "mahajanga", "toliara", "tuléar", "fianarantsoa", "toamasina", "tamatave",

            # Faritany 
            "antananarivo", "antsiranana", "fianarantsoa", "mahajanga", "toamasina", "toliary",

            # Region
            "analamanga", "bongolava", "itasy", "vakinakaratra", "diana", "sava", "amoron'i mania", "atsimo atsinanana", 
            "fitovinany", "haute matsiatra", "ihorombe", "vatovavy", "betsiboka", "boeny", "melaky", "sofia", "alaotra mangoro", 
            "analanjirofo", "atsinanana", "androy", "anosy", "atsimo andrefana", "menabe",

            # District
            "ambohidratrimo", "andramasina", "anjozorobe", "ankazobe", "antananarivo atsimonandrano", "antananarivo avaradrano", 
            "antananarivo renivohitra", "manjakandriana", "fenoarivobe", "tsiroanomandidy", "arivonimamo", "miarinariro", "soavinandriana", 
            "ambatolampy", "antanifotsy", "antsirabe i", "antsirabe ii", "betafo", "faratsiho", "mandoto", "ambanja", "ambilobe", 
            "antsiranana i", "antsiranana ii", "nosy-be", "andapa", "antalaha", "sambava", "vohemar", "ambatofinandrahana", "ambositra", 
            "fandriana", "manandriana", "befotaka", "farafangana", "midongy-atsimo", "vangaindrano", "vondrozo", "ikongo", "manakara atsimo", 
            "vohipeno", "ambalavao", "ambohimahasoa", "fianarantsoa i", "ikalamavony", "isandra", "lalangina", "vohibato", "iakora", "ihosy", 
            "ivohibe", "ifanadiana", "mananjary", "nosy-varika", "kandreho", "maevatanana", "tsaratanana", "ambato boeni", "mahajanga i", 
            "mahajanga ii", "marovoay", "mitsinjo", "soalala", "ambatomainty", "antsalova", "besalampy", "maintirano", "morafenobe", "analalava", 
            "antsohihy", "bealanana", "befandriana nord", "mampikony", "mandritsara", "port-berge (boriziny-vaovao)", "ambatondrazaka", 
            "amparafaravola", "andilamena", "anosibe-an'ala", "moramanga", "fenerive est", "mananara-avaratra", "maroantsetra", "sainte marie", 
            "soanierana ivongo", "vavatenina", "antanambao manampontsy", "brickaville", "mahanoro", "marolambo", "toamasina i", "toamasina ii", 
            "vatomandry", "ambovombe-androy", "bekily", "beloha", "tsihombe", "amboasary-atsimo", "betroka", "taolagnaro", "ampanihy ouest", 
            "ankazoabo", "benenitra", "beroroha", "betioky atsimo", "morombe", "sakaraha", "toliary i", "toliary ii", "belo sur tsiribihina", 
            "mahabо", "manja", "miandrivazo", "morondava",
        ]

        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.get("https://news.google.com/rss/articles/CBMikgFBVV95cUxNVTQtYndlMjRSSlBKaEd5MmxaVHlGT1NkV0VFbEFTMFlmTXp2aW1YRWlrYmxJS0pjS1phZTlObm1ER1VtNWxzVnh4M3ZWVVhhWDJLTVJkUHRiOGJtb3NXekNOWEgybTNCOER5NjV4TkNwcUczTlZ0WnhxVHlMcFdLVGhyTTFrM1N3ODRpNF9GQ21EUQ?oc=5")

        # Accept cookies if present (EU popup)
        try:
            agree = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button//*[text()='Accept all']")))
            agree.click()
        except:
            pass
        
        # URL  flux RSS Google News for: Madagascar + criquets
        self.rss_url = "https://news.google.com/rss/search?q=criquet+madagascar&hl=fr&gl=MG&ceid=MG:fr"
        self.rss_url_malagasy = "https://news.google.com/rss/search?q=valala+madagasikara&hl=mg&gl=MG&ceid=MG:mg"
        
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
        combined_text = combined_text.lower()
        
        # Keyword list
        has_locust_keyword = any(kw in combined_text for kw in self.thematic_keywords)
        has_madagascar = any(kw in combined_text for kw in self.geo_keywords)
        #"madagascar" in combined_text or "malgache" in combined_text or "malagasy" in combined_text or "madagasikara" in combined_text
        
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
            "scraped_at": datetime.now().isoformat(),
            "full_content": None,  # Sera rempli par fetch_full_content
            "content_fetched": False
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
        
        
    def fetch_full_content(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """Get content from webpages"""     
        
        for attempt in range(max_retries):
            try:
                print(f"      Get webpage content (Attempt {attempt + 1}/{max_retries})...")
                self.driver.get(url)

                # consent popup handling
                try: # classic
                    agree = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button//*[text()='Accept all']")))
                    agree.click()
                except:
                    try: # with dov dodomi
                        agree = self.wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button")))
                        agree.click()
                    except:
                        print("      [error]: could not accept cookie for this website")

                
                response = self.driver.page_source            

                # Parse  HTML
                soup = BeautifulSoup(response, 'html.parser')
                
                # Remove unnecessary web 
                for element in soup.find_all(['script', 'style', 'nav', 'footer', 'aside', 'header']):
                    element.decompose()
                
                # get main content
                main_content = None
                
                # Priority 1 : tag article
                article = soup.find('article')
                if article:
                    main_content = article
                
                # Priority 2 : div with "content"
                if not main_content:
                    content_classes = ['article-content', 'post-content', 'entry-content', 
                                      'article-body', 'story-body', 'main-content']
                    for class_name in content_classes:
                        content_div = soup.find('div', class_=re.compile(class_name, re.I))
                        if content_div:
                            main_content = content_div
                            break
                
                # Priority 3 : take the whole tag "body"
                if not main_content:
                    main_content = soup.find('body')
                
                if main_content:
                    # Extract texts
                    text = main_content.get_text(separator='\n', strip=True)
                    
                    # Remove duplicated lines
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    clean_text = '\n'.join(lines)
                    
                    
                    # Extract title
                    page_title = soup.find('title')
                    page_title_text = page_title.get_text(strip=True) if page_title else ""
                    
                    return {
                        'text': clean_text,
                        'page_title': page_title_text,
                        'word_count': len(clean_text.split()),
                        'fetched_at': datetime.now().isoformat(),
                    }
                else:
                    print(f"      [error]:  Could not get the main content")
                    return None
                
            except requests.exceptions.Timeout:
                print(f"      [error] Timeout ")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None
                
            except requests.exceptions.RequestException as e:
                print(f"     [error] HTTP: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None
                
            except Exception as e:
                print(f"      [error]: While extracting: {e}")
                return None
        
        return None
    
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
                    print(f" New article: {article_data['title'][:60]}...")

                    # Try to get the full content
                    full_content = self.fetch_full_content(article_data['link'])
                    
                    if full_content:
                        article_data['full_content'] = full_content
                        article_data['content_fetched'] = True
                        print(f"   Get content: {full_content['word_count']} words")
                    else:
                        article_data['content_fetched'] = False
                        print(f"   [error]: Could not extract content from webpages: use RSS metadata instead")
                    
                    new_articles.append(article_data)
                    
                    # Délai entre les requêtes pour être respectueux
                    if full_content:
                        time.sleep(2)
        
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