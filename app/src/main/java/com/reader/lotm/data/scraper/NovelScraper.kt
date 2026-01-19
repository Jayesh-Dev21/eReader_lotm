package com.reader.lotm.data.scraper

import com.reader.lotm.data.local.ChapterEntity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.jsoup.Jsoup
import org.jsoup.nodes.Document
import org.jsoup.nodes.Element

class NovelScraper {
    
    data class ScrapedChapter(
        val title: String,
        val content: String,
        val orderIndex: Int
    )
    
    data class ScrapedNovel(
        val title: String,
        val chapters: List<ScrapedChapter>
    )
    
    suspend fun scrapeNovel(url: String): Result<ScrapedNovel> = withContext(Dispatchers.IO) {
        try {
            val document: Document = Jsoup.connect(url)
                .userAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                .timeout(30000)
                .get()
            
            val bookTitle = extractBookTitle(document)
            val chapterLinks = extractChapterLinks(document)
            
            val chapters = chapterLinks.mapIndexed { index, link ->
                scrapeChapter(link, index)
            }
            
            Result.success(ScrapedNovel(bookTitle, chapters))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    private fun extractBookTitle(document: Document): String {
        return document.select("h1.title, .book-title, h1").firstOrNull()?.text()
            ?: "Lord of the Mysteries"
    }
    
    private fun extractChapterLinks(document: Document): List<String> {
        val chapterElements = document.select("a.chapter-link, .chapter-list a, ul.chapters a")
        
        return chapterElements.mapNotNull { element ->
            element.attr("abs:href").takeIf { it.isNotBlank() }
        }.distinct()
    }
    
    private suspend fun scrapeChapter(url: String, orderIndex: Int): ScrapedChapter = withContext(Dispatchers.IO) {
        try {
            val document: Document = Jsoup.connect(url)
                .userAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                .timeout(30000)
                .get()
            
            val title = extractChapterTitle(document, orderIndex)
            val content = extractChapterContent(document)
            
            ScrapedChapter(title, content, orderIndex)
        } catch (e: Exception) {
            ScrapedChapter(
                title = "Chapter ${orderIndex + 1}",
                content = "Failed to load chapter content: ${e.message}",
                orderIndex = orderIndex
            )
        }
    }
    
    private fun extractChapterTitle(document: Document, orderIndex: Int): String {
        val titleElement = document.select("h1, .chapter-title, h2.title").firstOrNull()
        return titleElement?.text() ?: "Chapter ${orderIndex + 1}"
    }
    
    private fun extractChapterContent(document: Document): String {
        val contentElement = document.select(".chapter-content, #chapter-content, .text, article").firstOrNull()
        
        if (contentElement != null) {
            val paragraphs = contentElement.select("p")
            return if (paragraphs.isNotEmpty()) {
                paragraphs.joinToString("\n\n") { it.text() }
            } else {
                contentElement.text()
            }
        }
        
        return "Content not found"
    }
    
    fun convertToEntities(scraped: ScrapedNovel): List<ChapterEntity> {
        return scraped.chapters.map { chapter ->
            ChapterEntity(
                title = chapter.title,
                content = chapter.content,
                orderIndex = chapter.orderIndex,
                bookId = "133485",  // Book ID for Lord of the Mysteries
                url = null
            )
        }
    }
}
