#!/usr/bin/env python3
"""
Test script to verify chapter content extraction
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils.cloudflare_bypass import CloudflareBypass
from utils.parser import RanobesParser
import yaml

def test_chapter_scrape(chapter_url: str):
    """Test scraping a single chapter to verify content extraction"""
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    site_config = config.get('ranobes.top', {})
    
    # Initialize
    cf = CloudflareBypass(site_config)
    parser = RanobesParser(site_config)
    
    print(f"Fetching: {chapter_url}")
    html = cf.get(chapter_url, force_selenium=True)
    
    if not html:
        print("❌ Failed to fetch HTML")
        return
    
    print(f"✅ Got HTML: {len(html)} characters")
    
    # Save raw HTML for debugging
    debug_file = Path('output/debug_chapter.html')
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"🔍 Raw HTML saved to: {debug_file}")
    
    # Parse chapter
    chapter_data = parser.parse_chapter_content(html)
    
    print(f"\n📖 Title: {chapter_data['title']}")
    print(f"📝 Content length: {len(chapter_data['content'])} characters")
    print(f"📝 Content length (words): {len(chapter_data['content'].split())} words")
    print(f"\n--- First 500 characters ---")
    print(chapter_data['content'][:500])
    print(f"\n--- Last 500 characters ---")
    print(chapter_data['content'][-500:])
    
    # Save to file for inspection
    output_file = Path('output/test_chapter.txt')
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Title: {chapter_data['title']}\n")
        f.write(f"Length: {len(chapter_data['content'])} characters\n")
        f.write(f"{'='*80}\n\n")
        f.write(chapter_data['content'])
    
    print(f"\n✅ Full content saved to: {output_file}")

if __name__ == '__main__':
    # Test with first chapter
    test_url = "https://ranobes.top/chapters/133485-glava-1.html"
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    
    test_chapter_scrape(test_url)
