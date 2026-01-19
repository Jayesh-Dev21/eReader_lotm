#!/usr/bin/env python3
"""
Complete automated scraper for Lord of the Mysteries
Scrapes all chapters with proper delays and checkpointing
"""
import argparse
import sys
import time
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))

from utils.cloudflare_bypass import CloudflareBypass
from utils.parser import RanobesParser
from utils.cleaner import ContentCleaner
from utils.checkpoint import CheckpointManager
import yaml


class CompleteScraper:
    def __init__(self, book_id: str, config_path: str = "config.yaml"):
        self.book_id = book_id
        self.config = self._load_config(config_path)
        self.site_config = self.config.get('ranobes.top', {})
        
        self.cf = CloudflareBypass(self.site_config)
        self.parser = RanobesParser(self.site_config)
        self.cleaner = ContentCleaner()
        
        self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        
        self.checkpoint_file = self.output_dir / f'complete_scrape_{book_id}.json'
        self.db_file = self.output_dir / f'chapters_{book_id}.db'
        self.json_file = self.output_dir / f'chapters_{book_id}_full.json'
        
        self._init_database()
    
    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _init_database(self):
        """Initialize SQLite database with proper schema"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                order_index INTEGER,
                book_id TEXT,
                url TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _save_checkpoint(self, data: dict):
        """Save progress checkpoint"""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_checkpoint(self) -> dict:
        """Load progress checkpoint"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        return {'completed_urls': [], 'failed_urls': [], 'last_index': 0}
    
    def _rate_limit(self, multiplier: float = 1.0):
        """Apply rate limiting between requests"""
        import random
        rate_config = self.site_config.get('rate_limit', {})
        min_delay = rate_config.get('min', 3) * multiplier
        max_delay = rate_config.get('max', 8) * multiplier
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def collect_all_links(self) -> list:
        """Collect all chapter links from all pages"""
        print("📚 Step 1: Collecting all chapter links...")
        
        all_links = []
        page = 1
        max_pages = 100  # Safety limit
        
        while page <= max_pages:
            if page == 1:
                url = self.site_config['chapters_url_first'].format(book_id=self.book_id)
            else:
                url = self.site_config['chapters_url'].format(book_id=self.book_id, page=page)
            
            print(f"  📄 Fetching page {page}... ", end='', flush=True)
            
            html = self.cf.get(url, force_selenium=True)
            if not html:
                print("❌ Failed")
                break
            
            print("✅")
            
            chapters, next_url = self.parser.parse_chapter_list(html, url)
            
            if not chapters:
                print(f"  ⚠️  No chapters found on page {page}")
                break
            
            all_links.extend(chapters)
            print(f"  ➕ Found {len(chapters)} chapters (Total: {len(all_links)})")
            
            # Detect total pages on first page
            if page == 1:
                total_pages = self.parser.detect_total_pages(html)
                print(f"  📊 Detected {total_pages} total pages")
                max_pages = total_pages
            
            if not next_url:
                break
            
            page += 1
            self._rate_limit(multiplier=2.5)  # Longer delays for list pages
        
        print(f"\n✅ Collected {len(all_links)} chapter links from {page} pages\n")
        
        # Save links
        links_file = self.output_dir / f'all_links_{self.book_id}.json'
        with open(links_file, 'w') as f:
            json.dump(all_links, f, indent=2)
        
        return all_links
    
    def scrape_chapters(self, links: list, start_from: int = 0):
        """Scrape all chapters with checkpointing"""
        print(f"📖 Step 2: Scraping {len(links)} chapters...\n")
        
        checkpoint = self._load_checkpoint()
        completed_urls = set(checkpoint['completed_urls'])
        failed_urls = checkpoint.get('failed_urls', [])
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        all_chapters = []
        
        for idx, chapter_info in enumerate(tqdm(links[start_from:], initial=start_from, total=len(links))):
            url = chapter_info['url']
            
            # Skip if already completed
            if url in completed_urls:
                continue
            
            try:
                # Fetch chapter
                html = self.cf.get(url, force_selenium=True)
                if not html:
                    failed_urls.append({'url': url, 'reason': 'Failed to fetch HTML'})
                    continue
                
                # Parse content
                chapter_data = self.parser.parse_chapter_content(html)
                
                # Clean content
                cleaned_content = self.cleaner.clean_text(chapter_data['content'])
                
                # Save to database
                cursor.execute('''
                    INSERT INTO chapters (title, content, order_index, book_id, url)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    chapter_data['title'],
                    cleaned_content,
                    idx,
                    self.book_id,
                    url
                ))
                conn.commit()
                
                # Add to JSON collection
                all_chapters.append({
                    'title': chapter_data['title'],
                    'content': cleaned_content,
                    'order': idx,
                    'url': url
                })
                
                # Update checkpoint
                completed_urls.add(url)
                checkpoint['completed_urls'] = list(completed_urls)
                checkpoint['failed_urls'] = failed_urls
                checkpoint['last_index'] = start_from + idx
                self._save_checkpoint(checkpoint)
                
                # Rate limit
                self._rate_limit(multiplier=1.5)
                
            except Exception as e:
                print(f"\n❌ Error scraping {url}: {e}")
                failed_urls.append({'url': url, 'reason': str(e)})
                checkpoint['failed_urls'] = failed_urls
                self._save_checkpoint(checkpoint)
                continue
        
        conn.close()
        
        # Save complete JSON
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(all_chapters, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Scraping complete!")
        print(f"  📊 Successfully scraped: {len(completed_urls)} chapters")
        print(f"  ❌ Failed: {len(failed_urls)} chapters")
        print(f"  💾 Database: {self.db_file}")
        print(f"  📝 JSON: {self.json_file}")
        
        if failed_urls:
            print(f"\n⚠️  Failed URLs saved in checkpoint. Run again to retry.")
    
    def run(self, links_only: bool = False, resume: bool = False):
        """Run complete scraping process"""
        start_time = datetime.now()
        print(f"🚀 Starting complete scrape at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📚 Book ID: {self.book_id}\n")
        
        # Step 1: Collect links
        links_file = self.output_dir / f'all_links_{self.book_id}.json'
        
        if resume and links_file.exists():
            print("📂 Loading existing links...")
            with open(links_file, 'r') as f:
                links = json.load(f)
            print(f"✅ Loaded {len(links)} links\n")
        else:
            links = self.collect_all_links()
        
        if links_only:
            print("✅ Links collected. Exiting (--links-only mode)")
            return
        
        # Step 2: Scrape chapters
        checkpoint = self._load_checkpoint()
        start_from = checkpoint.get('last_index', 0)
        
        if resume and start_from > 0:
            print(f"📂 Resuming from chapter {start_from + 1}...\n")
        
        self.scrape_chapters(links, start_from=start_from)
        
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\n⏱️  Total time: {duration}")
        print(f"✅ All done!")


def main():
    parser = argparse.ArgumentParser(description='Complete automated scraper')
    parser.add_argument('--book-id', default='133485', help='Book ID to scrape')
    parser.add_argument('--links-only', action='store_true', help='Only collect links, don\'t scrape content')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    
    args = parser.parse_args()
    
    scraper = CompleteScraper(args.book_id, args.config)
    scraper.run(links_only=args.links_only, resume=args.resume)


if __name__ == '__main__':
    main()
