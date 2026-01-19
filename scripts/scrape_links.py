#!/usr/bin/env python3
"""
Scrape only chapter links for a given book on ranobes.top and save to JSON.

This script reuses the project's existing parser and CloudflareBypass utilities.
It writes progress to a checkpoint file so you can resume collecting links later.

Usage:
  python scrape_links.py --book-id 133485
  python scrape_links.py --url "https://ranobes.top/novels/133485-lord-of-the-mysteries.html"

"""

import argparse
import json
import time
import random
from pathlib import Path
from typing import List, Dict
import sys
import yaml

# Make utils importable
sys.path.insert(0, str(Path(__file__).parent))

from utils.cloudflare_bypass import CloudflareBypass
from utils.parser import RanobesParser
from utils.checkpoint import CheckpointManager


def load_config(config_path: str = 'config.yaml') -> dict:
    cfg = Path(config_path)
    if not cfg.exists():
        return {'ranobes.top': {}}
    with open(cfg, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def rate_sleep(site_config: dict, multiplier: float = 1.0):
    """Sleep with rate limiting. Use multiplier for longer waits between pages."""
    rl = site_config.get('rate_limit', {})
    mn = rl.get('min', 2) * multiplier
    mx = rl.get('max', 5) * multiplier
    delay = random.uniform(mn, mx)
    print(f"   Waiting {delay:.1f}s before next request...")
    time.sleep(delay)


def collect_links(book_id: str, novel_url: str = None, config_path: str = 'config.yaml',
                  output_path: str = None, checkpoint_file: str = 'scripts/checkpoint_links.json',
                  max_pages: int = None) -> List[Dict]:
    cfg = load_config(config_path)
    site_cfg = cfg.get('ranobes.top', {})
    parser = RanobesParser(site_cfg)

    if novel_url and not book_id:
        book_id = parser.extract_book_id_from_url(novel_url)
        if not book_id:
            raise SystemExit(f"Could not extract book_id from URL: {novel_url}")

    if not book_id:
        raise SystemExit("book_id or novel_url is required")

    base_url = site_cfg.get('base_url', 'https://ranobes.top')
    first_page_tpl = site_cfg.get('chapters_url_first', 'https://ranobes.top/chapters/{book_id}/')
    page_tpl = site_cfg.get('chapters_url', 'https://ranobes.top/chapters/{book_id}/page/{page}/')

    first_page_url = first_page_tpl.format(book_id=book_id)

    checkpoint = CheckpointManager(checkpoint_file)
    checkpoint.set_book_id(book_id)

    # Output path
    if not output_path:
        output_path = Path('output') / f'chapter_links_{book_id}.json'
    else:
        output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use CloudflareBypass helper
    with CloudflareBypass(site_cfg) as cf:
        # Fetch first page - FORCE SELENIUM because chapter list uses Vue.js
        print(f"Fetching first page: {first_page_url}")
        print("Note: This page uses JavaScript (Vue.js), forcing Selenium...")
        html = cf.get(first_page_url, force_selenium=True)
        if not html:
            raise SystemExit("Failed to fetch first chapter list page with Selenium")

        total_pages = parser.detect_total_pages(html)
        print(f"Detected total pages: {total_pages}")

        if max_pages and max_pages < total_pages:
            total_pages = max_pages

        collected: List[Dict] = []
        seen = set()

        # If resuming, load already checkpointed chapters
        existing = checkpoint.get_chapters()
        if existing:
            for ch in existing:
                url = ch.get('url')
                if url:
                    seen.add(url)
                    collected.append(ch)

        for page_num in range(1, total_pages + 1):
            if checkpoint.is_page_complete(page_num):
                print(f"Skipping already completed page {page_num}")
                continue

            if page_num == 1:
                page_html = html
                page_url = first_page_url
            else:
                page_url = page_tpl.format(book_id=book_id, page=page_num)
                # Use longer delays between pages (2-3x normal) to avoid rate limiting
                rate_sleep(site_cfg, multiplier=2.5)
                # Force Selenium for all chapter list pages (Vue.js rendering required)
                print(f"Fetching page {page_num} with Selenium...")
                page_html = cf.get(page_url, force_selenium=True)

            if not page_html:
                print(f"Failed to fetch page {page_num}, saving debug HTML and continuing")
                try:
                    with open(f'scripts/debug_page_links_{page_num}.html', 'w', encoding='utf-8') as f:
                        f.write('')
                except Exception:
                    pass
                # Don't give up - continue to next page
                continue

            # Parse chapter links from page
            chapters, _ = parser.parse_chapter_list(page_html, base_url)
            if not chapters:
                print(f"No chapters found on page {page_num}, retrying once...")
                # Save debug HTML
                try:
                    with open(f'scripts/debug_page_links_{page_num}.html', 'w', encoding='utf-8') as f:
                        f.write(page_html)
                    print(f"   Saved debug HTML to scripts/debug_page_links_{page_num}.html")
                except Exception:
                    pass
                
                # Retry once with extra delay
                print(f"   Retrying page {page_num} after longer wait...")
                time.sleep(random.uniform(15, 25))
                retry_html = cf.get(page_url if page_num > 1 else first_page_url, force_selenium=True)
                if retry_html:
                    chapters, _ = parser.parse_chapter_list(retry_html, base_url)
                    if not chapters:
                        print(f"   Still no chapters on page {page_num} after retry, skipping")
                else:
                    print(f"   Retry failed for page {page_num}")
            
            if chapters:
                new_count = 0
                for idx, ch in enumerate(chapters):
                    url = ch.get('url')
                    title = ch.get('title')
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    item = {'url': url, 'title': title, 'order_index': len(collected)}
                    collected.append(item)
                    checkpoint.add_chapter(item)
                    new_count += 1

                print(f"Page {page_num}: found {len(chapters)} links, new {new_count}")

            checkpoint.mark_page_complete(page_num)

            # Periodically flush to disk
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump({'book_id': book_id, 'links': collected}, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Warning: could not write output file: {e}")

        # Final write
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({'book_id': book_id, 'links': collected}, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(collected)} links to {output_path}")
    return collected


def main():
    ap = argparse.ArgumentParser(description='Collect chapter links only (save to JSON)')
    ap.add_argument('--book-id', type=str, help='Book ID (e.g., 133485)')
    ap.add_argument('--url', type=str, help='Novel URL to extract book ID')
    ap.add_argument('--config', type=str, default='config.yaml', help='Config YAML path')
    ap.add_argument('--output', type=str, help='Output JSON path')
    ap.add_argument('--checkpoint', type=str, default='scripts/checkpoint_links.json', help='Checkpoint file')
    ap.add_argument('--max-pages', type=int, help='Limit number of pages to scan (for testing)')

    args = ap.parse_args()

    collect_links(book_id=args.book_id, novel_url=args.url, config_path=args.config,
                  output_path=args.output, checkpoint_file=args.checkpoint, max_pages=args.max_pages)


if __name__ == '__main__':
    main()
