#!/usr/bin/env python3
"""
Download individual chapter content from saved chapter links JSON.

This script reads the output from scrape_links.py and downloads each chapter's
content one by one, with checkpointing so you can resume at any time.

Usage:
  python fetch_chapters.py --links output/chapter_links_133485.json
  python fetch_chapters.py --links output/chapter_links_133485.json --batch-size 50
  python fetch_chapters.py --links output/chapter_links_133485.json --delay-min 5 --delay-max 10
"""

import argparse
import json
import time
import random
import sys
from pathlib import Path
from typing import List, Dict
import yaml

sys.path.insert(0, str(Path(__file__).parent))

from utils.cloudflare_bypass import CloudflareBypass
from utils.parser import RanobesParser
from utils.cleaner import ContentCleaner
from utils.formatter import OutputFormatter


class ChapterFetcher:
    def __init__(self, config_path: str = 'config.yaml'):
        self.config = self._load_config(config_path)
        self.site_config = self.config.get('ranobes.top', {})
        self.parser = RanobesParser(self.site_config)
        self.cleaner = ContentCleaner()
        self.checkpoint_data = {}
        
    def _load_config(self, path: str) -> dict:
        cfg = Path(path)
        if not cfg.exists():
            return {'ranobes.top': {}}
        with open(cfg, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_checkpoint(self, checkpoint_file: Path) -> dict:
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load checkpoint: {e}")
        return {'completed_urls': [], 'chapters': []}
    
    def _save_checkpoint(self, checkpoint_file: Path):
        try:
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(self.checkpoint_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save checkpoint: {e}")
    
    def _save_output(self, output_file: Path, book_id: str):
        """Save collected chapters to multiple formats"""
        chapters = self.checkpoint_data.get('chapters', [])
        
        # JSON
        json_file = output_file.with_suffix('.json')
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'book_id': book_id,
                    'chapters': chapters
                }, f, ensure_ascii=False, indent=2)
            print(f"   Saved to {json_file}")
        except Exception as e:
            print(f"   Warning: Could not save JSON: {e}")
        
        # SQLite database for Android app
        db_file = output_file.with_suffix('.db')
        try:
            OutputFormatter.export_sqlite(chapters, str(db_file), book_id)
            print(f"   Saved to {db_file}")
        except Exception as e:
            print(f"   Warning: Could not save SQLite: {e}")
    
    def fetch_chapters(
        self,
        links_file: Path,
        output_file: Path = None,
        checkpoint_file: Path = None,
        batch_size: int = None,
        delay_min: float = None,
        delay_max: float = None,
        start_index: int = 0,
        end_index: int = None
    ):
        # Load links
        with open(links_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        book_id = data.get('book_id', 'unknown')
        links = data.get('links', [])
        
        if not links:
            raise SystemExit("No links found in input file")
        
        print(f"Loaded {len(links)} chapter links for book {book_id}")
        
        # Setup paths
        if not output_file:
            output_file = Path('output') / f'chapters_{book_id}'
        else:
            output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not checkpoint_file:
            checkpoint_file = Path('scripts') / f'checkpoint_chapters_{book_id}.json'
        else:
            checkpoint_file = Path(checkpoint_file)
        
        # Load checkpoint
        self.checkpoint_data = self._load_checkpoint(checkpoint_file)
        completed_urls = set(self.checkpoint_data.get('completed_urls', []))
        
        # Determine delays
        if delay_min is None:
            delay_min = self.site_config.get('rate_limit', {}).get('min', 3)
        if delay_max is None:
            delay_max = self.site_config.get('rate_limit', {}).get('max', 8)
        
        print(f"Using delays: {delay_min}-{delay_max}s between chapters")
        
        # Filter links
        if end_index:
            links = links[start_index:end_index]
        else:
            links = links[start_index:]
        
        if batch_size:
            links = links[:batch_size]
            print(f"Batch mode: processing {len(links)} chapters")
        
        # Download chapters
        with CloudflareBypass(self.site_config) as cf:
            for idx, link_info in enumerate(links, start=start_index):
                url = link_info.get('url')
                title = link_info.get('title', 'Unknown')
                order_idx = link_info.get('order_index', idx)
                
                if not url:
                    print(f"Skipping item {idx}: no URL")
                    continue
                
                if url in completed_urls:
                    print(f"[{idx+1}/{len(links)}] Skipping (already completed): {title}")
                    continue
                
                print(f"\n[{idx+1}/{len(links)}] Fetching: {title}")
                print(f"   URL: {url}")
                
                # Rate limiting
                if idx > start_index:
                    delay = random.uniform(delay_min, delay_max)
                    print(f"   Waiting {delay:.1f}s...")
                    time.sleep(delay)
                
                # Fetch chapter
                html = cf.get(url, force_selenium=False)
                if not html:
                    print(f"   Failed to fetch, trying Selenium...")
                    html = cf.get(url, force_selenium=True)
                
                if not html:
                    print(f"   ❌ Failed to fetch chapter")
                    # Save debug
                    try:
                        with open(f'scripts/debug_chapter_{idx}.html', 'w', encoding='utf-8') as f:
                            f.write('')
                    except:
                        pass
                    continue
                
                # Parse content
                try:
                    parsed = self.parser.parse_chapter_content(html)
                    chapter_data = {
                        'url': url,
                        'title': self.cleaner.normalize_title(parsed['title']) if parsed['title'] else title,
                        'content': self.cleaner.clean_text(parsed['content']),
                        'order_index': order_idx
                    }
                    
                    # Add to checkpoint
                    self.checkpoint_data['chapters'].append(chapter_data)
                    self.checkpoint_data['completed_urls'].append(url)
                    completed_urls.add(url)
                    
                    print(f"   ✓ Downloaded ({len(chapter_data['content'])} chars)")
                    
                    # Save checkpoint every chapter
                    self._save_checkpoint(checkpoint_file)
                    
                    # Save output every 10 chapters
                    if len(self.checkpoint_data['chapters']) % 10 == 0:
                        self._save_output(output_file, book_id)
                        
                except Exception as e:
                    print(f"   ❌ Parse error: {e}")
                    continue
        
        # Final save
        print(f"\n{'='*60}")
        print(f"Download complete!")
        print(f"Total chapters downloaded: {len(self.checkpoint_data['chapters'])}")
        self._save_output(output_file, book_id)
        print(f"{'='*60}")


def main():
    ap = argparse.ArgumentParser(
        description='Download chapter content from saved links JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all chapters from links file
  python fetch_chapters.py --links output/chapter_links_133485.json

  # Download in batches of 50 chapters at a time
  python fetch_chapters.py --links output/chapter_links_133485.json --batch-size 50

  # Use custom delays (10-20 seconds between chapters)
  python fetch_chapters.py --links output/chapter_links_133485.json --delay-min 10 --delay-max 20

  # Resume from checkpoint (automatic)
  python fetch_chapters.py --links output/chapter_links_133485.json

  # Download specific range
  python fetch_chapters.py --links output/chapter_links_133485.json --start 0 --end 100
        """
    )
    
    ap.add_argument('--links', required=True, help='Path to chapter links JSON file')
    ap.add_argument('--output', help='Output path (without extension)')
    ap.add_argument('--checkpoint', help='Checkpoint file path')
    ap.add_argument('--config', default='config.yaml', help='Config YAML path')
    ap.add_argument('--batch-size', type=int, help='Number of chapters to download in this run')
    ap.add_argument('--delay-min', type=float, help='Minimum delay between chapters (seconds)')
    ap.add_argument('--delay-max', type=float, help='Maximum delay between chapters (seconds)')
    ap.add_argument('--start', type=int, default=0, help='Start index (0-based)')
    ap.add_argument('--end', type=int, help='End index (exclusive)')
    
    args = ap.parse_args()
    
    fetcher = ChapterFetcher(config_path=args.config)
    fetcher.fetch_chapters(
        links_file=Path(args.links),
        output_file=Path(args.output) if args.output else None,
        checkpoint_file=Path(args.checkpoint) if args.checkpoint else None,
        batch_size=args.batch_size,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        start_index=args.start,
        end_index=args.end
    )


if __name__ == '__main__':
    main()
