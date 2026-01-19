package com.reader.lotm.data.repository

import com.reader.lotm.data.local.ChapterDao
import com.reader.lotm.data.local.ChapterEntity
import com.reader.lotm.data.scraper.NovelScraper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext

class BookRepository(
    private val chapterDao: ChapterDao,
    private val scraper: NovelScraper
) {
    
    fun getAllChapters(): Flow<List<ChapterEntity>> {
        return chapterDao.getAllChapters()
    }
    
    fun getChapterById(chapterId: Int): Flow<ChapterEntity?> {
        return chapterDao.getChapterByIdFlow(chapterId)
    }
    
    suspend fun getChapterByIdSync(chapterId: Int): ChapterEntity? {
        return chapterDao.getChapterById(chapterId)
    }
    
    fun getChapterCount(): Flow<Int> {
        return chapterDao.getChapterCountFlow()
    }
    
    suspend fun getChapterCountSync(): Int {
        return chapterDao.getChapterCount()
    }
    
    suspend fun getNextChapterId(currentChapterId: Int): Int? {
        return chapterDao.getNextChapterId(currentChapterId)
    }
    
    suspend fun getPreviousChapterId(currentChapterId: Int): Int? {
        return chapterDao.getPreviousChapterId(currentChapterId)
    }
    
    suspend fun scrapeAndPopulateBook(url: String): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val result = scraper.scrapeNovel(url)
            
            result.fold(
                onSuccess = { scraped ->
                    val entities = scraper.convertToEntities(scraped)
                    chapterDao.deleteAllChapters()
                    chapterDao.insertChapters(entities)
                    Result.success(Unit)
                },
                onFailure = { error ->
                    Result.failure(error)
                }
            )
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun insertChapters(chapters: List<ChapterEntity>) {
        chapterDao.insertChapters(chapters)
    }
    
    suspend fun deleteAllChapters() {
        chapterDao.deleteAllChapters()
    }
}
