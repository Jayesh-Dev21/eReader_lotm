import json
import sqlite3
from typing import List, Dict
from pathlib import Path


class OutputFormatter:
    """Format and export scraped data to various formats"""
    
    @staticmethod
    def export_json(chapters: List[Dict], output_path: str, book_info: Dict = None):
        """Export to JSON format"""
        data = {
            'book_info': book_info or {},
            'chapters': chapters
        }
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Exported {len(chapters)} chapters to JSON: {output_path}")
    
    @staticmethod
    def export_sqlite(chapters: List[Dict], output_path: str, book_id: str):
        """Export to SQLite (Room-compatible schema)"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(output_path)
        cursor = conn.cursor()
        
        # Create table (Room-compatible schema)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                order_index INTEGER NOT NULL,
                bookTitle TEXT DEFAULT 'Unknown'
            )
        ''')
        
        # Clear existing data for this book
        cursor.execute('DELETE FROM chapters WHERE book_id = ?', (book_id,))
        
        # Insert chapters
        for idx, chapter in enumerate(chapters):
            cursor.execute('''
                INSERT INTO chapters (book_id, title, content, order_index, bookTitle)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                book_id,
                chapter.get('title', 'Untitled'),
                chapter.get('content', ''),
                chapter.get('order_index', idx),
                chapter.get('book_title', 'Unknown')
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Exported {len(chapters)} chapters to SQLite: {output_path}")
    
    @staticmethod
    def export_txt(chapters: List[Dict], output_path: str, book_info: Dict = None):
        """Export to plain text format"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if book_info:
                f.write(f"Book: {book_info.get('title', 'Unknown')}\n")
                f.write(f"ID: {book_info.get('book_id', 'Unknown')}\n")
                f.write("=" * 80 + "\n\n")
            
            for chapter in chapters:
                f.write(f"Chapter {chapter.get('order_index', 0) + 1}\n")
                f.write(f"{chapter.get('title', 'Untitled')}\n")
                f.write("-" * 80 + "\n\n")
                f.write(chapter.get('content', '') + "\n\n")
                f.write("=" * 80 + "\n\n")
        
        print(f"✓ Exported {len(chapters)} chapters to TXT: {output_path}")
    
    @staticmethod
    def export_all(chapters: List[Dict], base_name: str, book_id: str, book_info: Dict = None):
        """Export to all formats"""
        base_path = Path(base_name)
        
        OutputFormatter.export_json(
            chapters,
            str(base_path.with_suffix('.json')),
            book_info
        )
        
        OutputFormatter.export_sqlite(
            chapters,
            str(base_path.with_suffix('.db')),
            book_id
        )
        
        OutputFormatter.export_txt(
            chapters,
            str(base_path.with_suffix('.txt')),
            book_info
        )
