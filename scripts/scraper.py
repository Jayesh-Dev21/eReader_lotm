#!/usr/bin/env python3

import argparse
import sys
import time
import random
import yaml
from pathlib import Path
from tqdm import tqdm

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.cloudflare_bypass import CloudflareBypass
from utils.parser import RanobesParser
from utils.cleaner import ContentCleaner
from utils.formatter import OutputFormatter
from utils.checkpoint import CheckpointManager


class RanobesScraper:
    """Main scraper class for ranobes.top"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.site_config = self.config.get('ranobes.top', {})
        self.parser = RanobesParser(self.site_config)
        self.cleaner = ContentCleaner()
        self.checkpoint = None
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"Warning: Config file not found: {config_path}")
            return {'ranobes.top': {}}
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _rate_limit(self):
        """Apply rate limiting between requests"""
        rate_config = self.site_config.get('rate_limit', {})
        min_delay = rate_config.get('min', 2)
        max_delay = rate_config.get('max', 5)
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def scrape_book(
        self,
        book_id: str = None,
        novel_url: str = None,
        output_format: str = 'json',
        output_path: str = None,
        resume: bool = False,
        checkpoint_file: str = "checkpoint.json"
    ):
        """
        Main scraping method
        
        Args:
            book_id: Book ID to scrape
            novel_url: Alternative: extract book_id from URL
            output_format: json, sqlite, txt, or all
            output_path: Custom output path
            resume: Resume from checkpoint
            checkpoint_file: Path to checkpoint file
        """
        # Initialize checkpoint
        self.checkpoint = CheckpointManager(checkpoint_file)
        
        # Determine book ID
        if novel_url:
            book_id = self.parser.extract_book_id_from_url(novel_url)
            if not book_id:
                print(f"Error: Could not extract book_id from URL: {novel_url}")
                return
        
        if not book_id:
            print("Error: book_id or novel_url is required")
            return
        
        print(f"Starting scrape for book ID: {book_id}")
        print("\n⚠️  NOTE: ranobes.top uses JavaScript to load chapters.")
        print("Selenium is REQUIRED for this scraper to work.")
        print("\nTo install Selenium:")
        print("  pip install selenium undetected-chromedriver")
        print("\nAnd ensure Chrome/Chromium is installed on your system.")
        print("=" * 60)
        
        if resume:
            print(f"Resuming from checkpoint: {checkpoint_file}")
        
        self.checkpoint.set_book_id(book_id)
        
        # Initialize Cloudflare bypass
        with CloudflareBypass(self.site_config) as cf_bypass:
            # Step 1: Get chapter list
            chapters_info = self._scrape_chapter_list(cf_bypass, book_id)
            
            if not chapters_info:
                print("\n❌ Error: No chapters found")
                print("\nPossible reasons:")
                print("  1. Selenium not installed (REQUIRED for this site)")
                print("     Install: pip install selenium undetected-chromedriver")
                print("  2. Chrome/Chromium browser not installed")
                print("  3. Website structure changed")
                print("  4. Invalid book ID")
                print("\nDebug files saved as debug_page_*.html")
                return
            
            print(f"Found {len(chapters_info)} chapters to scrape")
            
            # Step 2: Scrape individual chapters
            chapters_data = self._scrape_chapters(cf_bypass, chapters_info)
            
            # Step 3: Export data
            if not output_path:
                output_path = f"output/book_{book_id}"
            
            book_info = {
                'book_id': book_id,
                'title': self.checkpoint.get_metadata('book_title', f'Book {book_id}'),
                'total_chapters': len(chapters_data)
            }
            
            self._export_data(chapters_data, output_format, output_path, book_id, book_info)
            
            print("\n✓ Scraping complete!")
            print(f"Total chapters scraped: {len(chapters_data)}")
    
    def _scrape_chapter_list(self, cf_bypass: CloudflareBypass, book_id: str) -> list:
        """Scrape all chapter links from paginated list"""
        base_url = self.site_config.get('base_url', 'https://ranobes.top')
        first_page_url = self.site_config.get('chapters_url_first', '').format(book_id=book_id)
        
        print(f"\nFetching chapter list from: {first_page_url}")
        print("Note: This page uses JavaScript (Vue.js), using Selenium...")
        
        # Get first page - FORCE SELENIUM for JavaScript-rendered content
        html = cf_bypass.get(first_page_url, force_selenium=True)
        if not html:
            print("Error: Failed to fetch chapter list")
            return []
        
        total_pages = self.parser.detect_total_pages(html)
        print(f"Detected {total_pages} page(s) of chapters")
        
        all_chapters = []
        
        # Scrape all pages
        for page_num in tqdm(range(1, total_pages + 1), desc="Scanning chapter list"):
            # Check checkpoint
            if self.checkpoint.is_page_complete(page_num):
                # Load chapters from checkpoint
                continue
            
            if page_num == 1:
                page_url = first_page_url
                page_html = html  # Already fetched
            else:
                page_url = self.site_config.get('chapters_url', '').format(
                    book_id=book_id,
                    page=page_num
                )
                self._rate_limit()
                page_html = cf_bypass.get(page_url, force_selenium=True)
            
            if not page_html:
                print(f"Warning: Failed to fetch page {page_num}")
                continue
            
            # Always save first page for debugging
            if page_num == 1:
                print(f"  Debug: About to save page {page_num} HTML ({len(page_html)} bytes)")
                try:
                    with open(f'debug_page_{page_num}.html', 'w', encoding='utf-8') as f:
                        f.write(page_html)
                    print(f"  Debug: Successfully saved page {page_num} HTML")
                except Exception as e:
                    print(f"  Debug: Failed to save HTML: {e}")
            
            chapters, _ = self.parser.parse_chapter_list(page_html, base_url)
            
            if not chapters:
                print(f"Warning: No chapters found on page {page_num}")
                # Save HTML for debugging
                if page_num != 1:  # Already saved above
                    with open(f'debug_page_{page_num}.html', 'w', encoding='utf-8') as f:
                        f.write(page_html)
                print(f"  Saved HTML to debug_page_{page_num}.html for inspection")
            
            # Set order index based on accumulated count
            for chapter in chapters:
                chapter['order_index'] = len(all_chapters)
                all_chapters.append(chapter)
            
            self.checkpoint.mark_page_complete(page_num)
        
        # Merge with checkpointed chapters
        checkpointed = self.checkpoint.get_chapters()
        if checkpointed:
            print(f"Resuming with {len(checkpointed)} chapters from checkpoint")
            # Merge and deduplicate
            all_urls = {ch['url'] for ch in all_chapters}
            for ch in checkpointed:
                if ch['url'] not in all_urls:
                    all_chapters.append(ch)
        
        return all_chapters
    
    def _scrape_chapters(self, cf_bypass: CloudflareBypass, chapters_info: list) -> list:
        """Scrape content from individual chapters"""
        chapters_data = []
        
        print(f"\nScraping chapter content...")
        
        for chapter_info in tqdm(chapters_info, desc="Chapters"):
            url = chapter_info['url']
            
            # Check if already in checkpoint
            existing_chapters = self.checkpoint.get_chapters()
            existing = next((ch for ch in existing_chapters if ch.get('url') == url), None)
            
            if existing and existing.get('content'):
                chapters_data.append(existing)
                continue
            
            # Scrape chapter
            self._rate_limit()
            html = cf_bypass.get(url)
            
            if not html:
                print(f"\nWarning: Failed to scrape chapter: {chapter_info.get('title', url)}")
                continue
            
            parsed = self.parser.parse_chapter_content(html)
            
            chapter_data = {
                'url': url,
                'title': self.cleaner.normalize_title(parsed['title']),
                'content': self.cleaner.clean_text(parsed['content']),
                'order_index': chapter_info['order_index']
            }
            
            chapters_data.append(chapter_data)
            self.checkpoint.add_chapter(chapter_data)
        
        return chapters_data
    
    def _export_data(
        self,
        chapters: list,
        output_format: str,
        output_path: str,
        book_id: str,
        book_info: dict
    ):
        """Export scraped data in specified format(s)"""
        print(f"\nExporting to {output_format} format...")
        
        if output_format == 'all':
            OutputFormatter.export_all(chapters, output_path, book_id, book_info)
        elif output_format == 'json':
            OutputFormatter.export_json(chapters, output_path + '.json', book_info)
        elif output_format == 'sqlite':
            OutputFormatter.export_sqlite(chapters, output_path + '.db', book_id)
        elif output_format == 'txt':
            OutputFormatter.export_txt(chapters, output_path + '.txt', book_info)
        else:
            print(f"Unknown format: {output_format}")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape novels from ranobes.top with Cloudflare bypass",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape by book ID
  python scraper.py --book-id 133485 --format sqlite --output lotm.db

  # Scrape from URL
  python scraper.py --url "https://ranobes.top/novels/133485-lord-of-the-mysteries.html"

  # Resume from checkpoint
  python scraper.py --resume checkpoint.json

  # Export to all formats
  python scraper.py --book-id 133485 --format all --output output/lotm
        """
    )
    
    parser.add_argument(
        '--book-id',
        type=str,
        help='Book ID to scrape (e.g., 133485)'
    )
    
    parser.add_argument(
        '--url',
        type=str,
        help='Novel URL (book ID will be extracted)'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['json', 'sqlite', 'txt', 'all'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (without extension for all format)'
    )
    
    parser.add_argument(
        '--resume',
        type=str,
        metavar='CHECKPOINT_FILE',
        help='Resume from checkpoint file'
    )
    
    parser.add_argument(
        '--checkpoint',
        type=str,
        default='checkpoint.json',
        help='Checkpoint file path (default: checkpoint.json)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Config file path (default: config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.resume and not args.book_id and not args.url:
        parser.error("Either --book-id, --url, or --resume is required")
    
    # Initialize scraper
    scraper = RanobesScraper(config_path=args.config)
    
    # Resume mode
    if args.resume:
        checkpoint = CheckpointManager(args.resume)
        book_id = checkpoint.data.get('book_id')
        if not book_id:
            print(f"Error: No book_id found in checkpoint: {args.resume}")
            sys.exit(1)
        
        scraper.scrape_book(
            book_id=book_id,
            output_format=args.format,
            output_path=args.output,
            resume=True,
            checkpoint_file=args.resume
        )
    else:
        scraper.scrape_book(
            book_id=args.book_id,
            novel_url=args.url,
            output_format=args.format,
            output_path=args.output,
            resume=False,
            checkpoint_file=args.checkpoint
        )


if __name__ == '__main__':
    main()
