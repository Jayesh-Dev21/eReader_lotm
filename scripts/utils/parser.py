from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
import re


class RanobesParser:
    """Parser for ranobes.top website"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.selectors = config.get('selectors', {})
    
    def extract_book_id_from_url(self, url: str) -> Optional[str]:
        """Extract book ID from novel URL"""
        # Pattern: /novels/{book_id}-{slug}.html or /chapters/{book_id}/
        patterns = [
            r'/novels/(\d+)-',
            r'/chapters/(\d+)',
            r'/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def parse_chapter_list(self, html: str, base_url: str) -> Tuple[List[Dict], Optional[str]]:
        """
        Parse chapter list page
        Returns: (list of chapter dicts, next_page_url)
        """
        soup = BeautifulSoup(html, 'lxml')
        chapters = []
        
        # Extract book_id from base_url
        book_id = self.extract_book_id_from_url(base_url)
        
        # Try multiple selectors (site uses Vue.js, so try both rendered and SSR)
        selectors_to_try = [
            self.selectors.get('chapter_links', 'article.poster a.poster-title'),
            'div.cat_block.cat_line a',  # Vue.js rendered
            '.cat_line a',
            'a[href*="/chapters/"]',
            'div[class*="chapter"] a',
        ]
        
        chapter_elements = []
        for selector in selectors_to_try:
            chapter_elements = soup.select(selector)
            if chapter_elements:
                print(f"Using selector: {selector} (found {len(chapter_elements)} links)")
                break
        
        if not chapter_elements:
            # Try finding all links with chapter-like patterns
            all_links = soup.find_all('a', href=True)
            
            # Look for links with book_id and chapter numbers
            if book_id:
                chapter_elements = [
                    link for link in all_links 
                    if book_id in link.get('href', '') and 
                       re.search(r'/\d+\.html', link.get('href', '')) and
                       'page=' not in link.get('href', '') and
                       '#comment' not in link.get('href', '')
                ]
            
            if not chapter_elements:
                # Broader fallback
                chapter_elements = [
                    link for link in all_links 
                    if '/chapters/' in link.get('href', '') and 
                       'page' not in link.get('href', '')
                ]
            
            if chapter_elements:
                print(f"Using fallback pattern matching (found {len(chapter_elements)} links)")
        
        for idx, element in enumerate(chapter_elements):
            url = element.get('href', '')
            title = element.get_text(strip=True)
            
            if not url or not title:
                continue
            
            # Skip pagination links and comments
            if 'page=' in url.lower() or '#comment' in url or not title:
                continue
            
            # Make absolute URL
            if not url.startswith('http'):
                url = base_url.rstrip('/') + '/' + url.lstrip('/')
            
            chapters.append({
                'url': url,
                'title': title,
                'order_index': idx
            })
        
        # Find next page
        next_page_url = self._find_next_page(soup, base_url)
        
        return chapters, next_page_url
    
    def _find_next_page(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Find next pagination page URL"""
        pagination_selector = self.selectors.get('pagination_next', 'div.pagination a:last-child')
        pagination_elements = soup.select(pagination_selector)
        
        if not pagination_elements:
            return None
        
        last_link = pagination_elements[-1]
        next_url = last_link.get('href', '')
        
        # Check if it's not the current page
        if 'disabled' in last_link.get('class', []) or not next_url:
            return None
        
        # Make absolute URL
        if not next_url.startswith('http'):
            next_url = base_url.rstrip('/') + '/' + next_url.lstrip('/')
        
        return next_url
    
    def parse_chapter_content(self, html: str) -> Dict[str, str]:
        """
        Parse individual chapter page with multiple fallback strategies
        Returns: dict with 'title' and 'content'
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract title - try multiple selectors
        title = self._extract_title(soup)
        
        # Extract content - try multiple strategies
        content = self._extract_content(soup, html)
        
        return {
            'title': title,
            'content': content
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract chapter title with fallback strategies"""
        title_selectors = [
            'h1.chapter-title',
            'h1.entry-title', 
            '.chapter-title',
            'h1',
            '.title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title:
                    return title
        
        return "Untitled"
    
    def _extract_content(self, soup: BeautifulSoup, html: str) -> str:
        """Extract chapter content with multiple fallback strategies"""
        
        # Strategy 1: Try configured selectors
        content_selectors = [
            'div.text-content',
            'div.entry-content',
            'article.text',
            'div.chapter-content',
            'div.content',
            '.text-content',
            '.entry-content'
        ]
        
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                content = self._clean_and_extract(content_element)
                if len(content) > 100:  # Ensure substantial content
                    return content
        
        # Strategy 2: Look for main content area
        main_selectors = ['main', 'article', '#content', '.main-content']
        for selector in main_selectors:
            main_element = soup.select_one(selector)
            if main_element:
                content = self._clean_and_extract(main_element)
                if len(content) > 100:
                    return content
        
        # Strategy 3: Find largest text block
        all_divs = soup.find_all(['div', 'article', 'section'])
        max_content = ""
        for div in all_divs:
            text = self._clean_and_extract(div)
            if len(text) > len(max_content):
                max_content = text
        
        return max_content if len(max_content) > 100 else ""
    
    def _clean_and_extract(self, element) -> str:
        """Clean element and extract text content"""
        # Make a copy to avoid modifying original
        element_copy = element.__copy__()
        
        # Remove unwanted elements
        remove_selectors = self.selectors.get('remove_elements', [])
        remove_selectors.extend([
            'script', 'style', 'iframe', 'noscript',
            'ins.adsbygoogle', 'div.ads', 'div.advertisement',
            'nav', 'header', 'footer', '.navigation', '.breadcrumbs'
        ])
        
        for selector in remove_selectors:
            for unwanted in element_copy.select(selector):
                unwanted.decompose()
        
        # Extract text from paragraphs first
        paragraphs = element_copy.find_all('p')
        if paragraphs:
            content_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 10:  # Filter out very short paragraphs
                    content_parts.append(text)
            
            if content_parts:
                return '\n\n'.join(content_parts)
        
        # Fallback: get all text
        text = element_copy.get_text(separator='\n', strip=True)
        
        # Clean up multiple newlines
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def detect_total_pages(self, html: str) -> int:
        """Detect total number of pages from pagination"""
        soup = BeautifulSoup(html, 'lxml')
        
        # First, try to extract from the JSON data in the page
        # Look for: window.__DATA__ = {"pages_count":58,...}
        json_match = re.search(r'window\.__DATA__\s*=\s*({.+?})\s*</script>', html, re.DOTALL)
        if json_match:
            try:
                import json
                data = json.loads(json_match.group(1))
                pages_count = data.get('pages_count', 1)
                if pages_count > 0:
                    return pages_count
            except:
                pass
        
        # Fallback 1: Look for pagination in div.pages (Vue.js rendered)
        pages_div = soup.select_one('div.pages')
        if pages_div:
            page_links = pages_div.find_all('a', href=True)
            max_page = 1
            for link in page_links:
                href = link.get('href', '')
                match = re.search(r'/page/(\d+)', href)
                if match:
                    page_num = int(match.group(1))
                    max_page = max(max_page, page_num)
            if max_page > 1:
                return max_page
        
        # Fallback 2: Look for standard pagination links
        pagination = soup.select('div.pagination a, div.navigation a')
        if pagination:
            max_page = 1
            for link in pagination:
                text = link.get_text(strip=True)
                match = re.search(r'\d+', text)
                if match:
                    page_num = int(match.group())
                    max_page = max(max_page, page_num)
            if max_page > 1:
                return max_page
        
        return 1
