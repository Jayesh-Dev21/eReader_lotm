import json
from typing import Dict, List, Optional
from pathlib import Path


class CheckpointManager:
    """Manage scraping progress checkpoints"""
    
    def __init__(self, checkpoint_file: str = "checkpoint.json"):
        self.checkpoint_file = Path(checkpoint_file)
        self.data = self._load()
    
    def _load(self) -> Dict:
        """Load checkpoint from file"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load checkpoint: {e}")
        
        return {
            'book_id': None,
            'completed_pages': [],
            'completed_chapters': [],
            'chapters': [],
            'metadata': {}
        }
    
    def save(self):
        """Save checkpoint to file"""
        try:
            self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save checkpoint: {e}")
    
    def set_book_id(self, book_id: str):
        """Set current book ID"""
        if self.data['book_id'] != book_id:
            # New book, reset progress
            self.data = {
                'book_id': book_id,
                'completed_pages': [],
                'completed_chapters': [],
                'chapters': [],
                'metadata': {}
            }
        self.save()
    
    def mark_page_complete(self, page_number: int):
        """Mark a page as completed"""
        if page_number not in self.data['completed_pages']:
            self.data['completed_pages'].append(page_number)
        self.save()
    
    def is_page_complete(self, page_number: int) -> bool:
        """Check if page was already scraped"""
        return page_number in self.data['completed_pages']
    
    def add_chapter(self, chapter: Dict):
        """Add scraped chapter to checkpoint"""
        chapter_url = chapter.get('url')
        if chapter_url not in self.data['completed_chapters']:
            self.data['chapters'].append(chapter)
            self.data['completed_chapters'].append(chapter_url)
        self.save()
    
    def get_chapters(self) -> List[Dict]:
        """Get all scraped chapters"""
        return self.data['chapters']
    
    def set_metadata(self, key: str, value):
        """Store metadata"""
        self.data['metadata'][key] = value
        self.save()
    
    def get_metadata(self, key: str, default=None):
        """Retrieve metadata"""
        return self.data['metadata'].get(key, default)
    
    def clear(self):
        """Clear checkpoint"""
        self.data = {
            'book_id': None,
            'completed_pages': [],
            'completed_chapters': [],
            'chapters': [],
            'metadata': {}
        }
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
