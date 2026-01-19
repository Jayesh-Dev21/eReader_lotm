import re
from bs4 import BeautifulSoup


class ContentCleaner:
    """Clean and normalize chapter content"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common ad phrases (Russian site specific)
        ad_patterns = [
            r'Реклама:.*?(?=\n|$)',
            r'Объявление:.*?(?=\n|$)',
            r'https?://[^\s]+',  # Remove URLs
        ]
        
        for pattern in ad_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Normalize line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    @staticmethod
    def clean_html(html: str, remove_selectors: list = None) -> str:
        """Remove unwanted HTML elements"""
        if not html:
            return ""
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Default elements to remove
        default_remove = [
            'script', 'style', 'iframe', 'ins',
            '.ads', '.advertisement', '.adsbygoogle'
        ]
        
        if remove_selectors:
            default_remove.extend(remove_selectors)
        
        for selector in default_remove:
            for element in soup.select(selector):
                element.decompose()
        
        return str(soup)
    
    @staticmethod
    def normalize_title(title: str) -> str:
        """Normalize chapter title"""
        if not title:
            return "Untitled"
        
        # Remove excessive whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Remove common prefixes if needed
        # title = re.sub(r'^(Chapter|Глава)\s*\d+\s*[:\-–—]?\s*', '', title, flags=re.IGNORECASE)
        
        return title
    
    @staticmethod
    def extract_chapter_number(title: str) -> int:
        """Try to extract chapter number from title"""
        # Pattern: Chapter 123, Глава 123, etc.
        patterns = [
            r'Chapter\s*(\d+)',
            r'Глава\s*(\d+)',
            r'Ch\.?\s*(\d+)',
            r'#(\d+)',
            r'^(\d+)\.',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 0
