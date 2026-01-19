package com.reader.lotm.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface ChapterDao {
    @Query("SELECT * FROM chapters ORDER BY COALESCE(order_index, id) ASC")
    fun getAllChapters(): Flow<List<ChapterEntity>>

    @Query("SELECT * FROM chapters WHERE id = :chapterId")
    suspend fun getChapterById(chapterId: Int): ChapterEntity?

    @Query("SELECT * FROM chapters WHERE id = :chapterId")
    fun getChapterByIdFlow(chapterId: Int): Flow<ChapterEntity?>

    @Query("SELECT * FROM chapters WHERE order_index = :orderIndex")
    suspend fun getChapterByOrder(orderIndex: Int): ChapterEntity?

    @Query("SELECT COUNT(*) FROM chapters")
    suspend fun getChapterCount(): Int

    @Query("SELECT COUNT(*) FROM chapters")
    fun getChapterCountFlow(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertChapter(chapter: ChapterEntity): Long

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertChapters(chapters: List<ChapterEntity>)

    @Query("DELETE FROM chapters")
    suspend fun deleteAllChapters()

    @Query("SELECT MIN(id) FROM chapters WHERE COALESCE(order_index, id) > (SELECT COALESCE(order_index, id) FROM chapters WHERE id = :currentChapterId)")
    suspend fun getNextChapterId(currentChapterId: Int): Int?

    @Query("SELECT MAX(id) FROM chapters WHERE COALESCE(order_index, id) < (SELECT COALESCE(order_index, id) FROM chapters WHERE id = :currentChapterId)")
    suspend fun getPreviousChapterId(currentChapterId: Int): Int?
}
